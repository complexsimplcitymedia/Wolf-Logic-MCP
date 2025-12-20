#!/bin/bash
# Wolf AI Production Deployment - Ionos 64GB Bare Metal
# Master orchestration script for complete stack deployment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "============================================================"
echo "WOLF AI PRODUCTION DEPLOYMENT"
echo "Ionos 64GB Bare Metal with Proxmox"
echo "============================================================"
echo ""
echo "This script will deploy the complete Wolf AI production stack:"
echo ""
echo "  VM100: PostgreSQL (12GB) - wolf_logic, authentik, gemini"
echo "  VM101: Application (12GB) - Gateways, Caddy, Authentik"
echo "  VM102: Dev/Backup (12GB) - Development environment"
echo "  VM103: TrueNAS (28GB) - Docker apps, storage, embeddings"
echo ""
echo "Prerequisites:"
echo "  - Ionos bare metal server provisioned with Proxmox"
echo "  - SSH access to Proxmox host"
echo "  - Tailscale configured"
echo "  - DNS records pointing to Ionos IP"
echo ""
echo "============================================================"
echo ""

# Prompt for Proxmox connection details
read -p "Proxmox host (IP or hostname): " PROXMOX_HOST
export PROXMOX_HOST

read -p "Proxmox node name [pve]: " PROXMOX_NODE
export PROXMOX_NODE="${PROXMOX_NODE:-pve}"

read -p "Storage pool [local-lvm]: " STORAGE
export STORAGE="${STORAGE:-local-lvm}"

echo ""
echo "Configuration:"
echo "  Proxmox: $PROXMOX_HOST"
echo "  Node: $PROXMOX_NODE"
echo "  Storage: $STORAGE"
echo ""

read -p "Proceed with deployment? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Deployment cancelled."
    exit 0
fi

echo ""
echo "============================================================"
echo "PHASE 1: Proxmox VM Provisioning"
echo "============================================================"
echo ""

# Copy deployment script to Proxmox host
scp "$SCRIPT_DIR/ionos-proxmox-deploy.sh" "root@$PROXMOX_HOST:/tmp/"

# Execute on Proxmox
ssh "root@$PROXMOX_HOST" "bash /tmp/ionos-proxmox-deploy.sh"

echo ""
echo "✓ VMs created successfully"
echo ""
echo "Waiting for VMs to boot (60 seconds)..."
sleep 60

# Get VM IP addresses
echo ""
echo "Retrieving VM IP addresses..."

VM100_IP=$(ssh "root@$PROXMOX_HOST" "qm guest cmd 100 network-get-interfaces | jq -r '.[] | select(.name==\"eth0\") | .[\"ip-addresses\"][] | select(.\"ip-address-type\"==\"ipv4\") | .\"ip-address\"'")
VM101_IP=$(ssh "root@$PROXMOX_HOST" "qm guest cmd 101 network-get-interfaces | jq -r '.[] | select(.name==\"eth0\") | .[\"ip-addresses\"][] | select(.\"ip-address-type\"==\"ipv4\") | .\"ip-address\"'")
VM102_IP=$(ssh "root@$PROXMOX_HOST" "qm guest cmd 102 network-get-interfaces | jq -r '.[] | select(.name==\"eth0\") | .[\"ip-addresses\"][] | select(.\"ip-address-type\"==\"ipv4\") | .\"ip-address\"'")

echo "  VM100 (PostgreSQL): $VM100_IP"
echo "  VM101 (Application): $VM101_IP"
echo "  VM102 (Dev/Backup): $VM102_IP"
echo "  VM103 (TrueNAS): Manual installation required"
echo ""

export IONOS_POSTGRES_HOST="$VM100_IP"
export IONOS_APP_HOST="$VM101_IP"
export IONOS_DEV_HOST="$VM102_IP"

echo "============================================================"
echo "PHASE 2: PostgreSQL Migration"
echo "============================================================"
echo ""

read -p "Migrate PostgreSQL clusters now? (yes/no): " MIGRATE
if [ "$MIGRATE" = "yes" ]; then
    bash "$SCRIPT_DIR/migrate-postgres.sh"
    echo ""
    echo "✓ PostgreSQL clusters migrated"
else
    echo "Skipping PostgreSQL migration (run manually later)"
