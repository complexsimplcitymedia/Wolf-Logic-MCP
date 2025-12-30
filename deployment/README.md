# Wolf AI Production Deployment - Ionos

Complete deployment automation for Wolf AI production infrastructure on Ionos 64GB bare metal server with Proxmox.

## Architecture

**Ionos Bare Metal: $98/month (64GB RAM, Xeon, 2-year contract)**

```
┌─────────────────────────────────────────────────────────────┐
│                  Ionos Proxmox Host (64GB)                  │
│                                                             │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  │
│  │ VM100         │  │ VM101         │  │ VM102         │  │
│  │ PostgreSQL    │  │ Application   │  │ Dev/Backup    │  │
│  │ 12GB RAM      │  │ 12GB RAM      │  │ 12GB RAM      │  │
│  │ 200GB disk    │  │ 150GB disk    │  │ 150GB disk    │  │
│  ├───────────────┤  ├───────────────┤  ├───────────────┤  │
│  │ PG16 @ 5433   │  │ Gateway 8001  │  │ Dev env       │  │
│  │ wolf_logic    │  │ Gateway 8002  │  │ Testing       │  │
│  │               │  │ Gateway 8003  │  │ CI/CD         │  │
│  │ PG17 @ 3306   │  │               │  │               │  │
│  │ authentik     │  │ Caddy :8000   │  │               │  │
│  │               │  │ Load balancer │  │               │  │
│  │ PG17 @ 5436   │  │               │  │               │  │
│  │ gemini        │  │ Authentik     │  │               │  │
│  │               │  │ OAuth/OIDC    │  │               │  │
│  └───────┬───────┘  │               │  └───────────────┘  │
│          │          │ Redis         │                      │
│          │          └───────────────┘                      │
│          │                                                 │
│          │          ┌───────────────────────────────────┐  │
│          └──────────► VM103 - TrueNAS                   │  │
│            NFS mount│ 28GB RAM, 1.5TB storage            │  │
│                     ├───────────────────────────────────┤  │
│                     │ Docker Apps (GUI management)      │  │
│                     │ - Ollama (qwen3-embedding:4b)     │  │
│                     │ - Portainer                       │  │
│                     │                                   │  │
│                     │ ZFS Storage                       │  │
│                     │ - PostgreSQL backups              │  │
│                     │ - Media/assets                    │  │
│                     │ - Embedding cache                 │  │
│                     └───────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Deployment Scripts

### 1. `deploy-ionos-production.sh` (Master Script)
**Main orchestration script - run this first**

Executes complete deployment:
- Provisions 4 VMs on Proxmox
- Migrates PostgreSQL clusters
- Deploys application stack
- Configures services
- Runs health checks

**Usage:**
```bash
./deploy-ionos-production.sh
```

**Interactive prompts:**
- Proxmox host IP/hostname
- Storage pool name
- Confirmation for each phase

**What it does:**
1. Calls `ionos-proxmox-deploy.sh` on Proxmox host
2. Waits for VMs to boot
3. Retrieves VM IPs
4. Calls `migrate-postgres.sh` to transfer databases
5. Calls `deploy-application-stack.sh` to install services
6. Guides TrueNAS manual installation
7. Starts services and validates health

### 2. `ionos-proxmox-deploy.sh` (VM Provisioning)
**Creates 4 VMs on Proxmox**

- Downloads Debian 13 cloud image
- Downloads TrueNAS SCALE ISO
- Creates VM100-103 with correct specs
- Configures cloud-init for Debian VMs

**Runs on:** Proxmox host (executed by master script)

**Manual execution (if needed):**
```bash
# SSH to Proxmox host
ssh root@proxmox.ionos.local
./ionos-proxmox-deploy.sh
```

### 3. `migrate-postgres.sh` (Database Migration)
**Transfers PostgreSQL clusters from local workstation to Ionos VM100**

**What it migrates:**
- wolf_logic @ 5433 (92k+ memories)
- authentik @ 3306 (user authentication)
- gemini @ 5436 (Gemini integration)

**Process:**
1. Dumps all clusters using `pg_dump -F c`
2. Transfers dumps via SCP
3. Installs PostgreSQL 16/17/18 on VM100
4. Creates clusters with correct ports
5. Restores dumps with `pg_restore`
6. Configures listen_addresses and pg_hba.conf
7. Restarts services

**Environment variables:**
- `IONOS_POSTGRES_HOST`: Target VM100 IP (auto-detected by master script)

**Manual execution:**
```bash
export IONOS_POSTGRES_HOST="ionos-vm100.ts.net"
./migrate-postgres.sh
```

### 4. `deploy-application-stack.sh` (Services Deployment)
**Installs Wolf Memory Gateway stack on VM101**

**Components deployed:**
- Wolf Memory Gateway (3 replicas on 8001, 8002, 8003)
- Caddy (load balancer with least_conn)
- Authentik (Docker)
- Redis

**Process:**
1. Transfers application files to VM101
2. Installs dependencies (Python 3.12, Docker, Caddy, Redis)
3. Creates Python venv and installs FastAPI/uvicorn
4. Generates systemd service files for 3 gateways
5. Configures Caddy with health checks
6. Updates Authentik docker-compose with Ionos PostgreSQL host

**Environment variables:**
- `IONOS_APP_HOST`: Target VM101 IP
- `IONOS_POSTGRES_HOST`: PostgreSQL VM100 IP

**Manual execution:**
```bash
export IONOS_APP_HOST="ionos-vm101.ts.net"
export IONOS_POSTGRES_HOST="ionos-vm100.ts.net"
./deploy-application-stack.sh
```

### 5. `truenas-setup-guide.md` (Manual Configuration)
**Step-by-step guide for TrueNAS VM103**

VM103 requires console access for initial installation (ISO boot).

**Covers:**
- TrueNAS installation from ISO
- Network configuration (static IP + Tailscale)
- ZFS pool creation (wolf-pool)
- NFS exports for PostgreSQL backups
- Docker app installation via TrueCharts
- Ollama deployment (qwen3-embedding:4b)
- Automatic backup configuration
- Embedding API proxy setup

**Follow after master script prompts for TrueNAS installation.**

## Deployment Workflow

### Step-by-Step Execution

**Prerequisites:**
1. Order Ionos 64GB bare metal with Proxmox
2. SSH access to Proxmox host
3. Tailscale account configured
4. DNS records ready (api.complexsimplicityai.com)

**Deployment:**

```bash
cd /mnt/Wolf-code/Wolf-Ai-Enterptises/deployment

