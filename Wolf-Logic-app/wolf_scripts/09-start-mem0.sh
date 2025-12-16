#!/bin/bash
# Start Mem0 service
docker start mem0 2>/dev/null || echo "Mem0 container not found"
echo "Mem0 started"
