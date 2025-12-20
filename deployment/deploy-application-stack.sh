#!/bin/bash
# Wolf Application Stack Deployment
# Deploys to Ionos VM101 (wolf-application)
# Components: Wolf Memory Gateways (3x), Caddy, Authentik, Redis

set -e

# Target host (Ionos VM101)
TARGET_HOST="${IONOS_APP_HOST:-ionos-vm101.ts.net}"
TARGET_USER="wolf"

# PostgreSQL connection (Ionos VM100)
POSTGRES_HOST="${IONOS_POSTGRES_HOST:-ionos-vm100.ts.net}"

echo "============================================================"
echo "WOLF APPLICATION STACK DEPLOYMENT"
echo "============================================================"
echo ""
echo "Target: $TARGET_HOST (Ionos VM101)"
echo "PostgreSQL: $POSTGRES_HOST (Ionos VM100)"
echo ""
echo "Components:"
echo "  - Wolf Memory Gateways (3 replicas: 8001, 8002, 8003)"
echo "  - Caddy (reverse proxy + load balancer)"
echo "  - Authentik (OAuth/OIDC)"
echo "  - Redis"
echo ""
echo "============================================================"
echo ""

# Create deployment directory structure on target
echo "Creating deployment structure..."
ssh "$TARGET_USER@$TARGET_HOST" << 'ENDSSH'
    mkdir -p ~/wolf-stack/{api,caddy,authentik,systemd}
ENDSSH

# Transfer Wolf Memory Gateway
echo ""
echo "Transferring Wolf Memory Gateway..."
scp /mnt/Wolf-code/Wolf-Ai-Enterptises/api/wolf_memory_gateway.py \
    "$TARGET_USER@$TARGET_HOST:~/wolf-stack/api/"

# Transfer Caddyfile
echo "Transferring Caddyfile..."
scp /mnt/Wolf-code/Wolf-Ai-Enterptises/api/Caddyfile \
    "$TARGET_USER@$TARGET_HOST:~/wolf-stack/caddy/"

# Transfer Authentik docker-compose
echo "Transferring Authentik configuration..."
scp /mnt/Wolf-code/Wolf-Ai-Enterptises/authentik/docker-compose.yml \
    "$TARGET_USER@$TARGET_HOST:~/wolf-stack/authentik/"
scp /mnt/Wolf-code/Wolf-Ai-Enterptises/authentik/.env \
    "$TARGET_USER@$TARGET_HOST:~/wolf-stack/authentik/"

# Install and configure on target
echo ""
echo "Installing dependencies on target..."

ssh "$TARGET_USER@$TARGET_HOST" << ENDSSH
    set -e

    # Update system
    sudo apt update && sudo apt upgrade -y

    # Install Python 3.12, pip, venv
    sudo apt install -y python3.12 python3-pip python3-venv

    # Install Docker and Docker Compose
    sudo apt install -y docker.io docker-compose
    sudo systemctl enable docker
    sudo systemctl start docker
    sudo usermod -aG docker $USER

    # Install Caddy
    sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | \
        sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | \
        sudo tee /etc/apt/sources.list.d/caddy-stable.list
    sudo apt update
    sudo apt install -y caddy

    # Install Redis
    sudo apt install -y redis-server
    sudo systemctl enable redis-server
    sudo systemctl start redis-server

    echo "✓ Dependencies installed"

    # Create Python virtual environment for gateways
    cd ~/wolf-stack/api
    python3.12 -m venv venv
    source venv/bin/activate

    # Install Python dependencies
    pip install --upgrade pip
    pip install fastapi uvicorn psycopg2-binary pydantic python-multipart

    echo "✓ Python environment configured"

    # Update gateway configuration with Ionos PostgreSQL host
    sed -i 's/100.110.82.181/$POSTGRES_HOST/g' wolf_memory_gateway.py

    # Create systemd service files for 3 gateway replicas
    cat > ~/wolf-stack/systemd/wolf-gateway-8001.service << 'EOF'
[Unit]
Description=Wolf Memory Gateway - Replica 1 (8001)
After=network.target

[Service]
Type=simple
User=wolf
WorkingDirectory=/home/wolf/wolf-stack/api
Environment="POSTGRES_HOST=$POSTGRES_HOST"
Environment="POSTGRES_PORT=5433"
Environment="POSTGRES_USER=wolf"
Environment="POSTGRES_PASSWORD=wolflogic2024"
Environment="POSTGRES_DB=wolf_logic"
ExecStart=/home/wolf/wolf-stack/api/venv/bin/uvicorn wolf_memory_gateway:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    cat > ~/wolf-stack/systemd/wolf-gateway-8002.service << 'EOF'
[Unit]
Description=Wolf Memory Gateway - Replica 2 (8002)
After=network.target

[Service]
Type=simple
User=wolf
WorkingDirectory=/home/wolf/wolf-stack/api
Environment="POSTGRES_HOST=$POSTGRES_HOST"
Environment="POSTGRES_PORT=5433"
Environment="POSTGRES_USER=wolf"
Environment="POSTGRES_PASSWORD=wolflogic2024"
Environment="POSTGRES_DB=wolf_logic"
ExecStart=/home/wolf/wolf-stack/api/venv/bin/uvicorn wolf_memory_gateway:app --host 0.0.0.0 --port 8002
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    cat > ~/wolf-stack/systemd/wolf-gateway-8003.service << 'EOF'
[Unit]
Description=Wolf Memory Gateway - Replica 3 (8003)
After=network.target

[Service]
Type=simple
User=wolf
WorkingDirectory=/home/wolf/wolf-stack/api
Environment="POSTGRES_HOST=$POSTGRES_HOST"
Environment="POSTGRES_PORT=5433"
Environment="POSTGRES_USER=wolf"
Environment="POSTGRES_PASSWORD=wolflogic2024"
Environment="POSTGRES_DB=wolf_logic"
ExecStart=/home/wolf/wolf-stack/api/venv/bin/uvicorn wolf_memory_gateway:app --host 0.0.0.0 --port 8003
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Install systemd services
    sudo cp ~/wolf-stack/systemd/*.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable wolf-gateway-8001 wolf-gateway-8002 wolf-gateway-8003

    echo "✓ Gateway services configured"

    # Configure Caddy
    sudo cp ~/wolf-stack/caddy/Caddyfile /etc/caddy/Caddyfile
    sudo systemctl enable caddy

    echo "✓ Caddy configured"

    # Update Authentik docker-compose with Ionos PostgreSQL host
    cd ~/wolf-stack/authentik
    sed -i 's/host.docker.internal/$POSTGRES_HOST/g' docker-compose.yml

    echo "✓ Authentik configured"

ENDSSH

echo ""
echo "============================================================"
echo "DEPLOYMENT COMPLETE"
echo "============================================================"
echo ""
echo "Start services:"
echo "  ssh $TARGET_USER@$TARGET_HOST"
echo ""
echo "  # Start Wolf gateways"
echo "  sudo systemctl start wolf-gateway-8001"
echo "  sudo systemctl start wolf-gateway-8002"
echo "  sudo systemctl start wolf-gateway-8003"
echo ""
echo "  # Start Caddy load balancer"
echo "  sudo systemctl start caddy"
echo ""
echo "  # Start Authentik"
echo "  cd ~/wolf-stack/authentik"
echo "  docker-compose up -d"
echo ""
echo "Health check:"
echo "  curl http://$TARGET_HOST:8000/health"
echo ""
echo "Swagger UI:"
echo "  http://$TARGET_HOST:8000/docs"
echo ""
