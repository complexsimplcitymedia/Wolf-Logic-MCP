#!/bin/bash
# ===========================================
# Wolf Logic Desktop - Dependency Installer
# macOS
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
echo "║     Wolf Logic MCP - Dependency Installer (macOS)        ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ===========================================
# Homebrew
# ===========================================
install_homebrew() {
  log_info "Checking Homebrew..."
  
  if command -v brew &>/dev/null; then
    log_success "Homebrew already installed"
    return
  fi

  log_info "Installing Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  
  # Add brew to PATH for Apple Silicon Macs
  if [ -f /opt/homebrew/bin/brew ]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
  fi
  
  log_success "Homebrew installed"
}

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

  brew install python@3.12
  
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

  brew install --cask miniconda
  
  # Initialize conda
  if [ -f "$HOME/miniconda3/bin/conda" ]; then
    eval "$($HOME/miniconda3/bin/conda shell.bash hook)"
    conda init bash zsh
  fi
  
  log_success "Miniconda installed"
  log_info "Please restart your terminal or run: source ~/.zshrc (or ~/.bashrc)"
}

# ===========================================
# Create Messiah Environment
# ===========================================
create_messiah_env() {
  log_info "Creating Messiah conda environment..."
  
  # Find conda
  CONDA_PATH=""
  if [ -f "$HOME/miniconda3/bin/conda" ]; then
    CONDA_PATH="$HOME/miniconda3/bin/conda"
  elif [ -f "$HOME/anaconda3/bin/conda" ]; then
    CONDA_PATH="$HOME/anaconda3/bin/conda"
  elif [ -f "/opt/homebrew/Caskroom/miniconda/base/bin/conda" ]; then
    CONDA_PATH="/opt/homebrew/Caskroom/miniconda/base/bin/conda"
  fi

  if [ -z "$CONDA_PATH" ]; then
    log_warn "Conda not found, skipping environment creation"
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

  brew install ollama
  
  # Start Ollama service
  brew services start ollama
  
  log_success "Ollama installed and started"
  
  # Give Ollama a moment to start
  sleep 3
  
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

  brew install postgresql@16
  
  # Add to PATH
  echo 'export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"' >> ~/.zshrc
  
  log_success "PostgreSQL client installed"
  log_info "Please restart your terminal or run: source ~/.zshrc"
}

# ===========================================
# Tailscale
# ===========================================
install_tailscale() {
  log_info "Installing Tailscale..."
  
  if [ -d "/Applications/Tailscale.app" ]; then
    log_success "Tailscale already installed"
    return
  fi

  brew install --cask tailscale
  
  log_success "Tailscale installed"
  log_info "Open Tailscale from Applications to connect"
}

# ===========================================
# Main Installation
# ===========================================
main() {
  log_info "Starting dependency installation..."
  echo ""

  install_homebrew
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
  echo "  1. Restart your terminal or run: source ~/.zshrc"
  echo "  2. Activate Messiah environment: conda activate messiah"
  echo "  3. Open Tailscale from Applications and connect"
  echo "  4. Launch Wolf Logic Desktop app"
}

# Run main installation
main
