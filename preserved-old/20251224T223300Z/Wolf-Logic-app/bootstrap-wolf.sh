#!/bin/bash
# ===========================================
# WOLF Logic - Full Environment Bootstrap
# ===========================================
# Rebuilds entire WOLF environment from scratch on Kubuntu 25.10
#
# This script will:
# 1. Install system dependencies
# 2. Install Docker & Docker Compose
# 3. Install LM Studio
# 4. Download required AI models
# 5. Install Python/Conda environment
# 6. Install Node.js
# 7. Clone/setup repositories
# 8. Configure services
# 9. Restore data backups (if available)
#
# Usage:
#   ./bootstrap-wolf.sh           # Full install
#   ./bootstrap-wolf.sh --backup  # Create backup of current state
#   ./bootstrap-wolf.sh --restore # Restore from backup

set -e

# ===========================================
# Configuration
# ===========================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WOLF_BASE="/mnt/Wolfpack"
WOLF_APP="${WOLF_BASE}/Wolf-Logic-app"
MEM0_DIR="${WOLF_BASE}/Github/memory_layer/mem0"
BACKUP_DIR="${WOLF_BASE}/wolf-backups"
LM_STUDIO_DIR="$HOME/.lmstudio"

# LM Studio models to download
MODELS=(
    "amethyst-13b-mistral"
    "text-embedding-qwen3-embedding-4b"
)

# Docker images to pull
DOCKER_IMAGES=(
    "qdrant/qdrant:latest"
    "pgvector/pgvector:pg16"
    "neo4j:5.26.4"
    "mariadb:11.4"
    "mem0/openmemory-mcp:latest"
    "mem0/openmemory-ui:latest"
)

# Python packages
PYTHON_PACKAGES=(
    "flask"
    "flask-cors"
    "requests"
    "mysql-connector-python"
    "neo4j"
    "qdrant-client"
    "psycopg2-binary"
    "python-dotenv"
    "numpy"
    "openai"
)

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# ===========================================
# Helper Functions
# ===========================================
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_header() { echo -e "\n${CYAN}========== $1 ==========${NC}\n"; }

confirm() {
    read -p "$1 [y/N] " response
    case "$response" in
        [yY][eE][sS]|[yY]) return 0 ;;
        *) return 1 ;;
    esac
}

check_root() {
    if [ "$EUID" -eq 0 ]; then
        log_error "Don't run as root. Script will use sudo when needed."
        exit 1
    fi
}

# ===========================================
# System Dependencies
# ===========================================
install_system_deps() {
    log_header "Installing System Dependencies"

    sudo apt update
    sudo apt install -y \
        curl \
        wget \
        git \
        build-essential \
        ca-certificates \
        gnupg \
        lsb-release \
        software-properties-common \
        apt-transport-https \
        jq \
        htop \
        net-tools \
        lsof \
        unzip \
        python3 \
        python3-pip \
        python3-venv

    log_success "System dependencies installed"
}

# ===========================================
# Docker Installation
# ===========================================
install_docker() {
    log_header "Installing Docker"

    if command -v docker &> /dev/null; then
        log_warn "Docker already installed: $(docker --version)"
        return 0
    fi

    # Add Docker's official GPG key
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg

    # Add repository
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    # Install Docker
    sudo apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    # Add user to docker group
    sudo usermod -aG docker $USER

    # Enable and start Docker
    sudo systemctl enable docker
    sudo systemctl start docker

    log_success "Docker installed"
    log_warn "You may need to log out and back in for docker group to take effect"
}

