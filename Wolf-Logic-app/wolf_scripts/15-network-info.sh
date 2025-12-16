#!/bin/bash
# Network info
echo "=== IP Addresses ==="
ip -4 addr show | grep -E "inet " | awk '{print $2, $NF}'
echo ""
echo "=== Listening Ports ==="
ss -tlnp | head -20
