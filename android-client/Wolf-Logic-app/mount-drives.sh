#!/bin/bash
# ===========================================
# COMPLEX Logic - Drive Mount Script
# ===========================================
# Ensures all drives are mounted correctly after reboot
#
# Drive Layout:
#   sda1 (3.6T)  -> /mnt/Wolf-backup-4TB
#   sdb2 (1.8T)  -> /mnt/Wolfpack
#   sdc1 (1TB)   -> /mnt/Wolf-backup-1TB
#   nvme0n1p1    -> /boot/efi (system)
#   nvme0n1p2    -> / (system root)
#   nvme1n1 + nvme2n1 -> LVM wolf-code (wolfcode_lv)
#
# Usage:
#   ./mount-drives.sh           # Mount all drives
#   ./mount-drives.sh --fstab   # Generate fstab entries
#   ./mount-drives.sh --status  # Show mount status

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ===========================================
# Drive Configuration
# ===========================================
declare -A MOUNTS=(
    ["/dev/sda1"]="/mnt/Wolf-backup-4TB"
    ["/dev/sdb2"]="/mnt/Wolfpack"
    ["/dev/sdc1"]="/mnt/Wolf-backup-1TB"
)

# LVM configuration
LVM_VG="wolf-code"
LVM_LV="wolfcode_lv"
LVM_MOUNT="/mnt/wolf-code"

# ===========================================
# Functions
# ===========================================

show_status() {
    echo -e "\n${BLUE}=== Current Drive Status ===${NC}\n"

    echo "Block Devices:"
    lsblk -o NAME,SIZE,TYPE,MOUNTPOINT

    echo -e "\n${BLUE}=== Expected Mounts ===${NC}\n"

    for dev in "${!MOUNTS[@]}"; do
        mount_point="${MOUNTS[$dev]}"
        if mountpoint -q "$mount_point" 2>/dev/null; then
            echo -e "  ${GREEN}●${NC} $dev -> $mount_point"
        else
            echo -e "  ${RED}○${NC} $dev -> $mount_point (NOT MOUNTED)"
        fi
    done

    # Check LVM
    if mountpoint -q "$LVM_MOUNT" 2>/dev/null; then
        echo -e "  ${GREEN}●${NC} LVM $LVM_VG/$LVM_LV -> $LVM_MOUNT"
    else
        echo -e "  ${RED}○${NC} LVM $LVM_VG/$LVM_LV -> $LVM_MOUNT (NOT MOUNTED)"
    fi

    echo ""
}

create_mount_points() {
    log_info "Creating mount points..."

    for mount_point in "${MOUNTS[@]}"; do
        if [ ! -d "$mount_point" ]; then
            sudo mkdir -p "$mount_point"
            log_success "Created $mount_point"
        fi
    done

    if [ ! -d "$LVM_MOUNT" ]; then
        sudo mkdir -p "$LVM_MOUNT"
        log_success "Created $LVM_MOUNT"
    fi
}

mount_drives() {
    log_info "Mounting drives..."

    for dev in "${!MOUNTS[@]}"; do
        mount_point="${MOUNTS[$dev]}"

        if mountpoint -q "$mount_point" 2>/dev/null; then
            log_warn "$mount_point already mounted"
            continue
        fi

        if [ -b "$dev" ]; then
            sudo mount "$dev" "$mount_point"
            log_success "Mounted $dev -> $mount_point"
        else
            log_error "Device $dev not found"
        fi
    done
}

mount_lvm() {
    log_info "Mounting LVM volume..."

    # Activate volume group
    if ! sudo vgdisplay "$LVM_VG" &>/dev/null; then
        log_info "Activating volume group $LVM_VG..."
        sudo vgchange -ay "$LVM_VG" 2>/dev/null || log_warn "VG activation failed"
    fi

    # Mount LVM
    local lvm_dev="/dev/$LVM_VG/$LVM_LV"

    if mountpoint -q "$LVM_MOUNT" 2>/dev/null; then
        log_warn "$LVM_MOUNT already mounted"
        return
    fi

    if [ -b "$lvm_dev" ]; then
        sudo mount "$lvm_dev" "$LVM_MOUNT"
        log_success "Mounted LVM $lvm_dev -> $LVM_MOUNT"
    else
        log_warn "LVM device $lvm_dev not found"
    fi
}

