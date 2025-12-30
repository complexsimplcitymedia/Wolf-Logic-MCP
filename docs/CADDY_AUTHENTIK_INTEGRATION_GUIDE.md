# Caddy + Caddy Manager + Authentik OAuth Integration Guide

**Complete Owner's Manual for Wolf Ai Enterprises Infrastructure**

---

## Current State (What's Running)

### ✅ Caddy (Native)
- **Service:** systemd (caddy.service)
- **Config:** `/etc/caddy/Caddyfile`
- **SSL Certs:** `/etc/caddy/certs/` (wildcard for *.complexsimplicityai.com)
- **Admin API:** http://100.110.82.181:2019
- **Status:** Running, listening on port 443

### ✅ Caddy Manager (Docker)
- **Compose File:** `/mnt/Wolf-code/memory_layer/mem0/caddymanager/docker-compose.yml`
- **Frontend:** Port 8008
- **Backend:** Port 3003
- **Status:** Running
- **Access:** http://localhost:8008 (currently NO AUTH)

### ✅ Authentik OAuth Provider (Docker)
- **Compose File:** `/home/thewolfwalksalone/Documents/authentik/docker-compose.yml`
- **Web UI:** Port 9080 (mapped from 9000)
- **HTTPS:** Port 7443 (mapped from 9443)
- **Database:** PostgreSQL (authentik-postgresql-1)
- **Status:** Running, healthy
- **Access:** http://localhost:9080 OR https://auth.complexsimplicityai.com

---

## The Problem You Keep Running Into

**Just connecting Caddy → Caddy Manager doesn't provide:**
1. **Authentication** - anyone can access Caddy Manager
2. **SSO Integration** - no unified login across services
3. **User Management** - can't control who has access
4. **Audit Trail** - no logging of who made changes

**The solution is OAuth/OIDC via Authentik protecting Caddy Manager.**

---

## Integration Architecture

```
User → https://caddy-manager.complexsimplicityai.com
         ↓
      Caddy (wildcard SSL)
         ↓
      Authentik Forward Auth Middleware
         ├─ Not Authenticated? → Redirect to auth.complexsimplicityai.com
         └─ Authenticated? → Pass to Caddy Manager (port 8008)
```

---

## Step-by-Step Integration

### Step 1: Configure Authentik Application

1. **Access Authentik Admin:**
   ```bash
   https://auth.complexsimplicityai.com
   ```

2. **Create OAuth Provider:**
   - Navigate to: Applications → Providers → Create
   - Type: OAuth2/OpenID Provider
   - Name: `Caddy Manager OAuth`
   - Client ID: (generate or set: `caddy-manager-client`)
   - Client Secret: (save this - you need it later)
   - Redirect URIs:
     ```
     https://caddy-manager.complexsimplicityai.com/oauth2/callback
     http://localhost:8008/oauth2/callback
     ```
   - Signing Key: (select default or create one)

3. **Create Application:**
   - Applications → Create
   - Name: `Caddy Manager`
   - Slug: `caddy-manager`
   - Provider: Select "Caddy Manager OAuth" from step 2
   - Launch URL: `https://caddy-manager.complexsimplicityai.com`

4. **Create Outpost (Forward Auth):**
   - Outposts → Create
   - Type: Proxy
   - Name: `Caddy Forward Auth`
   - Configuration:
     - External Host: `https://auth.complexsimplicityai.com/outpost.goauthentik.io`
   - Applications: Select "Caddy Manager"

### Step 2: Install OAuth2 Proxy (Sidecar for Caddy Manager)

This sits between Caddy and Caddy Manager to handle OAuth.

