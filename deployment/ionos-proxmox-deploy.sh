#!/bin/bash
# Ionos Proxmox VM Deployment Script
# Deploys 3x Debian + 1x TrueNAS on 64GB bare metal
# Total: 12GB + 12GB + 12GB + 28GB = 64GB

set -e

# Proxmox API endpoint (update after server provisioning)
PROXMOX_HOST="${PROXMOX_HOST:-proxmox.ionos.local}"
PROXMOX_NODE="${PROXMOX_NODE:-pve}"

# Storage pool
STORAGE="${STORAGE:-local-lvm}"

# Network bridge
BRIDGE="${BRIDGE:-vmbr0}"

# Debian 13 (Trixie) cloud image
DEBIAN_IMAGE_URL="https://cloud.debian.org/images/cloud/trixie/latest/debian-13-generic-amd64.qcow2"
DEBIAN_IMAGE="/var/lib/vz/template/iso/debian-13-cloud.qcow2"

# TrueNAS SCALE image
TRUENAS_IMAGE_URL="https://download.truenas.com/TrueNAS-SCALE-Dragonfish/TrueNAS-SCALE-24.10.0/TrueNAS-SCALE-24.10.0.iso"
TRUENAS_IMAGE="/var/lib/vz/template/iso/truenas-scale-24.10.0.iso"

# SSH key for cloud-init
SSH_KEY="${SSH_KEY:-$(cat ~/.ssh/id_ed25519.pub)}"

echo "============================================================"
echo "IONOS PROXMOX DEPLOYMENT - WOLF AI PRODUCTION STACK"
echo "============================================================"
echo ""
echo "Architecture:"
echo "  VM100: Debian PostgreSQL - 12GB RAM, 200GB disk"
echo "  VM101: Debian Application - 12GB RAM, 150GB disk"
echo "  VM102: Debian Dev/Backup - 12GB RAM, 150GB disk"
echo "  VM103: TrueNAS Storage - 28GB RAM, 500GB disk"
echo ""
echo "Total RAM: 64GB"
echo "============================================================"
echo ""

# Download images if not present
if [ ! -f "$DEBIAN_IMAGE" ]; then
    echo "Downloading Debian 13 cloud image..."
    wget -O "$DEBIAN_IMAGE" "$DEBIAN_IMAGE_URL"
fi

if [ ! -f "$TRUENAS_IMAGE" ]; then
    echo "Downloading TrueNAS SCALE image..."
    wget -O "$TRUENAS_IMAGE" "$TRUENAS_IMAGE_URL"
fi

echo ""
echo "Creating VM 100: Debian PostgreSQL (12GB RAM)..."
echo "============================================================"

# Create VM100 - PostgreSQL
qm create 100 \
    --name "wolf-postgres" \
    --memory 12288 \
    --cores 4 \
    --sockets 1 \
    --cpu host \
    --net0 virtio,bridge=$BRIDGE \
    --scsihw virtio-scsi-pci \
    --boot c --bootdisk scsi0

# Import cloud image
qm importdisk 100 "$DEBIAN_IMAGE" "$STORAGE"
qm set 100 --scsi0 "${STORAGE}:vm-100-disk-0,size=200G"

# Cloud-init configuration
qm set 100 --ide2 "${STORAGE}:cloudinit"
qm set 100 --ciuser wolf
qm set 100 --cipassword wolflogic2024
qm set 100 --sshkeys <(echo "$SSH_KEY")
qm set 100 --ipconfig0 ip=dhcp

# Enable QEMU guest agent
qm set 100 --agent enabled=1

echo "VM100 created successfully."
echo ""

echo "Creating VM 101: Debian Application (12GB RAM)..."
echo "============================================================"

# Create VM101 - Application
qm create 101 \
    --name "wolf-application" \
    --memory 12288 \
    --cores 4 \
    --sockets 1 \
    --cpu host \
    --net0 virtio,bridge=$BRIDGE \
    --scsihw virtio-scsi-pci \
    --boot c --bootdisk scsi0

qm importdisk 101 "$DEBIAN_IMAGE" "$STORAGE"
qm set 101 --scsi0 "${STORAGE}:vm-101-disk-0,size=150G"
qm set 101 --ide2 "${STORAGE}:cloudinit"
qm set 101 --ciuser wolf
qm set 101 --cipassword wolflogic2024
qm set 101 --sshkeys <(echo "$SSH_KEY")
qm set 101 --ipconfig0 ip=dhcp
qm set 101 --agent enabled=1

echo "VM101 created successfully."
echo ""

echo "Creating VM 102: Debian Dev/Backup (12GB RAM)..."
echo "============================================================"

# Create VM102 - Dev/Backup
qm create 102 \
    --name "wolf-dev" \
    --memory 12288 \
    --cores 4 \
    --sockets 1 \
    --cpu host \
    --net0 virtio,bridge=$BRIDGE \
    --scsihw virtio-scsi-pci \
    --boot c --bootdisk scsi0

qm importdisk 102 "$DEBIAN_IMAGE" "$STORAGE"
qm set 102 --scsi0 "${STORAGE}:vm-102-disk-0,size=150G"
qm set 102 --ide2 "${STORAGE}:cloudinit"
qm set 102 --ciuser wolf
qm set 102 --cipassword wolflogic2024
qm set 102 --sshkeys <(echo "$SSH_KEY")
qm set 102 --ipconfig0 ip=dhcp
qm set 102 --agent enabled=1

echo "VM102 created successfully."
echo ""

echo "Creating VM 103: TrueNAS Storage (28GB RAM)..."
echo "============================================================"

# Create VM103 - TrueNAS
qm create 103 \
    --name "wolf-truenas" \
    --memory 28672 \
    --cores 8 \
    --sockets 1 \
    --cpu host \
    --net0 virtio,bridge=$BRIDGE \
    --scsihw virtio-scsi-pci \
    --boot order=ide2 \
    --ide2 "${STORAGE}:iso/truenas-scale-24.10.0.iso,media=cdrom"

# Primary disk
qm set 103 --scsi0 "${STORAGE}:vm-103-disk-0,size=500G"

# Additional disk for ZFS pool
qm set 103 --scsi1 "${STORAGE}:vm-103-disk-1,size=1000G"

echo "VM103 created successfully."
echo ""

echo "============================================================"
echo "DEPLOYMENT COMPLETE"
echo "============================================================"
echo ""
echo "Next steps:"
echo "  1. Start VMs: qm start 100 && qm start 101 && qm start 102"
echo "  2. Install TrueNAS manually: qm start 103 (console required)"
echo "  3. Configure Tailscale on all VMs"
echo "  4. Run migration scripts to transfer PostgreSQL clusters"
echo "  5. Deploy Wolf Memory Gateway stack"
echo ""
echo "VM Status:"
qm list
echo ""