fi

echo ""
echo "============================================================"
echo "PHASE 3: Application Stack Deployment"
echo "============================================================"
echo ""

read -p "Deploy application stack now? (yes/no): " DEPLOY_APP
if [ "$DEPLOY_APP" = "yes" ]; then
    bash "$SCRIPT_DIR/deploy-application-stack.sh"
    echo ""
    echo "✓ Application stack deployed"
else
    echo "Skipping application deployment (run manually later)"
fi

echo ""
echo "============================================================"
echo "PHASE 4: TrueNAS Configuration"
echo "============================================================"
echo ""
echo "TrueNAS (VM103) requires manual installation via console."
echo ""
echo "Steps:"
echo "  1. Access Proxmox web UI: https://$PROXMOX_HOST:8006"
echo "  2. Select VM 103 (wolf-truenas)"
echo "  3. Open console and follow TrueNAS installer"
echo "  4. After installation, follow: deployment/truenas-setup-guide.md"
echo ""

read -p "Press Enter to continue after TrueNAS is installed..."

echo ""
echo "============================================================"
echo "PHASE 5: Service Startup and Health Checks"
echo "============================================================"
echo ""

# Start services on VM101
echo "Starting Wolf Memory Gateways..."
ssh "wolf@$VM101_IP" << 'ENDSSH'
    sudo systemctl start wolf-gateway-8001
    sudo systemctl start wolf-gateway-8002
    sudo systemctl start wolf-gateway-8003
    sudo systemctl start caddy
    cd ~/wolf-stack/authentik && docker-compose up -d
ENDSSH

echo "Waiting for services to start (30 seconds)..."
sleep 30

# Health checks
echo ""
echo "Running health checks..."

HEALTH_8001=$(curl -s -o /dev/null -w "%{http_code}" "http://$VM101_IP:8001/health")
HEALTH_8002=$(curl -s -o /dev/null -w "%{http_code}" "http://$VM101_IP:8002/health")
HEALTH_8003=$(curl -s -o /dev/null -w "%{http_code}" "http://$VM101_IP:8003/health")

if [ "$HEALTH_8001" = "200" ] && [ "$HEALTH_8002" = "200" ] && [ "$HEALTH_8003" = "200" ]; then
    echo "✓ All gateways healthy"
else
    echo "⚠ Some gateways may be unhealthy:"
    echo "  Gateway 8001: $HEALTH_8001"
    echo "  Gateway 8002: $HEALTH_8002"
    echo "  Gateway 8003: $HEALTH_8003"
fi

# Test Caddy load balancer
CADDY_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "http://$VM101_IP:8000/health")
if [ "$CADDY_HEALTH" = "200" ]; then
    echo "✓ Caddy load balancer healthy"
else
    echo "⚠ Caddy load balancer not responding (HTTP $CADDY_HEALTH)"
fi

echo ""
echo "============================================================"
echo "DEPLOYMENT COMPLETE"
echo "============================================================"
echo ""
echo "Production endpoints:"
echo "  Load Balancer: http://$VM101_IP:8000"
echo "  Swagger UI: http://$VM101_IP:8000/docs"
echo "  Gateway 1: http://$VM101_IP:8001"
echo "  Gateway 2: http://$VM101_IP:8002"
echo "  Gateway 3: http://$VM101_IP:8003"
echo "  Authentik: http://$VM101_IP:9500"
echo ""
echo "PostgreSQL clusters (on VM100):"
echo "  wolf_logic: $VM100_IP:5433"
echo "  authentik: $VM100_IP:3306"
echo "  gemini: $VM100_IP:5436"
echo ""
echo "Next steps:"
echo "  1. Configure Tailscale on all VMs for secure access"
echo "  2. Update DNS: api.complexsimplicityai.com → $VM101_IP"
echo "  3. Configure Authentik OAuth applications"
echo "  4. Test end-to-end memory operations"
echo "  5. Monitor logs and performance"
echo ""
echo "Documentation:"
echo "  TrueNAS setup: deployment/truenas-setup-guide.md"
echo "  PostgreSQL migration: deployment/migrate-postgres.sh"
echo "  App deployment: deployment/deploy-application-stack.sh"
echo ""
echo "Ready for 100 beta testers."
echo "============================================================"
echo ""
