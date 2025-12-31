# Server Configuration - Node 181 (100.110.82.181)

Production server infrastructure configuration for csmcloud-server.

## Contents

### Docker Compose
- **docker-compose.181.yml** - Full infrastructure stack (23 services)
  - Monitoring: Prometheus, Grafana, Node Exporter, cAdvisor
  - Auth: Authentik (PostgreSQL, Redis, Server, Worker)
  - Databases: Neo4j, MariaDB
  - Wolf APIs: wolf-rest-api, wolf-api, wolf-hunt-api, wolf-hunt-ui, wolf-mcp
  - LLM: Open WebUI, AnythingLLM
  - Management: Portainer

### Systemd Services
- **systemd/server-scripty.service** - Local LLM session transcription (llama3.2:1b)
- **systemd/wolf-mcp.service** - MCP server for PostgreSQL access
- **systemd/wolf-api.service** - Wolf API service
- **systemd/cloud-baremetal-mcp.service** - Cloud baremetal MCP

### Environment Configuration
- **.env** - Primary environment variables
- **.env.cloud-baremetal** - Cloud baremetal specific
- **.env.cloud-baremetal.template** - Template for cloud baremetal
- **.envrc** - direnv configuration

### Monitoring
- **monitoring/** - Prometheus and Grafana configurations

### Scripts
- **scripts/configure_postgres_tailscale.sh** - PostgreSQL Tailscale setup
- **scripts/setup_250_failover.sh** - Failover server setup (250)
- **scripts/setup_local_librarian.py** - Local librarian (pgai) setup
- **scripts/setup_local_postgres.sql** - PostgreSQL initialization
- **scripts/start_wolf_stack.sh** - Start full Wolf stack
- **scripts/sync_from_181.py** - Sync from server 181
- **scripts/sync_ollama_models.sh** - Sync Ollama models

### Other
- **failover-config.md** - Failover configuration documentation
- **mcp_config.json** - MCP server configuration

## Deployment

### Start Full Stack
```bash
cd /mnt/Wolf-code/Wolf-Ai-Enterptises/Wolf-Logic-MCP/server-configuration
docker compose -f docker-compose.181.yml up -d
```

### Enable Server-Scripty
```bash
sudo cp systemd/server-scripty.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable server-scripty.service
sudo systemctl start server-scripty.service
```

### Check Status
```bash
docker compose -f docker-compose.181.yml ps
systemctl status server-scripty
```

## Network
- **Tailscale IP:** 100.110.82.181
- **Services:** PostgreSQL (wolf_logic:5433), Ollama (host)
- **Bridge Network:** wolf_network

## PostgREST API Configuration

PostgREST provides a RESTful API interface to the PostgreSQL database.

### JWT Configuration

| Variable | Value | Notes |
|----------|-------|-------|
| `PGRST_JWT_SECRET` | `ipC5Xi04TlDcuBArsdFfn17bJIOMNEgEnxF6pRtPbG4` | JWT Secret Key |
| `POSTGREST_API_TOKEN` | See below | Valid for 1 year, **expires 2026-12-29** |

**API Token:**
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoid29sZiIsInN1YiI6IndvbGYtYXBpLWNsaWVudCIsImlhdCI6MTc2NzA2NDIxOCwiZXhwIjoxNzk4NjAwMjE4fQ.QbYeODx2MCQf8xQ0AQ_cuQtunsFG0ekS6JoPNjaZX44
```

### Usage Example

```bash
curl -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoid29sZiIsInN1YiI6IndvbGYtYXBpLWNsaWVudCIsImlhdCI6MTc2NzA2NDIxOCwiZXhwIjoxNzk4NjAwMjE4fQ.QbYeODx2MCQf8xQ0AQ_cuQtunsFG0ekS6JoPNjaZX44' \
  https://api.complexsimplicityai.com/memories?limit=1
```

### Token Details
- **Role:** `wolf`
- **Subject:** `wolf-api-client`
- **Issued:** 2025-12-29 (iat: 1767064218)
- **Expires:** 2026-12-29 (exp: 1798600218)

## Notes
- Ollama runs on host (NOT containerized) - required for server-scripty
- All services connect via wolf_network bridge
- Persistent volumes defined for data storage
- Server-scripty writes to staging dir for pgai vectorizer (no direct DB writes)
