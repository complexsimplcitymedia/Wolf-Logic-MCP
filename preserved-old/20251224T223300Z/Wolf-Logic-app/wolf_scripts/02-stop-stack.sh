#!/bin/bash
# Stop the Wolf Logic Docker stack
cd /mnt/WolfPack/Wolf-Logic-app
docker compose down
echo "Wolf stack stopped"
