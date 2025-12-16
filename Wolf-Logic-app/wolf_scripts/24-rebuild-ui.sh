#!/bin/bash
# Rebuild Wolf UI container
cd /mnt/WolfPack/Wolf-Logic-app
docker compose build --no-cache wolf-ui
docker compose up -d wolf-ui
echo "UI rebuilt and restarted"
