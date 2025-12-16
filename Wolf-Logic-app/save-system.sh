#!/bin/bash
# ===========================================
# WOLF Logic - System Settings & Apps Backup
# ===========================================
# Saves system settings, custom binaries, and configs
# for restoration after OS reinstall
#
# Usage:
#   ./save-system.sh           # Full backup
#   ./save-system.sh --list    # Show what will be backed up
#   ./save-system.sh --restore # Restore from backup

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Backup destination (NVMe for speed, survives OS reinstall)
BACKUP_ROOT="/mnt/wolf-code/system-backup"
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
USER_HOME="/home/thewolfwalksalone"

# Custom binaries to preserve (add more as needed)
CUSTOM_BINARIES=(
    "/usr/bin/dsnote"
)

# System config directories to backup
SYSTEM_CONFIGS=(
    "/etc/docker"
    "/etc/caddy"
    "/etc/systemd/system/wolf*.service"
    "/etc/fstab"
    "/etc/hosts"
    "/etc/environment"
)

# User dotfiles/configs to backup
USER_CONFIGS=(
    ".bashrc"
    ".bash_aliases"
    ".profile"
    ".zshrc"
    ".config/lmstudio"
    ".config/Code"
    ".ssh"
    ".gnupg"
    ".gitconfig"
    ".local/share/applications"
)

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║        WOLF Logic - System Backup Utility                 ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ===========================================
# Functions
# ===========================================

show_list() {
    echo -e "\n${BLUE}=== Items to Backup ===${NC}\n"

    echo "Custom Binaries:"
    for bin in "${CUSTOM_BINARIES[@]}"; do
        if [ -f "$bin" ]; then
            size=$(du -h "$bin" 2>/dev/null | cut -f1)
            echo -e "  ${GREEN}●${NC} $bin ($size)"
        else
            echo -e "  ${RED}○${NC} $bin (not found)"
        fi
    done

    echo -e "\nSystem Configs:"
    for conf in "${SYSTEM_CONFIGS[@]}"; do
        if [ -e "$conf" ] || ls $conf 2>/dev/null | head -1 >/dev/null; then
            echo -e "  ${GREEN}●${NC} $conf"
        else
            echo -e "  ${YELLOW}○${NC} $conf (not found)"
        fi
    done

    echo -e "\nUser Configs ($USER_HOME):"
    for conf in "${USER_CONFIGS[@]}"; do
        full_path="$USER_HOME/$conf"
        if [ -e "$full_path" ]; then
            echo -e "  ${GREEN}●${NC} ~/$conf"
        else
            echo -e "  ${YELLOW}○${NC} ~/$conf (not found)"
        fi
    done

    echo ""
}

backup_binaries() {
    log_info "Backing up custom binaries..."

    local bin_dir="$BACKUP_ROOT/binaries"
    mkdir -p "$bin_dir"

    for bin in "${CUSTOM_BINARIES[@]}"; do
        if [ -f "$bin" ]; then
            local name=$(basename "$bin")
            sudo cp -p "$bin" "$bin_dir/$name"
            # Also save any related libs
            ldd "$bin" 2>/dev/null | grep "=> /" | awk '{print $3}' | while read lib; do
                if [[ "$lib" == *"dsnote"* ]] || [[ "$lib" == *"speech"* ]]; then
                    sudo cp -p "$lib" "$bin_dir/" 2>/dev/null || true
                fi
            done
            log_success "Backed up $name"
        else
            log_warn "Binary not found: $bin"
        fi
    done
}

backup_system_configs() {
    log_info "Backing up system configs..."

    local sys_dir="$BACKUP_ROOT/system"
    mkdir -p "$sys_dir/etc" "$sys_dir/systemd"

    # Docker config
    if [ -d "/etc/docker" ]; then
        sudo cp -r /etc/docker "$sys_dir/etc/"
        log_success "Backed up /etc/docker"
    fi

    # Caddy config
    if [ -d "/etc/caddy" ]; then
        sudo cp -r /etc/caddy "$sys_dir/etc/"
        log_success "Backed up /etc/caddy"
    fi

    # Wolf services
    for service in /etc/systemd/system/wolf*.service; do
        if [ -f "$service" ]; then
            sudo cp "$service" "$sys_dir/systemd/"
            log_success "Backed up $(basename $service)"
        fi
    done

    # Critical system files
    for file in /etc/fstab /etc/hosts /etc/environment; do
        if [ -f "$file" ]; then
            sudo cp "$file" "$sys_dir/etc/"
            log_success "Backed up $file"
        fi
    done
}

