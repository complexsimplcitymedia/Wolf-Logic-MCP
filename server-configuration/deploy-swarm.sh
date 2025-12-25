#!/bin/bash
# =============================================================================
# Wolf Stack Multi-Node Swarm Deployment
# =============================================================================
# Distributes containers across 3 nodes:
#   Node 181 (manager/data):  Databases, Portainer, Redis
#   Node 250 (worker/compute): APIs, Monitoring (Prometheus, Grafana)
#   Node 3   (worker/apps):    UI services, LLM tools, Authentik
#
# Run this script on the manager node (100.110.82.181)
# =============================================================================

set -e

# Node configuration
MANAGER_NODE="100.110.82.181"
WORKER1_NODE="100.110.82.250"  # Compute tier
WORKER2_NODE=""                 # Apps tier - set this to your third node IP

echo "=============================================="
echo "  Wolf Stack Multi-Node Swarm Deployment"
echo "=============================================="
echo ""

# Check if running on swarm manager
if ! docker info 2>/dev/null | grep -q "Swarm: active"; then
    echo "ERROR: Docker Swarm not initialized"
    echo ""
    echo "Initialize swarm with:"
    echo "  docker swarm init --advertise-addr $MANAGER_NODE"
    echo ""
    echo "Then join worker nodes with the token from:"
    echo "  docker swarm join-token worker"
    exit 1
fi

echo "Swarm Status: Active"
echo ""

# Get node information
echo "=== Current Swarm Nodes ==="
docker node ls
echo ""

# Count nodes
NODE_COUNT=$(docker node ls --format "{{.ID}}" | wc -l)
echo "Total nodes in swarm: $NODE_COUNT"
echo ""

if [ "$NODE_COUNT" -lt 3 ]; then
    echo "WARNING: Less than 3 nodes detected in swarm"
    echo ""
    echo "To add worker nodes, run on each worker:"
    echo "  $(docker swarm join-token worker 2>/dev/null | grep 'docker swarm join')"
    echo ""
    echo "Continuing with available nodes..."
fi

# Label nodes for placement constraints
echo "=== Setting Node Labels ==="
echo ""

# Get manager node ID
MANAGER_ID=$(docker node ls --filter "role=manager" --format "{{.ID}}" | head -1)
if [ -n "$MANAGER_ID" ]; then
    echo "Labeling manager node (data tier)..."
    docker node update --label-add tier=data "$MANAGER_ID" 2>/dev/null || true
    echo "  Node $MANAGER_ID: tier=data"
fi

# Get worker node IDs and label them
WORKER_IDS=$(docker node ls --filter "role=worker" --format "{{.ID}}")
WORKER_NUM=1

for WORKER_ID in $WORKER_IDS; do
    if [ $WORKER_NUM -eq 1 ]; then
        echo "Labeling worker node 1 (compute tier)..."
        docker node update --label-add tier=compute "$WORKER_ID" 2>/dev/null || true
        echo "  Node $WORKER_ID: tier=compute"
    elif [ $WORKER_NUM -eq 2 ]; then
        echo "Labeling worker node 2 (apps tier)..."
        docker node update --label-add tier=apps "$WORKER_ID" 2>/dev/null || true
        echo "  Node $WORKER_ID: tier=apps"
    fi
    WORKER_NUM=$((WORKER_NUM + 1))
done

# If only manager exists, add all tiers to manager for single-node operation
if [ "$NODE_COUNT" -eq 1 ]; then
    echo ""
    echo "Single-node mode: Adding all tier labels to manager..."
    docker node update --label-add tier=data "$MANAGER_ID" 2>/dev/null || true
    docker node update --label-add tier=compute "$MANAGER_ID" 2>/dev/null || true
    docker node update --label-add tier=apps "$MANAGER_ID" 2>/dev/null || true
    echo "  Manager has all tiers: data, compute, apps"
fi

# If only 2 nodes, add apps tier to second node
if [ "$NODE_COUNT" -eq 2 ]; then
    echo ""
    echo "Two-node mode: Adding apps tier to compute node..."
    FIRST_WORKER=$(echo "$WORKER_IDS" | head -1)
    docker node update --label-add tier=apps "$FIRST_WORKER" 2>/dev/null || true
    echo "  Worker has: compute, apps"
fi

echo ""
echo "=== Node Labels Summary ==="
docker node ls --format "table {{.Hostname}}\t{{.Status}}\t{{.Availability}}\t{{.ManagerStatus}}"
echo ""

# Show labels per node
for NODE_ID in $(docker node ls --format "{{.ID}}"); do
    HOSTNAME=$(docker node inspect "$NODE_ID" --format "{{.Description.Hostname}}")
    LABELS=$(docker node inspect "$NODE_ID" --format '{{range $k, $v := .Spec.Labels}}{{$k}}={{$v}} {{end}}')
    echo "  $HOSTNAME: $LABELS"
done

echo ""
echo "=== Deploying Wolf Stack ==="
cd "$(dirname "$0")"

# Deploy stack
docker stack deploy -c wolf-stack.yml wolf

echo ""
echo "Waiting for services to initialize..."
sleep 15

echo ""
echo "=== Service Status ==="
docker stack services wolf --format "table {{.Name}}\t{{.Replicas}}\t{{.Image}}\t{{.Ports}}"

echo ""
echo "=== Container Distribution ==="
docker stack ps wolf --format "table {{.Name}}\t{{.Node}}\t{{.CurrentState}}" | head -30

echo ""
echo "=============================================="
echo "  Deployment Complete!"
echo "=============================================="
echo ""
echo "Service URLs (via manager node $MANAGER_NODE):"
echo "  Portainer:     https://$MANAGER_NODE:9443"
echo "  Grafana:       http://$MANAGER_NODE:3000"
echo "  Prometheus:    http://$MANAGER_NODE:9090"
echo "  Authentik:     http://$MANAGER_NODE:9001"
echo "  Wolf API:      http://$MANAGER_NODE:8000"
echo "  Wolf REST API: http://$MANAGER_NODE:3030"
echo "  Wolf MCP:      http://$MANAGER_NODE:8001"
echo "  Wolf Hunt UI:  http://$MANAGER_NODE:3333"
echo "  Open WebUI:    http://$MANAGER_NODE:3005"
echo "  AnythingLLM:   http://$MANAGER_NODE:3001"
echo ""
echo "Management Commands:"
echo "  View services: docker stack services wolf"
echo "  View tasks:    docker stack ps wolf"
echo "  View logs:     docker service logs wolf_<service-name>"
echo "  Remove stack:  docker stack rm wolf"
echo ""
