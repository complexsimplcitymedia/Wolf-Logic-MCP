#!/bin/bash
# Health check all services
echo "=== Service Health ==="
curl -s http://localhost:3333 > /dev/null && echo "Wolf UI: OK" || echo "Wolf UI: DOWN"
curl -s http://localhost:8474 > /dev/null && echo "Neo4j: OK" || echo "Neo4j: DOWN"
curl -s http://localhost:6333 > /dev/null && echo "Qdrant: OK" || echo "Qdrant: DOWN"
curl -s http://localhost:1234/v1/models > /dev/null && echo "LM Studio: OK" || echo "LM Studio: DOWN"
curl -s http://localhost:8765/api/v1/apps/ > /dev/null && echo "OpenMemory: OK" || echo "OpenMemory: DOWN"
