#!/bin/bash
# Start Qdrant
docker start qdrant 2>/dev/null || docker run -d --name qdrant -p 6333:6333 qdrant/qdrant
echo "Qdrant started"