backup_user_configs() {
    log_info "Backing up user configs..."

    local user_dir="$BACKUP_ROOT/user"
    mkdir -p "$user_dir"

    for conf in "${USER_CONFIGS[@]}"; do
        local full_path="$USER_HOME/$conf"
        if [ -e "$full_path" ]; then
            local parent_dir=$(dirname "$conf")
            if [ "$parent_dir" != "." ]; then
                mkdir -p "$user_dir/$parent_dir"
            fi
            cp -rp "$full_path" "$user_dir/$conf" 2>/dev/null || sudo cp -rp "$full_path" "$user_dir/$conf"
            log_success "Backed up ~/$conf"
        fi
    done
}

backup_package_list() {
    log_info "Saving installed packages list..."

    local pkg_dir="$BACKUP_ROOT/packages"
    mkdir -p "$pkg_dir"

    # APT packages (manually installed)
    apt-mark showmanual > "$pkg_dir/apt-manual.txt" 2>/dev/null || true

    # All APT packages
    dpkg --get-selections > "$pkg_dir/dpkg-selections.txt" 2>/dev/null || true

    # Snap packages
    snap list 2>/dev/null | tail -n +2 | awk '{print $1}' > "$pkg_dir/snap-packages.txt" || true

    # Flatpak packages
    flatpak list --app --columns=application 2>/dev/null > "$pkg_dir/flatpak-packages.txt" || true

    # pip packages (global)
    pip3 list --format=freeze 2>/dev/null > "$pkg_dir/pip-global.txt" || true

    # npm global packages
    npm list -g --depth=0 2>/dev/null > "$pkg_dir/npm-global.txt" || true

    log_success "Package lists saved"
}

backup_dconf() {
    log_info "Backing up desktop settings (dconf)..."

    local dconf_dir="$BACKUP_ROOT/dconf"
    mkdir -p "$dconf_dir"

    # Dump all dconf settings
    dconf dump / > "$dconf_dir/dconf-full-backup.txt" 2>/dev/null || true

    # KDE-specific (Kubuntu)
    if [ -d "$USER_HOME/.config/kde*" ] || [ -d "$USER_HOME/.config/plasma*" ]; then
        cp -r "$USER_HOME/.config/kde"* "$dconf_dir/" 2>/dev/null || true
        cp -r "$USER_HOME/.config/plasma"* "$dconf_dir/" 2>/dev/null || true
        log_success "Backed up KDE/Plasma settings"
    fi

    # General desktop settings
    for cfg in "$USER_HOME/.config/autostart" "$USER_HOME/.local/share/konsole"; do
        if [ -d "$cfg" ]; then
            local name=$(basename "$cfg")
            cp -r "$cfg" "$dconf_dir/$name" 2>/dev/null || true
        fi
    done

    log_success "Desktop settings backed up"
}

do_backup() {
    # Check mount
    if ! mountpoint -q /mnt/wolf-code 2>/dev/null; then
        log_error "/mnt/wolf-code is not mounted!"
        log_info "Run: sudo mount /dev/wolf-code/wolfcode_lv /mnt/wolf-code"
        exit 1
    fi

    # Create backup directory
    mkdir -p "$BACKUP_ROOT"

    log_info "Backup destination: $BACKUP_ROOT"
    echo ""

    backup_binaries
    backup_system_configs
    backup_user_configs
    backup_package_list
    backup_dconf

    # Create manifest
    echo "Backup created: $(date)" > "$BACKUP_ROOT/MANIFEST.txt"
    echo "Hostname: $(hostname)" >> "$BACKUP_ROOT/MANIFEST.txt"
    echo "OS: $(lsb_release -ds 2>/dev/null || cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)" >> "$BACKUP_ROOT/MANIFEST.txt"
    echo "Kernel: $(uname -r)" >> "$BACKUP_ROOT/MANIFEST.txt"
    echo "" >> "$BACKUP_ROOT/MANIFEST.txt"
    echo "Contents:" >> "$BACKUP_ROOT/MANIFEST.txt"
    find "$BACKUP_ROOT" -type f | sed "s|$BACKUP_ROOT/||" >> "$BACKUP_ROOT/MANIFEST.txt"

    # Summary
    local total_size=$(du -sh "$BACKUP_ROOT" | cut -f1)

    echo ""
    echo -e "${GREEN}=== Backup Complete ===${NC}"
    echo ""
    echo "Location: $BACKUP_ROOT"
    echo "Size: $total_size"
    echo ""
    echo "Contents:"
    ls -la "$BACKUP_ROOT"
    echo ""
    log_success "System backup saved to wolf-code (NVMe)"
    log_info "This survives OS reinstall - just remount the LVM"
}

