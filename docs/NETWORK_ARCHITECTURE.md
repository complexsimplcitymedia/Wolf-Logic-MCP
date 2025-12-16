# Network Architecture Blueprint

**Last Updated:** 2025-12-04
**Network Type:** Tailscale Mesh VPN

---

## Critical: USE TAILSCALE TUNNELS, NOT DIRECT SSH

**All inter-device communication goes through Tailscale mesh network.**
Do NOT use local IPs for SSH. Use Tailscale IPs.

---

## Network Topology

```
┌─────────────────────────────────────────────────────────────┐
│                     Tailscale Mesh Network                   │
│                    (100.110.82.0/24)                        │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
   ┌────▼─────┐       ┌────▼─────┐       ┌────▼─────┐
   │ MacBook  │       │  Server  │       │  Debian  │
   │ Wolfbook │       │ csmcloud │       │  Client  │
   └──────────┘       └──────────┘       └──────────┘
```

---

## Device Details

### 1. MacBook (Wolfbook) - Primary Development Machine

**Tailscale (USE THIS):**
- Tailscale IP: `100.110.82.245`
- SSH: `ssh -i ~/.ssh/id_ed25519 complexsimplicity@100.110.82.245`

**Services:**
- Caddy (reverse proxy)
- Caddy Manager
- Portainer: `100.110.82.245:9444`
- Caddy Admin API: `http://100.110.82.245:2019`
- Docker: `/usr/local/bin/docker`

**Domains:**
- `mactainer.complexsimplicityai.com` → `100.110.82.245:9444`
- `caddy-manager.complexsimplicityai.com` → `localhost:8080`

---

### 2. Server (csmcloud-server) - Production Infrastructure

**Tailscale (USE THIS):**
- Hostname: `csmcloud-server`
- Tailscale IP: `100.110.82.181`
- SSH: `ssh user@100.110.82.181`

**Services:**
- Qdrant (vector database)
- Neo4j (graph database)
- OpenMemory MCP
- OpenMemory UI
- Portainer: `100.110.82.181:9443`

**Domains:**
- `portainer.complexsimplicityai.com` → `100.110.82.181:9443`

---

**Services on csmcloud-server (100.110.82.181):**
- PostgreSQL (wolf_logic): `100.110.82.181:5433`
- Ollama (embedding fleet): `localhost:11434`
- Piper TTS: `localhost:5050`
- Memory API: `localhost:5000`
- Neo4j: `localhost:7474` / `localhost:8687`
- Grafana: `localhost:3000`
- Prometheus: `localhost:9090`

**GPU:**
- AMD RX 7900 XT (21.4GB VRAM)
- ROCm enabled

---

## SSH Connection Examples

### ✅ CORRECT - Tailscale Tunnel Only
```bash
# Use Tailscale IP
ssh -i ~/.ssh/id_ed25519 complexsimplicity@100.110.82.245
```

---

## Docker MCP Gateway (MacBook)

The MCP server configuration uses SSH tunnel to MacBook's Docker:

```json
{
  "MCP_DOCKER": {
    "command": "ssh",
    "args": [
      "-i",
      "/home/thewolfwalksalone/.ssh/id_ed25519",
      "complexsimplicity@100.110.82.245",
      "PATH=/usr/local/bin:$PATH",
      "/usr/local/bin/docker",
      "mcp",
      "gateway",
      "run",
      "--stdio"
    ]
  }
}
```

**Key:** SSH to Tailscale IP `100.110.82.245`, execute Docker MCP gateway remotely.

---

## Why Tailscale?

1. **Secure tunnels** - Encrypted mesh network
2. **NAT traversal** - Works across networks/firewalls
3. **Persistent IPs** - `100.110.82.*` IPs don't change
4. **Zero trust** - Each device authenticated
5. **No port forwarding** - Direct peer-to-peer when possible

---

## Service Access Matrix

| Service | Device | Local Access | Tailscale Access | Public Domain |
|---------|--------|-------------|------------------|---------------|
| PostgreSQL (wolf_logic) | Debian | `100.110.82.181:5433` | N/A (local only) | N/A |
| Ollama | Debian | `localhost:11434` | N/A (local only) | N/A |
| Portainer (Mac) | MacBook | `localhost:9444` | `100.110.82.245:9444` | `mactainer.complexsimplicityai.com` |
| Portainer (Server) | Server | `localhost:9443` | `100.110.82.181:9443` | `portainer.complexsimplicityai.com` |
| Caddy Admin API | MacBook | `localhost:2019` | `100.110.82.245:2019` | N/A |
| Docker (Mac) | MacBook | `/usr/local/bin/docker` | SSH tunnel | N/A |

---

## Firewall Rules

**Tailscale handles all firewall/routing automatically.**

No manual iptables or firewall configuration needed for inter-device communication.

---

## Quick Reference

### Connect to MacBook
```bash
ssh -i ~/.ssh/id_ed25519 complexsimplicity@100.110.82.245
```

### Connect to Server
```bash
ssh user@100.110.82.181
```

### Access Mac Portainer
```
http://100.110.82.245:9444
# OR
https://mactainer.complexsimplicityai.com
```

### Access Server Portainer
```
http://100.110.82.181:9443
# OR
https://portainer.complexsimplicityai.com
```

---

## Troubleshooting

### Can't SSH to device
1. Verify Tailscale is running: `tailscale status`
2. Check device is online in Tailscale network
3. Use Tailscale IP, not local IP
4. Verify SSH key path: `~/.ssh/id_ed25519`

### Docker MCP not connecting
1. Verify MacBook Tailscale IP: `100.110.82.245`
2. Test SSH connection manually first
3. Check Docker path on Mac: `/usr/local/bin/docker`
4. Verify MCP gateway is installed on Mac

---

**SECURITY:** Never document or expose local network IPs.
**ALWAYS use Tailscale IPs (`100.110.82.*`) for all inter-device communication.**