# ===========================================
# LM Studio Installation
# ===========================================
install_lmstudio() {
    log_header "Installing LM Studio"

    if [ -d "$LM_STUDIO_DIR" ] || command -v lmstudio &> /dev/null; then
        log_warn "LM Studio appears to be installed"
        return 0
    fi

    # Download LM Studio AppImage
    local lmstudio_url="https://releases.lmstudio.ai/linux/x86/0.3.5/LM-Studio-0.3.5-x86_64.AppImage"
    local lmstudio_path="$HOME/Applications/LM-Studio.AppImage"

    mkdir -p "$HOME/Applications"

    log_info "Downloading LM Studio..."
    wget -O "$lmstudio_path" "$lmstudio_url"
    chmod +x "$lmstudio_path"

    # Create desktop entry
    mkdir -p "$HOME/.local/share/applications"
    cat > "$HOME/.local/share/applications/lmstudio.desktop" << EOF
[Desktop Entry]
Name=LM Studio
Exec=$lmstudio_path
Type=Application
Categories=Development;
Icon=lmstudio
Terminal=false
EOF

    # Create symlink
    mkdir -p "$HOME/.local/bin"
    ln -sf "$lmstudio_path" "$HOME/.local/bin/lmstudio"

    log_success "LM Studio installed to $lmstudio_path"
    log_info "You'll need to launch LM Studio and download models manually"
    log_info "Models needed: ${MODELS[*]}"
}

# ===========================================
# Conda/Python Environment
# ===========================================
install_conda() {
    log_header "Installing Miniconda"

    if command -v conda &> /dev/null; then
        log_warn "Conda already installed"
        return 0
    fi

    # Download Miniconda
    local conda_installer="/tmp/miniconda.sh"
    wget -O "$conda_installer" "https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"

    # Install
    bash "$conda_installer" -b -p "$HOME/miniconda3"
    rm "$conda_installer"

    # Initialize
    "$HOME/miniconda3/bin/conda" init bash
    "$HOME/miniconda3/bin/conda" init zsh 2>/dev/null || true

    log_success "Miniconda installed"
}

setup_python_env() {
    log_header "Setting up Python Environment"

    # Source conda
    source "$HOME/miniconda3/etc/profile.d/conda.sh" 2>/dev/null || true

    # Create WOLF environment
    if conda env list | grep -q "wolf-logic"; then
        log_warn "wolf-logic environment exists"
    else
        conda create -n wolf-logic python=3.11 -y
    fi

    # Activate and install packages
    conda activate wolf-logic

    log_info "Installing Python packages..."
    pip install --upgrade pip
    pip install ${PYTHON_PACKAGES[@]}

    log_success "Python environment ready"
}

# ===========================================
# Node.js Installation
# ===========================================
install_nodejs() {
    log_header "Installing Node.js"

    if command -v node &> /dev/null; then
        log_warn "Node.js already installed: $(node --version)"
        return 0
    fi

    # Install via NodeSource
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt install -y nodejs

    # Install yarn
    sudo npm install -g yarn

    log_success "Node.js $(node --version) installed"
}

# ===========================================
# Pull Docker Images
# ===========================================
pull_docker_images() {
    log_header "Pulling Docker Images"

    for image in "${DOCKER_IMAGES[@]}"; do
        log_info "Pulling $image..."
        docker pull "$image" || log_warn "Failed to pull $image"
    done

    log_success "Docker images pulled"
}

# ===========================================
# Setup Directories & Clone Repos
# ===========================================
setup_directories() {
    log_header "Setting up Directories"

    mkdir -p "$WOLF_BASE"
    mkdir -p "$WOLF_APP"
    mkdir -p "$BACKUP_DIR"
    mkdir -p "${WOLF_BASE}/Github/memory_layer"

    # Clone mem0 repo if not exists
    if [ ! -d "$MEM0_DIR" ]; then
        log_info "Cloning mem0 repository..."
        cd "${WOLF_BASE}/Github/memory_layer"
        git clone https://github.com/mem0ai/mem0.git || log_warn "Clone failed - may already exist"
    else
        log_warn "mem0 directory already exists"
    fi

    log_success "Directories ready"
}

