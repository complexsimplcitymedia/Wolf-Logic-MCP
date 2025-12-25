#!/bin/bash
# Deploy Wolf Stack to Docker Swarm
# Run on manager node (100.110.82.181)

set -e

echo "=== Wolf Stack Swarm Deployment ==="
echo ""

# Check if running on swarm manager
if ! docker info | grep -q "Swarm: active"; then
    echo "ERROR: Docker Swarm not initialized"
    echo "Run: docker swarm init --advertise-addr 100.110.82.181"
    exit 1
fi

# Label nodes for placement constraints
echo "Setting node labels..."
docker node update --label-add role=monitoring $(docker node ls --filter "role=manager" -q)
docker node update --label-add role=auth $(docker node ls --filter "role=manager" -q)

echo ""
echo "Deploying Wolf stack..."
cd /mnt/Wolf-code/Wolf-Ai-Enterptises/Wolf-Logic-MCP/server-configuration

# Deploy stack
docker stack deploy -c wolf-stack.yml wolf

echo ""
echo "Waiting for services to start..."
sleep 10

echo ""
echo "=== Service Status ==="
docker stack services wolf

echo ""
echo "=== Stack Deployed ==="
echo "Grafana: http://100.110.82.181:3000"
echo "Prometheus: http://100.110.82.181:9090"
echo "Authentik: http://100.110.82.181:9001"
echo "Caddy Admin: http://100.110.82.181:2019"
echo "Portainer: http://100.110.82.181:9000"
echo ""
echo "Monitor: docker stack ps wolf"
echo "Logs: docker service logs wolf_<service-name>"
echo "Remove: docker stack rm wolf"