do_restore() {
    if [ ! -d "$BACKUP_ROOT" ]; then
        log_error "No backup found at $BACKUP_ROOT"
        exit 1
    fi

    echo -e "${YELLOW}=== Restore from Backup ===${NC}"
    echo ""
    echo "This will restore:"
    echo "  - Custom binaries to /usr/bin/"
    echo "  - System configs to /etc/"
    echo "  - User configs to $USER_HOME/"
    echo ""
    read -p "Continue? [y/N] " confirm
    if [[ ! "$confirm" =~ ^[yY] ]]; then
        exit 0
    fi

    # Restore binaries
    if [ -d "$BACKUP_ROOT/binaries" ]; then
        log_info "Restoring custom binaries..."
        for bin in "$BACKUP_ROOT/binaries"/*; do
            if [ -f "$bin" ]; then
                local name=$(basename "$bin")
                sudo cp -p "$bin" "/usr/bin/$name"
                sudo chmod +x "/usr/bin/$name"
                log_success "Restored $name"
            fi
        done
    fi

    # Restore system configs (selective)
    if [ -d "$BACKUP_ROOT/system/etc/docker" ]; then
        log_info "Restoring Docker config..."
        sudo mkdir -p /etc/docker
        sudo cp -r "$BACKUP_ROOT/system/etc/docker"/* /etc/docker/
        log_success "Restored /etc/docker"
    fi

    # Restore user configs
    if [ -d "$BACKUP_ROOT/user" ]; then
        log_info "Restoring user configs..."
        for item in "$BACKUP_ROOT/user"/*; do
            local name=$(basename "$item")
            cp -rp "$item" "$USER_HOME/$name" 2>/dev/null || sudo cp -rp "$item" "$USER_HOME/$name"
            log_success "Restored ~/$name"
        done
        # Fix ownership
        sudo chown -R thewolfwalksalone:thewolfwalksalone "$USER_HOME"
    fi

    # Show package restore instructions
    echo ""
    echo -e "${BLUE}=== Package Restore Instructions ===${NC}"
    echo ""
    echo "APT packages (manually installed):"
    echo "  cat $BACKUP_ROOT/packages/apt-manual.txt | xargs sudo apt install -y"
    echo ""
    echo "Snap packages:"
    echo "  cat $BACKUP_ROOT/packages/snap-packages.txt | xargs -I {} sudo snap install {}"
    echo ""
    echo "pip packages:"
    echo "  pip3 install -r $BACKUP_ROOT/packages/pip-global.txt"
    echo ""

    log_success "Restore complete!"
}

# ===========================================
# Main
# ===========================================

case "${1:-}" in
    --list)
        show_list
        ;;
    --restore)
        do_restore
        ;;
    --help)
        echo "Usage: $0 [option]"
        echo ""
        echo "Options:"
        echo "  (none)    Full backup to $BACKUP_ROOT"
        echo "  --list    Show what will be backed up"
        echo "  --restore Restore from existing backup"
        echo ""
        echo "Backup includes:"
        echo "  - DS Note and other custom binaries"
        echo "  - System configs (/etc/docker, /etc/caddy, services)"
        echo "  - User dotfiles and configs"
        echo "  - Installed package lists"
        echo "  - Desktop/KDE settings"
        ;;
    *)
        do_backup
        ;;
esac
