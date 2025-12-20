# TrueNAS SCALE Setup Guide - Ionos VM103

## Overview
TrueNAS SCALE VM (28GB RAM) on Ionos Proxmox for:
- Docker container management via GUI
- Embedding model inference (qwen3-embedding:4b on Xeon)
- ZFS storage pools
- NFS/SMB shares for backup and media

## Installation Steps

### 1. Boot from ISO
```bash
# On Proxmox host
qm start 103
```

Access console via Proxmox web UI and follow TrueNAS installer:
- Select installation disk (scsi0 - 500GB)
- Set root password: `wolflogic2024`
- Reboot after installation

### 2. Initial Configuration

Access TrueNAS web UI: `http://[vm-ip]` (check Proxmox console for DHCP-assigned IP)

Login: `root` / `wolflogic2024`

**Set static IP:**
1. Network → Interfaces → Edit ens18
2. Configure static IP (e.g., 10.0.0.50/24)
3. Set gateway and DNS
4. Test changes, then save

**Install Tailscale:**
```bash
# SSH to TrueNAS as root
curl -fsSL https://tailscale.com/install.sh | sh
tailscale up
```

### 3. Create Storage Pool

**Navigate to Storage → Create Pool:**
- Name: `wolf-pool`
- Layout: Single disk (scsi1 - 1TB)
- Click "Create"

**Create datasets:**
```
wolf-pool/
├── docker-data (for container persistent volumes)
├── backups (PostgreSQL dumps, system backups)
├── media (application media/assets)
└── embeddings (embedding model cache)
```

### 4. Configure NFS Exports

**For PostgreSQL backups:**
1. Sharing → UNIX (NFS) → Add
2. Path: `/mnt/wolf-pool/backups`
3. Authorized networks: `10.0.0.0/24` (Proxmox network)
4. Enable service

**Mount on Debian VMs:**
```bash
# On VM100 (postgres) and VM102 (dev)
sudo apt install nfs-common
sudo mount ionos-vm103:/mnt/wolf-pool/backups /mnt/backups
```

### 5. Install Docker Apps

**Navigate to Apps:**

TrueNAS SCALE uses TrueCharts for Docker management.

**Add TrueCharts catalog:**
1. Apps → Discover Apps → Manage Catalogs
2. Add: `https://github.com/truecharts/catalog`
3. Save

**Install Ollama (for embedding models):**
1. Apps → Discover Apps → Search "ollama"
2. Install TrueCharts Ollama
3. Configuration:
   - Storage: Use `wolf-pool/embeddings` dataset
   - Network: Host network mode
   - GPU: None (CPU inference on Xeon)
4. Deploy

**Pull qwen3-embedding:4b:**
```bash
# SSH to TrueNAS
docker exec -it ollama ollama pull qwen3-embedding:4b
```

**Install Portainer (optional - Docker GUI):**
1. Apps → Discover Apps → Search "portainer"
2. Install
3. Access: `http://ionos-vm103:9000`

### 6. Configure Automatic Backups

**Create backup script on VM100 (postgres):**

```bash
#!/bin/bash
# /home/wolf/backup-postgres.sh

BACKUP_DATE=$(date +%Y%m%d-%H%M%S)
BACKUP_DIR="/mnt/backups/postgres"

mkdir -p "$BACKUP_DIR"

# Backup wolf_logic
PGPASSWORD=wolflogic2024 pg_dump \
    -h localhost -p 5433 -U wolf -d wolf_logic \
    -F c -f "$BACKUP_DIR/wolf_logic-${BACKUP_DATE}.dump"

# Backup authentik
PGPASSWORD=wolflogic2024 pg_dump \
    -h localhost -p 3306 -U authentik -d authentik \
    -F c -f "$BACKUP_DIR/authentik-${BACKUP_DATE}.dump"

# Cleanup old backups (keep 7 days)
find "$BACKUP_DIR" -name "*.dump" -mtime +7 -delete
```

**Add to crontab:**
```bash
crontab -e
# Add:
0 2 * * * /home/wolf/backup-postgres.sh
```