# ===========================================
# Configure Environment
# ===========================================
configure_environment() {
    log_header "Configuring Environment"

    # Create .env file
    cat > "$WOLF_APP/.env" << 'EOF'
# WOLF Logic Environment Configuration
LMSTUDIO_BASE_URL=https://ai-studio.complexsimplicityai.com/v1
LLM_MODEL=amethyst-13b-mistral
EMBEDDER_MODEL=text-embedding-qwen3-embedding-4b
EMBEDDING_DIMS=2560

# MariaDB
MARIADB_HOST=localhost
MARIADB_PORT=32768
MARIADB_USER=root
MARIADB_PASSWORD=Lonewolf82$$$
MARIADB_DATABASE=wolf-logic

# PostgreSQL
PG_HOST=localhost
PG_PORT=5432
PG_DB=memories
PG_USER=mem0
PG_PASSWORD=mem0

# Neo4j
NEO4J_URI=bolt://localhost:8687
NEO4J_USER=neo4j
NEO4J_PASSWORD=mem0graph

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333

# OpenMemory
OPENMEMORY_API_KEY=wolf-permanent-api-key-2024-never-expires
USER=thewolfwalksalone
EOF

    # Add to bashrc
    if ! grep -q "WOLF_APP" "$HOME/.bashrc"; then
        cat >> "$HOME/.bashrc" << EOF

# WOLF Logic Environment
export WOLF_APP="$WOLF_APP"
export PATH="\$HOME/.local/bin:\$PATH"
source "$WOLF_APP/.env" 2>/dev/null || true
EOF
    fi

    log_success "Environment configured"
}

# ===========================================
# Initialize Docker Swarm
# ===========================================
init_docker_swarm() {
    log_header "Initializing Docker Swarm"

    if docker info 2>/dev/null | grep -q "Swarm: active"; then
        log_warn "Docker Swarm already active"
        return 0
    fi

    docker swarm init || log_warn "Swarm init failed (may already exist)"

    # Create overlay network
    docker network create --driver overlay --attachable openmemory_network 2>/dev/null || true

    log_success "Docker Swarm initialized"
}

# ===========================================
# Backup Functions
# ===========================================
create_backup() {
    log_header "Creating Backup"

    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_path="$BACKUP_DIR/wolf_backup_$timestamp"

    mkdir -p "$backup_path"

    log_info "Backing up configurations..."
    cp -r "$WOLF_APP" "$backup_path/Wolf-Logic-app" 2>/dev/null || true
    cp -r "$MEM0_DIR/openmemory" "$backup_path/openmemory" 2>/dev/null || true
    cp -r "$MEM0_DIR/wolf-ui" "$backup_path/wolf-ui" 2>/dev/null || true
    cp -r "$MEM0_DIR/wolf_scripts" "$backup_path/wolf_scripts" 2>/dev/null || true

    log_info "Backing up Docker volumes..."

    # Export MariaDB
    if docker ps -q -f name=wolf-mariadb | grep -q .; then
        log_info "Exporting MariaDB..."
        docker exec wolf-mariadb mysqldump -uroot -p'Lonewolf82$$$' --all-databases > "$backup_path/mariadb_backup.sql" 2>/dev/null || true
    fi

    # Export PostgreSQL
    local pg_container=$(docker ps -q -f name=openmemory_postgres | head -1)
    if [ -n "$pg_container" ]; then
        log_info "Exporting PostgreSQL..."
        docker exec "$pg_container" pg_dumpall -U mem0 > "$backup_path/postgres_backup.sql" 2>/dev/null || true
    fi

    # Export memory JSON (if exists)
    if [ -f "$MEM0_DIR/memory_export/mem0_complete_export.json" ]; then
        cp "$MEM0_DIR/memory_export/mem0_complete_export.json" "$backup_path/"
    fi

    # Compress
    log_info "Compressing backup..."
    cd "$BACKUP_DIR"
    tar -czf "wolf_backup_$timestamp.tar.gz" "wolf_backup_$timestamp"
    rm -rf "$backup_path"

    log_success "Backup created: $BACKUP_DIR/wolf_backup_$timestamp.tar.gz"
}