# Run master script
./deploy-ionos-production.sh

# Follow interactive prompts:
# 1. Enter Proxmox host IP
# 2. Confirm VM provisioning
# 3. Confirm PostgreSQL migration
# 4. Confirm application deployment
# 5. Install TrueNAS manually when prompted
# 6. Press Enter to continue after TrueNAS boots
```

**Post-Deployment:**

```bash
# Configure Tailscale on all VMs
ssh wolf@ionos-vm100.ts.net
curl -fsSL https://tailscale.com/install.sh | sh
tailscale up

# Repeat for VM101, VM102, VM103

# Update DNS
# Point api.complexsimplicityai.com → VM101 public IP

# Test endpoints
curl http://ionos-vm101.ts.net:8000/health
curl http://ionos-vm101.ts.net:8000/docs
```

## File Structure

```
deployment/
├── README.md                        # This file
├── deploy-ionos-production.sh       # Master orchestration script
├── ionos-proxmox-deploy.sh          # Proxmox VM provisioning
├── migrate-postgres.sh              # PostgreSQL migration
├── deploy-application-stack.sh      # Application stack deployment
└── truenas-setup-guide.md           # TrueNAS manual configuration
```

## Resource Allocation

**Total: 64GB RAM**

| VM | Purpose | RAM | Disk | Key Services |
|----|---------|-----|------|--------------|
| VM100 | PostgreSQL | 12GB | 200GB | wolf_logic, authentik, gemini clusters |
| VM101 | Application | 12GB | 150GB | Wolf gateways (3x), Caddy, Authentik, Redis |
| VM102 | Dev/Backup | 12GB | 150GB | Development, testing, CI/CD |
| VM103 | TrueNAS | 28GB | 1.5TB | Docker apps, Ollama, ZFS storage, backups |

**Why TrueNAS gets 28GB:**
- Heavy Docker workload (Ollama, Portainer, etc.)
- ZFS ARC cache (10GB)
- Embedding model inference (qwen3-embedding:4b)
- Offloads compute from workstation

## Network Configuration

**Internal (Proxmox bridge):**
- VM100: 10.0.0.100 (static)
- VM101: 10.0.0.101 (static)
- VM102: 10.0.0.102 (static)
- VM103: 10.0.0.103 (static)

**Tailscale (mesh VPN):**
- ionos-vm100.ts.net → PostgreSQL
- ionos-vm101.ts.net → Application
- ionos-vm102.ts.net → Dev
- ionos-vm103.ts.net → TrueNAS

**Public DNS:**
- api.complexsimplicityai.com → VM101 (Caddy load balancer)

## Service Endpoints

**Production API (via Caddy load balancer):**
- `http://api.complexsimplicityai.com/docs` - Swagger UI
- `http://api.complexsimplicityai.com/health` - Health check
- `http://api.complexsimplicityai.com/memories/add` - Add memory
- `http://api.complexsimplicityai.com/memories/search` - Search memories

