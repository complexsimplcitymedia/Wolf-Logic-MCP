#!/bin/bash
# System info
echo "=== CPU ==="
lscpu | grep -E "Model name|CPU\(s\)|MHz"
echo ""
echo "=== Memory ==="
free -h
echo ""
echo "=== Disk ==="
df -h /