generate_fstab() {
    echo -e "\n${BLUE}=== Recommended /etc/fstab Entries ===${NC}\n"
    echo "# Add these lines to /etc/fstab for automatic mounting"
    echo ""

    for dev in "${!MOUNTS[@]}"; do
        mount_point="${MOUNTS[$dev]}"

        # Get UUID
        uuid=$(sudo blkid -s UUID -o value "$dev" 2>/dev/null)

        if [ -n "$uuid" ]; then
            # Detect filesystem
            fstype=$(sudo blkid -s TYPE -o value "$dev" 2>/dev/null)
            fstype=${fstype:-auto}

            echo "# $dev -> $mount_point"
            echo "UUID=$uuid  $mount_point  $fstype  defaults,nofail  0  2"
            echo ""
        else
            echo "# WARNING: Could not get UUID for $dev"
        fi
    done

    # LVM entry
    local lvm_dev="/dev/$LVM_VG/$LVM_LV"
    if [ -b "$lvm_dev" ]; then
        uuid=$(sudo blkid -s UUID -o value "$lvm_dev" 2>/dev/null)
        fstype=$(sudo blkid -s TYPE -o value "$lvm_dev" 2>/dev/null)
        fstype=${fstype:-auto}

        if [ -n "$uuid" ]; then
            echo "# LVM wolf-code -> $LVM_MOUNT"
            echo "UUID=$uuid  $LVM_MOUNT  $fstype  defaults,nofail  0  2"
            echo ""
        fi
    fi

    echo -e "${YELLOW}To apply, run: sudo nano /etc/fstab${NC}"
    echo -e "${YELLOW}Then: sudo mount -a${NC}"
}

apply_fstab() {
    log_info "Generating and applying fstab entries..."

    local fstab_backup="/etc/fstab.backup.$(date +%Y%m%d_%H%M%S)"
    sudo cp /etc/fstab "$fstab_backup"
    log_success "Backed up fstab to $fstab_backup"

    # Check if entries already exist
    for dev in "${!MOUNTS[@]}"; do
        mount_point="${MOUNTS[$dev]}"
        uuid=$(sudo blkid -s UUID -o value "$dev" 2>/dev/null)

        if [ -n "$uuid" ]; then
            if grep -q "$uuid" /etc/fstab; then
                log_warn "Entry for $dev already in fstab"
            else
                fstype=$(sudo blkid -s TYPE -o value "$dev" 2>/dev/null)
                fstype=${fstype:-auto}

                echo "UUID=$uuid  $mount_point  $fstype  defaults,nofail  0  2" | sudo tee -a /etc/fstab > /dev/null
                log_success "Added fstab entry for $dev"
            fi
        fi
    done

    # Add LVM if not exists
    local lvm_dev="/dev/$LVM_VG/$LVM_LV"
    if [ -b "$lvm_dev" ]; then
        uuid=$(sudo blkid -s UUID -o value "$lvm_dev" 2>/dev/null)
        if [ -n "$uuid" ] && ! grep -q "$uuid" /etc/fstab; then
            fstype=$(sudo blkid -s TYPE -o value "$lvm_dev" 2>/dev/null)
            fstype=${fstype:-auto}

            echo "UUID=$uuid  $LVM_MOUNT  $fstype  defaults,nofail  0  2" | sudo tee -a /etc/fstab > /dev/null
            log_success "Added fstab entry for LVM"
        fi
    fi

    # Test mount
    log_info "Testing fstab with mount -a..."
    sudo mount -a
    log_success "All drives mounted successfully"
}

set_permissions() {
    log_info "Setting permissions..."

    local user="thewolfwalksalone"

    for mount_point in "${MOUNTS[@]}"; do
        if mountpoint -q "$mount_point" 2>/dev/null; then
            sudo chown -R "$user:$user" "$mount_point" 2>/dev/null || true
            log_success "Set ownership on $mount_point"
        fi
    done

    if mountpoint -q "$LVM_MOUNT" 2>/dev/null; then
        sudo chown -R "$user:$user" "$LVM_MOUNT" 2>/dev/null || true
        log_success "Set ownership on $LVM_MOUNT"
    fi
}

# ===========================================
# Main
# ===========================================
main() {
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║           COMPLEX Logic - Drive Mount Utility                ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    case "${1:-}" in
        --status)
            show_status
            ;;
        --fstab)
            generate_fstab
            ;;
        --apply-fstab)
            apply_fstab
            show_status
            ;;
        --help)
            echo "Usage: $0 [option]"
            echo ""
            echo "Options:"
            echo "  (none)        Mount all drives"
            echo "  --status      Show current mount status"
            echo "  --fstab       Generate fstab entries (display only)"
            echo "  --apply-fstab Add entries to /etc/fstab and mount"
            echo ""
            echo "Drive Layout:"
            echo "  sda1 (3.6T)  -> /mnt/Wolf-backup-4TB"
            echo "  sdb2 (1.8T)  -> /mnt/Wolfpack"
            echo "  sdc1 (1TB)   -> /mnt/Wolf-backup-1TB"
            echo "  LVM wolf-code -> /mnt/wolf-code"
            ;;
        *)
            create_mount_points
            mount_drives
            mount_lvm
            set_permissions
            show_status
            log_success "All drives mounted"
            ;;
    esac
}

main "$@"
