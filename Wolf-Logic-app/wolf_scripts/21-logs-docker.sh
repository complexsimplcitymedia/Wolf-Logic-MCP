#!/bin/bash
# Show recent Docker logs
for container in $(docker ps -q); do
    name=$(docker inspect --format '{{.Name}}' $container | sed 's/\///')
    echo "=== $name ==="
    docker logs --tail 10 $container 2>&1
    echo ""
done
