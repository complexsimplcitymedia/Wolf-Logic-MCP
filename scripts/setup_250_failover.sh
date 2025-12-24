#!/bin/bash
# Setup 250 as failover node for 181
# Run this ON 250 (debian-wolf-logic-node)

set -e

echo "🔧 Setting up 250 as failover node for 181"

# 1. Enable Tailscale exit node
echo "📡 Enabling Tailscale exit node..."
sudo tailscale up --advertise-exit-node
echo "⚠️  Go to https://login.tailscale.com/admin/machines and approve 250 as exit node"

# 2. Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "📦 Installing PostgreSQL..."
    sudo apt update
    sudo apt install -y postgresql-17 postgresql-client-17
fi

# 3. Configure PostgreSQL for network access
echo "🗄️  Configuring PostgreSQL..."
sudo -u postgres psql <<EOF
-- Create wolf user if not exists
CREATE USER wolf WITH PASSWORD 'wolflogic2024';
CREATE DATABASE wolf_logic OWNER wolf;
GRANT ALL PRIVILEGES ON DATABASE wolf_logic TO wolf;
EOF

# Allow network connections
echo "host    wolf_logic    wolf    100.110.82.0/24    md5" | sudo tee -a /etc/postgresql/17/main/pg_hba.conf
echo "listen_addresses = '*'" | sudo tee -a /etc/postgresql/17/main/postgresql.conf

sudo systemctl restart postgresql

# 4. Test PostgreSQL connection
echo "🧪 Testing PostgreSQL..."
PGPASSWORD=wolflogic2024 psql -h localhost -p 5432 -U wolf -d wolf_logic -c "SELECT 'PostgreSQL ready on 250' as status;"

# 5. Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "🐳 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
fi

# 6. Deploy MCP Gateway
echo "🌐 Deploying MCP Gateway..."
mkdir -p ~/mcp-gateway-failover
cd ~/mcp-gateway-failover

# Create docker-compose.yml
cat > docker-compose.yml <<'COMPOSE_EOF'
version: '3.8'

services:
  mcp-gateway:
    image: python:3.12-slim
    container_name: wolf-mcp-gateway-250
    ports:
      - "8080:8080"
    environment:
      - PYTHONUNBUFFERED=1
      - DB_HOST=127.0.0.1
      - DB_PORT=5432
    volumes:
      - ./app:/app
    working_dir: /app
    command: >
      bash -c "apt-get update &&
               apt-get install -y postgresql-client &&
               pip install --no-cache-dir fastapi uvicorn[standard] pydantic &&
               python fastapi_server.py"
    restart: unless-stopped
    network_mode: host
COMPOSE_EOF

# Copy MCP Gateway code (Wolf needs to scp this from Mac or 181)
echo "📋 MCP Gateway config created at ~/mcp-gateway-failover/"
echo "⚠️  Need to copy fastapi_server.py to ~/mcp-gateway-failover/app/"
echo "    Run from Mac: scp /Users/apexwolf/Wolf-Logic-MCP/mcp-gateway/fastapi_server.py user@100.110.82.250:~/mcp-gateway-failover/app/"

# Create app directory
mkdir -p app

# 7. Create health check script
cat > /usr/local/bin/check_181_health.sh <<'HEALTH_EOF'
#!/bin/bash
# Monitor 181, log when it goes down

PRIMARY="100.110.82.181"
BACKUP="100.110.82.250"
LOG="/var/log/181_health.log"

check_postgres() {
    PGPASSWORD=wolflogic2024 psql -h $1 -p 5433 -U wolf -d wolf_logic -c "SELECT 1;" >/dev/null 2>&1
}

while true; do
    if check_postgres $PRIMARY; then
        echo "$(date): ✓ $PRIMARY UP" >> $LOG
    else
        echo "$(date): ⚠️  $PRIMARY DOWN - Failover to $BACKUP active" >> $LOG
    fi
    sleep 30
done
HEALTH_EOF

chmod +x /usr/local/bin/check_181_health.sh

echo "✅ 250 failover setup complete!"
echo ""
echo "Next steps:"
echo "1. Copy MCP Gateway code: scp mcp-gateway/fastapi_server.py to 250:~/mcp-gateway-failover/app/"
echo "2. Start MCP Gateway: cd ~/mcp-gateway-failover && docker-compose up -d"
echo "3. Approve Tailscale exit node: https://login.tailscale.com/admin/machines"
echo "4. Update client connection strings to use multi-host: host=100.110.82.181,100.110.82.250"
echo "5. Test failover: Stop services on 181, verify clients connect to 250"
