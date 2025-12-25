#!/bin/bash
# ===========================================
# Move Docker Data to Wolfpack Drive + Add Caddy
# ===========================================
# 1. Moves /var/lib/docker to /mnt/Wolfpack/docker
# 2. Adds Caddy as a Docker container
# Preserves all images, containers, volumes, networks

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

DOCKER_SRC="/var/lib/docker"
DOCKER_DST="/mnt/wolf-code/docker"
CADDY_DATA="/mnt/wolf-code/caddy"

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║      Move Docker + Containerize Caddy                     ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if destination mount exists (LVM on NVMe drives)
if ! mountpoint -q /mnt/wolf-code 2>/dev/null; then
    log_error "/mnt/wolf-code is not mounted!"
    log_info "Mount the LVM: sudo mount /dev/wolf-code/wolfcode_lv /mnt/wolf-code"
    exit 1
fi

# Check current Docker size
DOCKER_SIZE=$(sudo du -sh "$DOCKER_SRC" 2>/dev/null | cut -f1)
log_info "Current Docker data size: $DOCKER_SIZE"

# Check destination space
DEST_FREE=$(df -h /mnt/wolf-code | tail -1 | awk '{print $4}')
log_info "Free space on wolf-code (NVMe LVM): $DEST_FREE"

read -p "Continue with move? [y/N] " confirm
if [[ ! "$confirm" =~ ^[yY] ]]; then
    exit 0
fi

# ===========================================
# Step 1: Backup existing Caddy config
# ===========================================
log_info "Backing up existing Caddy configuration..."
mkdir -p "$CADDY_DATA"/{config,data,logs}

# Copy existing Caddy config if present
if [ -f /etc/caddy/Caddyfile ]; then
    cp /etc/caddy/Caddyfile "$CADDY_DATA/Caddyfile"
    log_success "Backed up Caddyfile"
elif [ -d /etc/caddy ]; then
    cp -r /etc/caddy/* "$CADDY_DATA/config/" 2>/dev/null || true
fi

# Copy Caddy data if exists
if [ -d /var/lib/caddy ]; then
    sudo cp -r /var/lib/caddy/* "$CADDY_DATA/data/" 2>/dev/null || true
    log_success "Backed up Caddy data (certificates, etc.)"
fi

# Stop existing Caddy service
if systemctl is-active caddy &>/dev/null; then
    log_info "Stopping Caddy service..."
    sudo systemctl stop caddy
    sudo systemctl disable caddy 2>/dev/null || true
fi

# ===========================================
# Step 2: Stop Docker and Sync
# ===========================================
log_info "Stopping Docker..."
sudo systemctl stop docker docker.socket containerd

log_info "Syncing Docker data to $DOCKER_DST..."
sudo rsync -aP --info=progress2 "$DOCKER_SRC/" "$DOCKER_DST/"

# Configure Docker
log_info "Configuring Docker to use new location..."
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json > /dev/null << EOF
{
    "data-root": "$DOCKER_DST"
}
EOF

# Start Docker
log_info "Starting Docker..."
sudo systemctl start docker
sleep 5

# ===========================================
# Step 3: Create Caddy Container
# ===========================================
log_info "Setting up Caddy container..."

# Create default Caddyfile if none exists
if [ ! -f "$CADDY_DATA/Caddyfile" ]; then
    cat > "$CADDY_DATA/Caddyfile" << 'EOF'
# COMPLEX Logic Caddy Configuration
# Reverse proxy for all WOLF services

{
    admin off
    log {
        output file /var/log/caddy/access.log
        format json
    }
}

# LM Studio API
ai-studio.complexsimplicityai.com {
    reverse_proxy host.docker.internal:1234
}

# Neo4j Graph Database
neo4j-ai.complexsimplicityai.com {
    reverse_proxy host.docker.internal:8474
}

# OpenMemory API
openmemory.complexsimplicityai.com {
    reverse_proxy host.docker.internal:8765
}

# OpenMemory UI
memory-ui.complexsimplicityai.com {
    reverse_proxy host.docker.internal:8080
}

# Wolf Dashboard
wolf.complexsimplicityai.com {
    reverse_proxy host.docker.internal:4500
}

# Qdrant Vector DB
qdrant.complexsimplicityai.com {
    reverse_proxy host.docker.internal:6333
}
EOF
    log_success "Created default Caddyfile"
fi

# Pull Caddy image
log_info "Pulling Caddy image..."
docker pull caddy:latest

# Remove existing caddy container if exists
docker rm -f wolf-caddy 2>/dev/null || true

# Create and start Caddy container
log_info "Starting Caddy container..."
docker run -d \
    --name wolf-caddy \
    --restart unless-stopped \
    --network host \
    -v "$CADDY_DATA/Caddyfile:/etc/caddy/Caddyfile:ro" \
    -v "$CADDY_DATA/data:/data" \
    -v "$CADDY_DATA/config:/config" \
    -v "$CADDY_DATA/logs:/var/log/caddy" \
    caddy:latest

sleep 3

# ===========================================
# Step 4: Verify
# ===========================================
log_info "Verifying..."

if docker info &>/dev/null; then
    NEW_ROOT=$(docker info 2>/dev/null | grep "Docker Root Dir" | awk '{print $4}')
    log_success "Docker now using: $NEW_ROOT"
fi

if docker ps | grep -q wolf-caddy; then
    log_success "Caddy container running"
else
    log_error "Caddy container not running!"
    docker logs wolf-caddy 2>&1 | tail -20
fi

# Show status
echo ""
echo -e "${GREEN}=== Migration Complete ===${NC}"
echo ""
echo "Docker data:  $DOCKER_DST"
echo "Caddy config: $CADDY_DATA/Caddyfile"
echo "Caddy data:   $CADDY_DATA/data"
echo ""
echo "Commands:"
echo "  docker logs wolf-caddy              # View Caddy logs"
echo "  docker exec wolf-caddy caddy reload # Reload config"
echo "  docker restart wolf-caddy           # Restart Caddy"
echo ""
log_warn "Old Docker data still at $DOCKER_SRC"
log_warn "Remove after confirming: sudo rm -rf $DOCKER_SRC"
