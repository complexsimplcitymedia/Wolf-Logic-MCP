# Native Caddy Setup for Docker Swarm

## Overview
Caddy runs natively on host (not in swarm), managing reverse proxy for swarm services.
- **Host:** 100.110.82.181
- **Admin API:** http://100.110.82.181:2019
- **Authentik integration:** Swarm services communicate with native Caddy API

## Installation

### 1. Install Caddy on Host
```bash
# Debian/Ubuntu
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy
```

### 2. Configure Caddy
```bash
# Copy Caddyfile to /etc/caddy/
sudo cp /mnt/Wolf-code/Wolf-Ai-Enterptises/Wolf-Logic-MCP/server-configuration/Caddyfile /etc/caddy/Caddyfile

# Validate config
sudo caddy validate --config /etc/caddy/Caddyfile

# Restart Caddy
sudo systemctl restart caddy
sudo systemctl enable caddy
```

### 3. Verify Caddy Admin API
```bash
# Should return config JSON
curl http://100.110.82.181:2019/config/ | jq
```

## Caddyfile Configuration

The Caddyfile (`/etc/caddy/Caddyfile`) routes to swarm service names on overlay network:

```caddyfile
{
	admin 100.110.82.181:2019
	auto_https off
}

auth.complexsimplicityai.com {
	reverse_proxy authentik-server:9000
}

grafana.complexsimplicityai.com {
	reverse_proxy grafana:3000
}
```

## Network Bridge for Swarm Services

Caddy on host needs to reach swarm overlay network services.

### Option 1: Join Caddy to Overlay Network (Recommended)
```bash
# Run Caddy in a container but in host network mode
# Then join it to the swarm overlay network
docker network connect wolf_overlay <caddy-container-id>
```

### Option 2: Publish Service Ports
Services already publish ports to host (grafana:3000, authentik:9001, etc.)

Update Caddyfile to use `localhost:PORT`:
```caddyfile
auth.complexsimplicityai.com {
	reverse_proxy localhost:9001
}

grafana.complexsimplicityai.com {
	reverse_proxy localhost:3000
}
```

## Authentik Integration

### Configure Authentik Outpost
1. Access Authentik admin: `http://100.110.82.181:9001`
2. Navigate to **Outposts** → **Integrations**
3. Create new integration:
   - **Type:** Proxy
   - **Name:** Native Caddy
   - **Connection:** HTTP
   - **URL:** `http://100.110.82.181:2019`

### Configure Outpost for Applications
1. Navigate to **Outposts** → **Outposts**
2. Create outpost:
   - **Name:** Caddy Proxy
   - **Type:** Proxy
   - **Integration:** Native Caddy (from above)
   - **Applications:** Select Grafana, Prometheus, etc.

Authentik will now configure Caddy routes via the admin API at 100.110.82.181:2019.

## Firewall Rules

Ensure ports are accessible:
```bash
# Allow Caddy admin API (internal only - restrict to Tailscale)
sudo ufw allow from 100.110.82.0/24 to any port 2019

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Or use Tailscale ACLs instead of UFW
```

## Testing

### 1. Check Caddy Status
```bash
sudo systemctl status caddy
```

### 2. Test Admin API
```bash
curl http://100.110.82.181:2019/config/ | jq
```

### 3. Test Service Access
```bash
# Should return Grafana login page
curl http://localhost:3000

# Through Caddy (if DNS configured)
curl http://grafana.complexsimplicityai.com
```

### 4. Test Authentik Integration
```bash
# Check if Authentik can reach Caddy API
docker exec $(docker ps -q -f name=wolf_authentik-server) curl http://100.110.82.181:2019/config/
```

## Troubleshooting

### Caddy Can't Reach Swarm Services
If using service names (authentik-server, grafana, etc.) instead of localhost:PORT:

1. Run Caddy in Docker container attached to wolf_overlay network
2. Or use published ports (localhost:9001, localhost:3000, etc.)

### Authentik Can't Reach Caddy Admin API
1. Check firewall rules
2. Verify Caddy is listening on 100.110.82.181:2019
3. Check from within swarm network:
   ```bash
   docker run --rm --network wolf_overlay nicolaka/netshoot curl http://100.110.82.181:2019/config/
   ```

### TLS Certificate Issues
Enable auto HTTPS in Caddyfile:
```caddyfile
{
	admin 100.110.82.181:2019
	# Remove: auto_https off
	email admin@complexsimplicityai.com
}
```

## Production Checklist

- [ ] Install Caddy on host
- [ ] Copy Caddyfile to /etc/caddy/
- [ ] Enable and start Caddy service
- [ ] Configure DNS records for all domains
- [ ] Deploy swarm stack
- [ ] Configure Authentik integration
- [ ] Test all service routes
- [ ] Enable TLS (Let's Encrypt)
- [ ] Restrict admin API access (Tailscale/VPN only)
- [ ] Set up monitoring (Prometheus scraping Caddy metrics)
