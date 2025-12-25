#!/bin/bash
# ===========================================
# Install Complex Logic Systemd Services
# ===========================================
# Run with sudo: sudo ./install-services.sh

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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYSTEMD_DIR="/etc/systemd/system"

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║      Install Complex Logic Systemd Services                  ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

if [ "$EUID" -ne 0 ]; then
    log_error "Please run as root: sudo $0"
    exit 1
fi

# Copy service files
log_info "Installing systemd service files..."

for service in "$SCRIPT_DIR/systemd/"*.service; do
    if [ -f "$service" ]; then
        name=$(basename "$service")
        cp "$service" "$SYSTEMD_DIR/$name"
        log_success "Installed $name"
    fi
done

# Reload systemd
log_info "Reloading systemd daemon..."
systemctl daemon-reload

# Enable services
log_info "Enabling services..."

systemctl enable wolf-backend.service
systemctl enable wolf-ui.service
# systemctl enable wolf-stack.service  # Uncomment to auto-start full stack
# systemctl enable wolf-mount.service  # Uncomment if not using fstab

log_success "Services installed!"

echo ""
echo "Available commands:"
echo "  sudo systemctl start wolf-backend    # Start backend API"
echo "  sudo systemctl start wolf-ui         # Start React UI"
echo "  sudo systemctl start wolf-stack      # Start full Docker stack"
echo ""
echo "  sudo systemctl status wolf-backend   # Check status"
echo "  sudo systemctl stop wolf-backend     # Stop service"
echo ""
echo "  journalctl -u wolf-backend -f        # View logs"
echo ""
