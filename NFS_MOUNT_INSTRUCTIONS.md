# NFS Mount Instructions - Client Dumps Directory

## Server: 100.110.82.181 (csmcloud-server)
**Export:** `/mnt/Wolf-code/Wolf-Ai-Enterptises/Wolf-Logic-MCP/data/client-dumps`

## For Remote Nodes (e.g., 245 - csmcloud-client)

### One-time Setup

```bash
# Install NFS client
sudo apt update && sudo apt install -y nfs-common

# Create local mount point
sudo mkdir -p /mnt/wolf-client-dumps

# Mount the NFS share
sudo mount -t nfs 100.110.82.181:/mnt/Wolf-code/Wolf-Ai-Enterptises/Wolf-Logic-MCP/data/client-dumps /mnt/wolf-client-dumps

# Verify mount
df -h | grep wolf-client-dumps
```

### Persistent Mount (Add to /etc/fstab)

```bash
# Add this line to /etc/fstab for auto-mount on boot
echo "100.110.82.181:/mnt/Wolf-code/Wolf-Ai-Enterptises/Wolf-Logic-MCP/data/client-dumps /mnt/wolf-client-dumps nfs defaults,_netdev 0 0" | sudo tee -a /etc/fstab

# Test mount
sudo mount -a
```

### Usage on Remote Node

```bash
# Write transcripts to NFS mount
echo '{"transcript": "USER: test message", "session": "node-245", "timestamp": "'$(date -Iseconds)'"}' >> /mnt/wolf-client-dumps/transcript_$(date +%Y%m%d).jsonl

# Verify file appears on server
ssh 100.110.82.181 "tail -1 /mnt/Wolf-code/Wolf-Ai-Enterptises/Wolf-Logic-MCP/data/client-dumps/transcript_$(date +%Y%m%d).jsonl"
```

## Pipeline Flow

1. **Remote node** writes to `/mnt/wolf-client-dumps/transcript_YYYYMMDD.jsonl`
2. **NFS** syncs to server `data/client-dumps/`
3. **swarm-intake** (on 181) watches and processes automatically
4. **pgai-queue** ingests to PostgreSQL
5. **pgai vectorizer** embeds with qwen3-embedding:4b

## Troubleshooting

```bash
# Check if NFS share is accessible
showmount -e 100.110.82.181

# Check mount status
mount | grep wolf-client-dumps

# Remount if needed
sudo umount /mnt/wolf-client-dumps
sudo mount -a

# Check NFS logs on server
sudo journalctl -u nfs-kernel-server -n 50
```

## Network Requirements

- Tailscale mesh network: 100.110.82.0/24
- NFS ports: 2049 (TCP/UDP), 111 (portmapper)
- Nodes must be on same Tailscale network