**Create compose file:**
```yaml
# /mnt/Wolf-code/memory_layer/mem0/caddymanager/docker-compose-oauth.yml
version: '3.8'

services:
  oauth2-proxy:
    image: quay.io/oauth2-proxy/oauth2-proxy:latest
    container_name: caddy-manager-oauth
    restart: unless-stopped
    ports:
      - "4180:4180"
    environment:
      - OAUTH2_PROXY_PROVIDER=oidc
      - OAUTH2_PROXY_CLIENT_ID=caddy-manager-client
      - OAUTH2_PROXY_CLIENT_SECRET=<FROM_AUTHENTIK>
      - OAUTH2_PROXY_OIDC_ISSUER_URL=https://auth.complexsimplicityai.com/application/o/caddy-manager/
      - OAUTH2_PROXY_REDIRECT_URL=https://caddy-manager.complexsimplicityai.com/oauth2/callback
      - OAUTH2_PROXY_UPSTREAMS=http://caddymanager-frontend:80
      - OAUTH2_PROXY_HTTP_ADDRESS=0.0.0.0:4180
      - OAUTH2_PROXY_COOKIE_SECRET=<GENERATE_32_BYTE_SECRET>
      - OAUTH2_PROXY_EMAIL_DOMAINS=*
      - OAUTH2_PROXY_PASS_ACCESS_TOKEN=true
      - OAUTH2_PROXY_PASS_USER_HEADERS=true
      - OAUTH2_PROXY_SET_XAUTHREQUEST=true
      - OAUTH2_PROXY_COOKIE_SECURE=true
      - OAUTH2_PROXY_COOKIE_HTTPONLY=true
    networks:
      - caddymanager_caddymanager

networks:
  caddymanager_caddymanager:
    external: true
```

**Generate cookie secret:**
```bash
python -c 'import os,base64; print(base64.urlsafe_b64encode(os.urandom(32)).decode())'
```

**Start OAuth2 Proxy:**
```bash
cd /mnt/Wolf-code/memory_layer/mem0/caddymanager
docker compose -f docker-compose-oauth.yml up -d
```

### Step 3: Update Caddyfile

**Modify `/etc/caddy/Caddyfile`:**

```caddy
https://caddy-manager.complexsimplicityai.com {
	import custom_wildcard_tls
	import security_headers

	# Forward auth to Authentik
	forward_auth localhost:4180 {
		uri /oauth2/auth
		copy_headers X-Auth-Request-User X-Auth-Request-Email
	}

	# Reverse proxy to Caddy Manager via OAuth2 Proxy
	reverse_proxy localhost:4180
}
```

**Reload Caddy:**
```bash
sudo systemctl reload caddy
```

### Step 4: Test the Flow

1. **Access Caddy Manager:**
   ```
   https://caddy-manager.complexsimplicityai.com
   ```

2. **Expected Flow:**
   - Caddy receives request
   - Forward auth checks with OAuth2 Proxy (port 4180)
   - OAuth2 Proxy checks auth status
   - If not authenticated: Redirect to Authentik login
   - User logs in via Authentik
   - Redirect back to Caddy Manager
   - Access granted

3. **Verify:**
   - Should see Authentik login page
   - After login, should land on Caddy Manager UI
   - Headers should include user info from Authentik

---

## Alternative: Native Caddy + Authentik (Without OAuth2 Proxy)

If you want Caddy to handle OAuth directly (no sidecar):

### Install Caddy with Security Plugin

**Build custom Caddy:**
```bash
xcaddy build --with github.com/greenpau/caddy-security
```

**Or use Docker image:**
```bash
docker pull ghcr.io/greenpau/caddy-security:latest
```

### Updated Caddyfile (Native OAuth)

```caddy
{
	order authenticate before respond
	order authorize before authenticate

	security {
		oauth identity provider authentik {
			realm authentik
			driver generic
			client_id caddy-manager-client
			client_secret <FROM_AUTHENTIK>
			scopes openid profile email
			base_auth_url https://auth.complexsimplicityai.com
			metadata_url https://auth.complexsimplicityai.com/application/o/caddy-manager/.well-known/openid-configuration
		}

		authentication portal myportal {
			crypto default token lifetime 3600
			crypto key sign-verify <GENERATE_KEY>
			enable identity provider authentik
			cookie domain complexsimplicityai.com
			ui {
				links {
					"Caddy Manager" https://caddy-manager.complexsimplicityai.com
				}
			}
		}

		authorization policy caddy_manager_policy {
			set auth url https://auth.complexsimplicityai.com/oauth2/start
			allow roles authp/admin authp/user
		}
	}
}

https://caddy-manager.complexsimplicityai.com {
	import custom_wildcard_tls
	import security_headers

	authenticate with myportal
	authorize with caddy_manager_policy

	reverse_proxy localhost:8008
}
```

