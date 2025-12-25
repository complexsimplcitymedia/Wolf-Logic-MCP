#!/bin/bash
# Backup configs
BACKUP_DIR="/mnt/WolfPack/backups/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"
cp -r /mnt/WolfPack/Wolf-Logic-app/*.sh "$BACKUP_DIR/"
cp -r /mnt/WolfPack/Wolf-Logic-app/wolf_scripts "$BACKUP_DIR/"
echo "Backed up to $BACKUP_DIR"
