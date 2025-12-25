# Authentik + Caddy Integration Setup

## Overview
Authentik SSO integrated with Caddy reverse proxy on Docker Swarm.
- **Caddy Admin API:** http://100.110.82.181:2019
- **Authentik Server:** http://100.110.82.181:9001

## Prerequisites
1. Docker Swarm initialized
2. Node labels configured
3. DNS records pointing to 100.110.82.181

## Deployment Steps

### 1. Deploy Stack
```bash
cd /mnt/Wolf-code/Wolf-Ai-Enterptises/Wolf-Logic-MCP/server-configuration
./deploy-swarm.sh
```

### 2. Configure Authentik

#### Initial Setup
1. Access Authentik: `http://100.110.82.181:9001/if/flow/initial-setup/`
2. Create admin account:
   - Email: admin@complexsimplicityai.com
   - Password: wolflogic2024
3. Complete initial setup wizard

#### Create Application for Grafana
1. Navigate to **Applications** → **Applications**
2. Click **Create**
3. Configure:
   - **Name:** Grafana
   - **Slug:** grafana
   - **Provider:** Create new OAuth2/OIDC Provider
4. Provider settings:
   - **Name:** Grafana OAuth
   - **Authorization flow:** default-provider-authorization-implicit-consent
   - **Client type:** Confidential
   - **Client ID:** grafana
   - **Client Secret:** wolflogic2024 (save this)
   - **Redirect URIs:** `https://grafana.complexsimplicityai.com/login/generic_oauth`
   - **Signing Key:** authentik Self-signed Certificate
5. Save provider and application

#### Create Outpost for Caddy
1. Navigate to **Outposts** → **Outposts**
2. Click **Create**
3. Configure:
   - **Name:** Caddy Proxy
   - **Type:** Proxy
   - **Integration:** Local Docker connection
   - **Applications:** Select all apps you want proxied (Grafana, Prometheus, etc.)
4. Advanced settings:
   - **External host:** http://100.110.82.181:2019

### 3. Configure Caddy for Authentik

Caddy is already configured via Caddyfile. The admin API listens on `100.110.82.181:2019`.

#### Verify Caddy Config
```bash
docker exec $(docker ps -q -f name=wolf_caddy) caddy validate --config /etc/caddy/Caddyfile
```

#### Reload Caddy
```bash
curl -X POST http://100.110.82.181:2019/load \
  -H "Content-Type: application/json" \
  -d @Caddyfile
```

### 4. Test Authentication Flow

#### Access Grafana
1. Navigate to: `https://grafana.complexsimplicityai.com`
2. Should redirect to Authentik login
3. Log in with Authentik credentials
4. Should redirect back to Grafana dashboard

### 5. Configure Additional Applications

For each service you want to protect with Authentik:

1. **Create application in Authentik**
   - Navigate to Applications → Create
   - Choose OAuth2/OIDC provider
   - Configure redirect URIs

2. **Update service environment variables**
   - Add OAuth settings to service in wolf-stack.yml
   - Redeploy: `docker stack deploy -c wolf-stack.yml wolf`

3. **Add Caddy route**
   - Update Caddyfile with new domain
   - Reload Caddy config

## Verification

### Check Services
```bash
docker stack services wolf
```

Expected services running:
- wolf_caddy (1/1)
- wolf_authentik-server (1/1)
- wolf_authentik-worker (1/1)
- wolf_authentik-postgresql (1/1)
- wolf_authentik-redis (1/1)
- wolf_grafana (1/1)
- wolf_prometheus (1/1)

### Check Caddy Admin API
```bash
curl http://100.110.82.181:2019/config/ | jq
```

### Check Authentik Health
```bash
curl http://100.110.82.181:9001/-/health/ready/
```

Should return: `{"status":"ok"}`

## Troubleshooting

### Authentik Not Connecting to Caddy
1. Check Caddy admin API is accessible:
   ```bash
   curl http://100.110.82.181:2019/config/
   ```

2. Check network connectivity:
   ```bash
   docker exec $(docker ps -q -f name=wolf_authentik-server) ping caddy
   ```

3. Check outpost logs:
   ```bash
   docker service logs wolf_authentik-server
   ```

### Grafana OAuth Not Working
1. Verify client secret matches in both Authentik and Grafana
2. Check redirect URI is exactly: `https://grafana.complexsimplicityai.com/login/generic_oauth`
3. Ensure Grafana OAuth environment variables are set correctly

### Service Not Starting
```bash
# Check service logs
docker service logs wolf_<service-name>

# Check service details
docker service ps wolf_<service-name> --no-trunc
```

## Security Notes

1. **Change default passwords** in production
2. **Use proper TLS certificates** (Caddy can auto-provision Let's Encrypt)
3. **Restrict Caddy admin API** to internal network only
4. **Enable Authentik 2FA** for all users
5. **Review Authentik flows** and customize for your security requirements

## References
- Authentik Docs: https://goauthentik.io/docs/
- Caddy Docs: https://caddyserver.com/docs/
- Docker Swarm: https://docs.docker.com/engine/swarm/
