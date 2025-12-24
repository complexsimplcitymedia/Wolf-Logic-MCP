#!/bin/bash
# Restart the Wolf Logic Docker stack
cd /mnt/WolfPack/Wolf-Logic-app
docker compose restart
echo "Wolf stack restarted"