restore_backup() {
    log_header "Restoring from Backup"

    # Find latest backup
    local latest_backup=$(ls -t "$BACKUP_DIR"/wolf_backup_*.tar.gz 2>/dev/null | head -1)

    if [ -z "$latest_backup" ]; then
        log_error "No backup found in $BACKUP_DIR"
        exit 1
    fi

    log_info "Found backup: $latest_backup"

    if ! confirm "Restore from this backup?"; then
        exit 0
    fi

    # Extract
    local temp_dir="/tmp/wolf_restore_$$"
    mkdir -p "$temp_dir"
    tar -xzf "$latest_backup" -C "$temp_dir"

    local backup_dir=$(ls "$temp_dir")

    # Restore configs
    log_info "Restoring configurations..."
    cp -r "$temp_dir/$backup_dir/Wolf-Logic-app/"* "$WOLF_APP/" 2>/dev/null || true

    # Restore databases (after services are up)
    if [ -f "$temp_dir/$backup_dir/mariadb_backup.sql" ]; then
        log_info "MariaDB backup found - restore with:"
        echo "  docker exec -i wolf-mariadb mysql -uroot -p'Lonewolf82\$\$\$' < $temp_dir/$backup_dir/mariadb_backup.sql"
    fi

    rm -rf "$temp_dir"

    log_success "Restore complete"
}

# ===========================================
# Print Summary
# ===========================================
print_summary() {
    log_header "Installation Complete!"

    echo -e "${CYAN}"
    echo "    ██╗    ██╗ ██████╗ ██╗     ███████╗"
    echo "    ██║    ██║██╔═══██╗██║     ██╔════╝"
    echo "    ██║ █╗ ██║██║   ██║██║     █████╗  "
    echo "    ██║███╗██║██║   ██║██║     ██╔══╝  "
    echo "    ╚███╔███╔╝╚██████╔╝███████╗██║     "
    echo "     ╚══╝╚══╝  ╚═════╝ ╚══════╝╚═╝     "
    echo -e "${NC}"

    echo ""
    echo "Next steps:"
    echo "  1. Log out and back in (for docker group)"
    echo "  2. Launch LM Studio and download models:"
    echo "     - amethyst-13b-mistral"
    echo "     - text-embedding-qwen3-embedding-4b"
    echo "  3. Start WOLF stack:"
    echo "     cd $WOLF_APP && ./start-wolf.sh"
    echo ""
    echo "Useful commands:"
    echo "  ./start-wolf.sh          # Start everything"
    echo "  ./start-wolf.sh --status # Check status"
    echo "  ./start-wolf.sh --stop   # Stop everything"
    echo "  ./bootstrap-wolf.sh --backup  # Create backup"
    echo ""
}

# ===========================================
# Main
# ===========================================
main() {
    echo -e "${CYAN}"
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║        WOLF Logic Environment Bootstrap                   ║"
    echo "║        Target: Kubuntu 25.10                              ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    # Parse arguments
    case "${1:-}" in
        --backup)
            create_backup
            exit 0
            ;;
        --restore)
            restore_backup
            exit 0
            ;;
        --help)
            echo "Usage: $0 [--backup|--restore|--help]"
            echo ""
            echo "Options:"
            echo "  (none)    Full installation"
            echo "  --backup  Create backup of current state"
            echo "  --restore Restore from latest backup"
            exit 0
            ;;
    esac

    check_root

    if ! confirm "This will install the full WOLF environment. Continue?"; then
        exit 0
    fi

    install_system_deps
    install_docker
    install_conda
    setup_python_env
    install_nodejs
    install_lmstudio
    setup_directories
    pull_docker_images
    configure_environment
    init_docker_swarm

    print_summary
}

main "$@"