**Direct gateway access (load balancer bypass):**
- `http://ionos-vm101.ts.net:8001/docs` - Gateway 1
- `http://ionos-vm101.ts.net:8002/docs` - Gateway 2
- `http://ionos-vm101.ts.net:8003/docs` - Gateway 3

**Authentication:**
- `http://ionos-vm101.ts.net:9500` - Authentik admin UI

**PostgreSQL (direct connections):**
- `ionos-vm100.ts.net:5433` - wolf_logic
- `ionos-vm100.ts.net:3306` - authentik
- `ionos-vm100.ts.net:5436` - gemini

**TrueNAS:**
- `http://ionos-vm103.ts.net` - TrueNAS web UI
- `http://ionos-vm103.ts.net:11434` - Ollama API (embeddings)

## Troubleshooting

### VMs not getting IPs
```bash
# On Proxmox host
qm guest cmd 100 network-get-interfaces
```

### PostgreSQL migration fails
```bash
# Check PostgreSQL running on VM100
ssh wolf@ionos-vm100.ts.net
sudo systemctl status postgresql@16-wolf_logic
sudo systemctl status postgresql@17-authentik

# Check connectivity
PGPASSWORD=wolflogic2024 psql -h localhost -p 5433 -U wolf -d wolf_logic -c '\l'
```

### Gateways not starting
```bash
# On VM101
ssh wolf@ionos-vm101.ts.net
sudo systemctl status wolf-gateway-8001
sudo journalctl -u wolf-gateway-8001 -f

# Check Python dependencies
source ~/wolf-stack/api/venv/bin/activate
pip list
```

### Caddy load balancer errors
```bash
# Check Caddy logs
ssh wolf@ionos-vm101.ts.net
sudo journalctl -u caddy -f

# Test upstream health
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
```

### TrueNAS NFS mount fails
```bash
# On TrueNAS
showmount -e

# On Debian VMs
sudo mount -t nfs ionos-vm103:/mnt/wolf-pool/backups /mnt/backups
```

## Cost Analysis

**Ionos 64GB Bare Metal:**
- $98/month × 24 months = $2,352 total

**Equivalent cloud (4 VMs @ 12-28GB each):**
- AWS/DigitalOcean estimate: ~$400/month
- 2-year cost: $9,600

**Savings: $7,248 over 2 years**

## Security Considerations

**Port obfuscation:**
- PostgreSQL authentik on port 3306 (MariaDB default) instead of 5432

**Network isolation:**
- Tailscale mesh VPN for all internal communication
- Proxmox bridge for VM-to-VM communication (no external exposure)

**Authentication:**
- Authentik OAuth/OIDC for API access
- FIDO2 hardware key support

**Backups:**
- Automatic PostgreSQL dumps to TrueNAS NFS every night
- 7-day retention

## Performance Expectations

**Gateway throughput:**
- 3 replicas with least_conn balancing
- ~100-300 req/sec per gateway (FastAPI/uvicorn)
- Total capacity: 300-900 req/sec

**Database performance:**
- PostgreSQL on Xeon with NVMe storage
- ~1-2ms query latency for semantic search
- 92k+ memories indexed

**Embedding inference:**
- qwen3-embedding:4b on TrueNAS (Xeon CPU)
- Single embed: ~300-400ms
- Batch 100: ~3-4 embeddings/sec

**Network latency:**
- VM-to-VM (localhost/LAN): <1ms
- Internet → Ionos: ~10-50ms (depending on location)
- Tailscale overhead: ~5-10ms

## Monitoring

**Health checks:**
```bash
# Gateway health
curl http://ionos-vm101.ts.net:8000/health

# PostgreSQL connections
PGPASSWORD=wolflogic2024 psql -h ionos-vm100.ts.net -p 5433 -U wolf -d wolf_logic -c 'SELECT version();'

# Redis
redis-cli -h ionos-vm101.ts.net ping
```

**Logs:**
```bash
# Gateway logs
ssh wolf@ionos-vm101.ts.net
sudo journalctl -u wolf-gateway-8001 -f

# Caddy logs
sudo journalctl -u caddy -f

# PostgreSQL logs
ssh wolf@ionos-vm100.ts.net
sudo tail -f /var/log/postgresql/postgresql-16-wolf_logic.log
```

## Next Steps After Deployment

1. Configure Authentik OAuth applications
2. Create API keys for beta testers
3. Set up monitoring (Grafana + Prometheus)
4. Configure automated backups to external storage
5. Load test with 100 concurrent users
6. Deploy Android app pointing to api.complexsimplicityai.com

**Ready for production beta launch with 100 testers.**