---

## Troubleshooting

### Caddy Manager Not Loading
```bash
# Check containers
docker ps --filter "name=caddymanager"

# Check logs
docker logs caddymanager-frontend
docker logs caddymanager-backend

# Check if port 8008 is accessible
curl -I http://localhost:8008
```

### OAuth Loop (Keeps Redirecting)
- Verify redirect URIs in Authentik match exactly
- Check cookie domain settings
- Ensure HTTPS is enforced (no mixed http/https)

### Authentik Not Accessible
```bash
# Check Authentik containers
docker ps --filter "name=authentik"

# Check Authentik logs
docker logs authentik-server-1

# Verify port 9080
ss -tlnp | grep 9080
```

### Caddy Not Proxying
```bash
# Check Caddy status
systemctl status caddy

# Validate Caddyfile
caddy validate --config /etc/caddy/Caddyfile

# Check Caddy logs
sudo journalctl -u caddy -n 50
```

---

## Security Checklist

- [ ] Wildcard SSL certificates installed and valid
- [ ] Authentik using strong admin password
- [ ] OAuth client secrets generated (not default)
- [ ] Cookie secrets are random 32-byte values
- [ ] HTTPS enforced (no HTTP fallback)
- [ ] Authentik database backed up
- [ ] Caddy Manager backend restricts API access to authenticated users
- [ ] Audit logging enabled in Authentik
- [ ] Rate limiting configured on auth endpoints

---

## Next Steps After Integration

1. **User Management:**
   - Create user accounts in Authentik
   - Assign roles (admin, editor, viewer)
   - Set up groups for team access

2. **Additional Services:**
   - Add OAuth to other services (Grafana, Portainer, etc.)
   - Use same Authentik instance for SSO

3. **Monitoring:**
   - Set up Authentik event monitoring
   - Track OAuth failures
   - Monitor Caddy access logs

4. **Backup:**
   - Backup Authentik PostgreSQL database
   - Backup `/etc/caddy/` directory
   - Backup OAuth client secrets

---

## Quick Reference Commands

```bash
# Restart Caddy
sudo systemctl restart caddy

# Reload Caddy config (no downtime)
sudo systemctl reload caddy

# Restart Caddy Manager
cd /mnt/Wolf-code/memory_layer/mem0/caddymanager
docker compose restart

# Restart Authentik
cd /home/thewolfwalksalone/Documents/authentik
docker compose restart

# View all logs
docker compose logs -f

# Check Caddy config
caddy validate --config /etc/caddy/Caddyfile

# Test OAuth flow
curl -I https://caddy-manager.complexsimplicityai.com
```

---

## What You Need From The Other Model

Ask whoever is helping with Authentik for:

1. **OAuth Provider Details:**
   - Client ID
   - Client Secret
   - OIDC Discovery URL

2. **Application Configuration:**
   - Confirm redirect URIs are set correctly
   - Verify signing key is configured

3. **Outpost Status:**
   - Is the Forward Auth outpost running?
   - What's the external host URL?

4. **User Setup:**
   - Are there test users created?
   - What roles/groups exist?

Once you have these details, the integration becomes plug-and-play.

---

**This is the complete owner's manual. Follow these steps in order and you'll have:**
- Caddy (reverse proxy with wildcard SSL)
- Caddy Manager (web UI for managing Caddy)
- Authentik OAuth (protecting Caddy Manager with SSO)

All three working together as one unified, authenticated API-serving masterpiece.
