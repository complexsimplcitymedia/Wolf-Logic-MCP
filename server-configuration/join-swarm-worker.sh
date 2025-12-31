#!/bin/bash
# =============================================================================
# Join Worker Node to Wolf Docker Swarm
# =============================================================================
# Run this script on worker nodes (100.110.82.250 or third node) to join
# the Docker Swarm cluster managed by 100.110.82.181
#
# Prerequisites:
#   - Docker installed on this node
#   - Network connectivity to manager (100.110.82.181)
#   - Tailscale connected (if using Tailscale network)
# =============================================================================

set -e

MANAGER_NODE="100.110.82.181"
MANAGER_PORT="2377"

echo "=============================================="
echo "  Wolf Swarm Worker Node Setup"
echo "=============================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed"
    echo ""
    echo "Install Docker with:"
    echo "  curl -fsSL https://get.docker.com | sh"
    echo "  sudo usermod -aG docker \$USER"
    exit 1
fi

# Check if already in a swarm
if docker info 2>/dev/null | grep -q "Swarm: active"; then
    echo "This node is already part of a swarm"
    echo ""
    docker info 2>/dev/null | grep -A 5 "Swarm:"
    echo ""
    echo "To leave current swarm and rejoin, run:"
    echo "  docker swarm leave --force"
    exit 0
fi

echo "Docker Status: OK"
echo ""

# Check connectivity to manager
echo "Testing connectivity to manager node ($MANAGER_NODE)..."
if ! ping -c 1 -W 3 "$MANAGER_NODE" &> /dev/null; then
    echo "WARNING: Cannot ping manager node"
    echo "This might be OK if ICMP is blocked"
fi

# Check if port 2377 is reachable
if command -v nc &> /dev/null; then
    if nc -z -w 3 "$MANAGER_NODE" "$MANAGER_PORT" 2>/dev/null; then
        echo "Manager swarm port ($MANAGER_PORT): Reachable"
    else
        echo "WARNING: Cannot reach manager swarm port ($MANAGER_PORT)"
        echo "Ensure firewall allows TCP 2377, 7946, 4789 (UDP)"
    fi
fi

echo ""
echo "=============================================="
echo "  Join Command Required"
echo "=============================================="
echo ""
echo "To join this node to the swarm, you need the join token from the manager."
echo ""
echo "On the MANAGER node ($MANAGER_NODE), run:"
echo "  docker swarm join-token worker"
echo ""
echo "Then paste the 'docker swarm join' command here, or run it directly:"
echo ""
echo "Example command format:"
echo "  docker swarm join --token SWMTKN-1-xxx $MANAGER_NODE:$MANAGER_PORT"
echo ""

# If join token is provided as argument
if [ -n "$1" ]; then
    echo "Joining swarm with provided token..."
    docker swarm join --token "$1" "$MANAGER_NODE:$MANAGER_PORT"

    echo ""
    echo "=============================================="
    echo "  Worker Node Joined Successfully!"
    echo "=============================================="
    echo ""
    echo "This node is now part of the Wolf swarm."
    echo ""
    echo "Next steps (run on manager node $MANAGER_NODE):"
    echo "  1. Verify node: docker node ls"
    echo "  2. Deploy stack: ./deploy-swarm.sh"
    echo ""
fi

echo "=============================================="
echo "  Required Firewall Ports"
echo "=============================================="
echo ""
echo "Ensure these ports are open between all swarm nodes:"
echo "  TCP 2377  - Cluster management"
echo "  TCP 7946  - Node communication"
echo "  UDP 7946  - Node communication"
echo "  UDP 4789  - Overlay network traffic"
echo ""
echo "For UFW:"
echo "  sudo ufw allow 2377/tcp"
echo "  sudo ufw allow 7946/tcp"
echo "  sudo ufw allow 7946/udp"
echo "  sudo ufw allow 4789/udp"
echo ""
