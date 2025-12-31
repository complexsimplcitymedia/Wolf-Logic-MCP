#!/bin/bash
# ===========================================
# Wolf Logic Desktop - Dependency Installer
# Linux (Debian/Ubuntu)
# ===========================================

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

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║     Wolf Logic MCP - Dependency Installer (Linux)        ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check for sudo
if [ "$EUID" -eq 0 ]; then
  log_warn "Please run as normal user, sudo will be requested when needed"
  exit 1
fi

# Update package lists
log_info "Updating package lists..."
sudo apt update

# ===========================================
# Python 3.12+
# ===========================================
install_python() {
  log_info "Installing Python 3.12..."
  
  if command -v python3.12 &>/dev/null; then
    log_success "Python 3.12 already installed"
    python3.12 --version
    return
  fi

  # Add deadsnakes PPA for Python 3.12
  sudo apt install -y software-properties-common
  sudo add-apt-repository -y ppa:deadsnakes/ppa
  sudo apt update
  
  sudo apt install -y python3.12 python3.12-venv python3.12-dev python3-pip
  
  log_success "Python 3.12 installed"
  python3.12 --version
}

# ===========================================
# Miniconda
# ===========================================
install_miniconda() {
  log_info "Installing Miniconda..."
  
  if [ -d "$HOME/miniconda3" ] || [ -d "$HOME/anaconda3" ]; then
    log_success "Conda already installed"
    return
  fi

  MINICONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"
  INSTALLER="/tmp/miniconda_installer.sh"
  
  wget -O "$INSTALLER" "$MINICONDA_URL"
  bash "$INSTALLER" -b -p "$HOME/miniconda3"
  rm "$INSTALLER"
  
  # Initialize conda
  eval "$($HOME/miniconda3/bin/conda shell.bash hook)"
  conda init bash
  
  log_success "Miniconda installed"
  log_info "Please restart your shell or run: source ~/.bashrc"
}

# ===========================================
# Create Messiah Environment
# ===========================================
create_messiah_env() {
  log_info "Creating Messiah conda environment..."
  
  if [ ! -d "$HOME/miniconda3" ] && [ ! -d "$HOME/anaconda3" ]; then
    log_warn "Conda not found, skipping environment creation"
    return
  fi

  # Find conda
  CONDA_PATH=""
  if [ -f "$HOME/miniconda3/bin/conda" ]; then
    CONDA_PATH="$HOME/miniconda3/bin/conda"
  elif [ -f "$HOME/anaconda3/bin/conda" ]; then
    CONDA_PATH="$HOME/anaconda3/bin/conda"
  fi

  if [ -z "$CONDA_PATH" ]; then
    log_warn "Conda binary not found"
    return
  fi

  # Check if messiah already exists
  if $CONDA_PATH env list | grep -q messiah; then
    log_success "Messiah environment already exists"
    return
  fi

  # Create environment
  $CONDA_PATH create -y -n messiah python=3.12
  
  # Activate and install packages
  eval "$($CONDA_PATH shell.bash hook)"
  conda activate messiah
  
  pip install --upgrade pip
  pip install \
    torch torchvision torchaudio \
    sentence-transformers transformers \
    psycopg2-binary \
    pypdf pdfplumber python-docx pillow \
    ollama langchain chromadb \
    fastapi uvicorn requests aiohttp pydantic \
    python-dotenv rich click
  
  conda deactivate
  
  log_success "Messiah environment created"
}

# ===========================================
# Ollama
# ===========================================
install_ollama() {
  log_info "Installing Ollama..."
  
  if command -v ollama &>/dev/null; then
    log_success "Ollama already installed"
    ollama --version
    return
  fi

  curl -fsSL https://ollama.com/install.sh | sh
  
  # Start Ollama service
  sudo systemctl enable ollama
  sudo systemctl start ollama
  
  log_success "Ollama installed and started"
  
  # Pull recommended models
  log_info "Pulling recommended models (this may take a while)..."
  ollama pull llama3.2
  ollama pull qwen3-embedding:4b
}

# ===========================================
# PostgreSQL Client
# ===========================================
install_postgresql_client() {
  log_info "Installing PostgreSQL client..."
  
  if command -v psql &>/dev/null; then
    log_success "PostgreSQL client already installed"
    psql --version
    return
  fi

  # Add PostgreSQL repository
  sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
  wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
  sudo apt update
  
  sudo apt install -y postgresql-client-16
  
  log_success "PostgreSQL client installed"
  psql --version
}

# ===========================================
# Tailscale
# ===========================================
install_tailscale() {
  log_info "Installing Tailscale..."
  
  if command -v tailscale &>/dev/null; then
    log_success "Tailscale already installed"
    tailscale version
    return
  fi

  curl -fsSL https://tailscale.com/install.sh | sh
  
  log_success "Tailscale installed"
  log_info "Run 'sudo tailscale up' to connect to your network"
}

# ===========================================
# Main Installation
# ===========================================
main() {
  log_info "Starting dependency installation..."
  echo ""

  install_python
  echo ""
  
  install_miniconda
  echo ""
  
  create_messiah_env
  echo ""
  
  install_ollama
  echo ""
  
  install_postgresql_client
  echo ""
  
  install_tailscale
  echo ""

  log_success "All dependencies installed successfully!"
  echo ""
  echo "Next steps:"
  echo "  1. Restart your terminal or run: source ~/.bashrc"
  echo "  2. Activate Messiah environment: source ~/miniconda3/bin/activate messiah"
  echo "  3. Connect to Tailscale: sudo tailscale up"
  echo "  4. Launch Wolf Logic Desktop app"
}

# Run main installation
main
