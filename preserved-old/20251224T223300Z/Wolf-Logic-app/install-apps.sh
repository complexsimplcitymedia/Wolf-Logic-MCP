#!/bin/bash
# ===========================================
# WOLF Logic - App Installer
# ===========================================
# Downloads and installs common apps after fresh OS install
# - Pika Backup
# - VS Code Insiders
# - Claude Code (CLI)
# - Claude Desktop
# - Google Chrome

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

DOWNLOAD_DIR="/tmp/wolf-apps"
mkdir -p "$DOWNLOAD_DIR"

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║          WOLF Logic - App Installer                       ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ===========================================
# Pika Backup (Flatpak)
# ===========================================
install_pika() {
    log_info "Installing Pika Backup..."

    # Ensure flatpak is installed
    if ! command -v flatpak &>/dev/null; then
        log_info "Installing Flatpak first..."
        sudo apt update
        sudo apt install -y flatpak
        flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
    fi

    flatpak install -y flathub org.gnome.World.PikaBackup
    log_success "Pika Backup installed"
}

# ===========================================
# VS Code Insiders
# ===========================================
install_vscode_insiders() {
    log_info "Installing VS Code Insiders..."

    # Add Microsoft GPG key and repo
    wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > "$DOWNLOAD_DIR/packages.microsoft.gpg"
    sudo install -D -o root -g root -m 644 "$DOWNLOAD_DIR/packages.microsoft.gpg" /etc/apt/keyrings/packages.microsoft.gpg

    echo "deb [arch=amd64,arm64,armhf signed-by=/etc/apt/keyrings/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main" | \
        sudo tee /etc/apt/sources.list.d/vscode.list > /dev/null

    sudo apt update
    sudo apt install -y code-insiders

    log_success "VS Code Insiders installed"
}

# ===========================================
# Claude Code (CLI)
# ===========================================
install_claude_code() {
    log_info "Installing Claude Code CLI..."

    # Requires Node.js
    if ! command -v node &>/dev/null; then
        log_info "Installing Node.js first..."
        curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
        sudo apt install -y nodejs
    fi

    # Install claude-code globally via npm
    sudo npm install -g @anthropic-ai/claude-code

    log_success "Claude Code CLI installed"
    log_info "Run 'claude' to start"
}

# ===========================================
# Claude Desktop
# ===========================================
install_claude_desktop() {
    log_info "Installing Claude Desktop..."

    # Download latest .deb from Anthropic
    cd "$DOWNLOAD_DIR"

    # Claude Desktop for Linux (official .deb)
    CLAUDE_URL="https://storage.googleapis.com/osprey-downloads-c02f6a0d-347c-492b-a752-3e0651722e97/nest-win-x64/Claude-Setup-x64.exe"

    # Check if there's a Linux version available
    # As of late 2024, Claude Desktop is available for Linux
    CLAUDE_DEB_URL="https://storage.googleapis.com/osprey-downloads-c02f6a0d-347c-492b-a752-3e0651722e97/nest-linux/claude_latest_amd64.deb"

    if wget -q --spider "$CLAUDE_DEB_URL" 2>/dev/null; then
        wget -O claude-desktop.deb "$CLAUDE_DEB_URL"
        sudo dpkg -i claude-desktop.deb || sudo apt install -f -y
        log_success "Claude Desktop installed"
    else
        # Fallback: try snap or flatpak if available
        log_warn "Direct .deb not available, trying alternative..."

        # Check for snap version
        if snap info claude 2>/dev/null | grep -q "name:"; then
            sudo snap install claude
            log_success "Claude Desktop installed via snap"
        else
            log_warn "Claude Desktop: Check https://claude.ai/download for Linux version"
            log_info "You can install manually when available"
        fi
    fi
}

# ===========================================
# Google Chrome
# ===========================================
install_chrome() {
    log_info "Installing Google Chrome..."

    cd "$DOWNLOAD_DIR"
    wget -O chrome.deb "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb"
    sudo dpkg -i chrome.deb || sudo apt install -f -y

    log_success "Google Chrome installed"
}

# ===========================================
# Main Menu
# ===========================================
show_menu() {
    echo ""
    echo "Select apps to install:"
    echo "  1) Pika Backup (Flatpak)"
    echo "  2) VS Code Insiders"
    echo "  3) Claude Code CLI"
    echo "  4) Claude Desktop"
    echo "  5) Google Chrome"
    echo "  a) All of the above"
    echo "  q) Quit"
    echo ""
}

install_all() {
    install_pika
    install_vscode_insiders
    install_claude_code
    install_claude_desktop
    install_chrome
}

# ===========================================
# Parse arguments or show menu
# ===========================================
case "${1:-}" in
    --all|-a)
        install_all
        ;;
    --pika)
        install_pika
        ;;
    --vscode|--code)
        install_vscode_insiders
        ;;
    --claude-code|--cli)
        install_claude_code
        ;;
    --claude-desktop|--desktop)
        install_claude_desktop
        ;;
    --chrome)
        install_chrome
        ;;
    --help|-h)
        echo "Usage: $0 [option]"
        echo ""
        echo "Options:"
        echo "  --all          Install all apps"
        echo "  --pika         Install Pika Backup"
        echo "  --vscode       Install VS Code Insiders"
        echo "  --claude-code  Install Claude Code CLI"
        echo "  --claude-desktop Install Claude Desktop"
        echo "  --chrome       Install Google Chrome"
        echo ""
        echo "Without options, shows interactive menu"
        ;;
    *)
        # Interactive mode
        while true; do
            show_menu
            read -p "Choice: " choice
            case $choice in
                1) install_pika ;;
                2) install_vscode_insiders ;;
                3) install_claude_code ;;
                4) install_claude_desktop ;;
                5) install_chrome ;;
                a|A) install_all; break ;;
                q|Q) break ;;
                *) log_warn "Invalid choice" ;;
            esac
        done
        ;;
esac

# Cleanup
rm -rf "$DOWNLOAD_DIR"

echo ""
log_success "Done!"
echo ""
echo "Installed apps:"
command -v pika-backup &>/dev/null && echo "  - Pika Backup"
command -v code-insiders &>/dev/null && echo "  - VS Code Insiders"
command -v claude &>/dev/null && echo "  - Claude Code CLI"
command -v google-chrome &>/dev/null && echo "  - Google Chrome"
[ -f /usr/bin/claude-desktop ] || [ -f /usr/share/applications/claude.desktop ] && echo "  - Claude Desktop"