### 7. Embedding API Endpoint

**Create systemd service for Ollama API proxy:**

```bash
# On VM101 (application)
cat > /etc/systemd/system/embedding-proxy.service << 'EOF'
[Unit]
Description=Embedding API Proxy to TrueNAS Ollama
After=network.target

[Service]
Type=simple
User=wolf
ExecStart=/usr/bin/socat TCP-LISTEN:11434,fork,reuseaddr TCP:ionos-vm103:11434
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable embedding-proxy
sudo systemctl start embedding-proxy
```

Now Wolf gateways can call `http://localhost:11434` which proxies to TrueNAS Ollama.

## Resource Allocation

**28GB RAM breakdown:**
- TrueNAS OS: ~2GB
- ZFS ARC cache: ~10GB
- Ollama qwen3-embedding:4b: ~2.5GB (model loaded)
- Docker containers: ~5GB
- Available: ~8.5GB headroom

**Xeon Performance:**
- qwen3-embedding:4b on Xeon (single): ~300-400ms per embed (estimated)
- Batch 100: ~3-4 embeddings/sec (similar to 14700K)
- Workstation offload successful

## Maintenance

**Check pool health:**
```bash
zpool status wolf-pool
```

**Monitor Docker containers:**
```bash
docker ps
docker stats
```

**Update TrueNAS:**
System Settings → Update → Check for updates

## Network Diagram

```
┌─────────────────────────────────────────────┐
│ Ionos Proxmox (64GB Bare Metal)            │
│                                             │
│  ┌──────────────┐  ┌──────────────┐       │
│  │ VM100        │  │ VM101        │       │
│  │ PostgreSQL   │◄─┤ Application  │       │
│  │ 12GB         │  │ 12GB         │       │
│  │              │  │              │       │
│  │ wolf_logic   │  │ Gateways x3  │       │
│  │ authentik    │  │ Caddy        │       │
│  │ gemini       │  │ Authentik    │       │
│  └──────┬───────┘  └──────┬───────┘       │
│         │                 │                │
│         │    NFS mount    │                │
│         │    ┌────────────┘                │
│         │    │                             │
│  ┌──────▼────▼─────────────────────┐      │
│  │ VM103 - TrueNAS (28GB)          │      │
│  │                                  │      │
│  │  ┌──────────┐  ┌──────────────┐ │     │
│  │  │ Ollama   │  │ ZFS Storage  │ │     │
│  │  │ qwen3    │  │ wolf-pool    │ │     │
│  │  │ embed    │  │              │ │     │
│  │  │ :11434   │  │ 1TB          │ │     │
│  │  └──────────┘  └──────────────┘ │     │
│  │                                  │      │
│  │  Docker containers, backups      │      │
│  └──────────────────────────────────┘      │
│                                             │
│  ┌──────────────┐                          │
│  │ VM102        │                          │
│  │ Dev/Backup   │                          │
│  │ 12GB         │                          │
│  └──────────────┘                          │
└─────────────────────────────────────────────┘
```

## Troubleshooting

**Ollama not responding:**
```bash
docker restart ollama
docker logs ollama
```

**ZFS pool degraded:**
```bash
zpool status -v
zpool scrub wolf-pool
```

**NFS mount fails:**
```bash
# Check NFS service
service nfs-server status
showmount -e ionos-vm103
```

**Embedding model slow:**
- Check Xeon CPU usage: `htop`
- Verify model loaded: `docker exec ollama ollama list`
- Monitor RAM: `free -h`

## Post-Deployment Checklist

- [ ] TrueNAS accessible via Tailscale
- [ ] ZFS pool created and healthy
- [ ] NFS exports configured and mounted
- [ ] Ollama running with qwen3-embedding:4b
- [ ] Automatic PostgreSQL backups configured
- [ ] Docker containers deployed
- [ ] Embedding API proxy on VM101 working
- [ ] Monitor Grafana dashboard (optional)

**TrueNAS is now the backbone of Wolf AI infrastructure - storing everything, running Docker apps via GUI, and handling embedding inference on that Xeon.**
