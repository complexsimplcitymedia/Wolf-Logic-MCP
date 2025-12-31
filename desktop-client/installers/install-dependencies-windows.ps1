# ===========================================
# Wolf Logic Desktop - Dependency Installer
# Windows (PowerShell)
# ===========================================

$ErrorActionPreference = "Stop"

function Write-Info { Write-Host "[INFO] $args" -ForegroundColor Blue }
function Write-Success { Write-Host "[OK] $args" -ForegroundColor Green }
function Write-Warning { Write-Host "[WARN] $args" -ForegroundColor Yellow }
function Write-Error { Write-Host "[ERROR] $args" -ForegroundColor Red }

Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Blue
Write-Host "║     Wolf Logic MCP - Dependency Installer (Windows)      ║" -ForegroundColor Blue
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Blue
Write-Host ""

# Check for winget
if (!(Get-Command winget -ErrorAction SilentlyContinue)) {
    Write-Error "winget is not available. Please install App Installer from Microsoft Store."
    exit 1
}

# ===========================================
# Python 3.12+
# ===========================================
function Install-Python {
    Write-Info "Installing Python 3.12..."
    
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "Python 3\.1[2-9]") {
        Write-Success "Python 3.12+ already installed"
        python --version
        return
    }

    winget install --id Python.Python.3.12 --silent --accept-source-agreements
    
    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    
    Write-Success "Python 3.12 installed"
    python --version
}

# ===========================================
# Miniconda
# ===========================================
function Install-Miniconda {
    Write-Info "Installing Miniconda..."
    
    if (Test-Path "$env:USERPROFILE\miniconda3" -or Test-Path "$env:USERPROFILE\anaconda3") {
        Write-Success "Conda already installed"
        return
    }

    winget install --id Anaconda.Miniconda3 --silent --accept-source-agreements
    
    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    
    Write-Success "Miniconda installed"
    Write-Info "Please restart PowerShell to use conda commands"
}

# ===========================================
# Create Messiah Environment
# ===========================================
function Create-MessiahEnv {
    Write-Info "Creating Messiah conda environment..."
    
    # Find conda
    $condaPath = $null
    if (Test-Path "$env:USERPROFILE\miniconda3\Scripts\conda.exe") {
        $condaPath = "$env:USERPROFILE\miniconda3\Scripts\conda.exe"
    } elseif (Test-Path "$env:USERPROFILE\anaconda3\Scripts\conda.exe") {
        $condaPath = "$env:USERPROFILE\anaconda3\Scripts\conda.exe"
    }

    if (!$condaPath) {
        Write-Warning "Conda not found, skipping environment creation"
        return
    }

    # Check if messiah already exists
    $envList = & $condaPath env list 2>&1 | Out-String
    if ($envList -match "messiah") {
        Write-Success "Messiah environment already exists"
        return
    }

    # Create environment
    & $condaPath create -y -n messiah python=3.12
    
    # Activate and install packages
    & $condaPath run -n messiah pip install --upgrade pip
    & $condaPath run -n messiah pip install `
        torch torchvision torchaudio `
        sentence-transformers transformers `
        psycopg2-binary `
        pypdf pdfplumber python-docx pillow `
        ollama langchain chromadb `
        fastapi uvicorn requests aiohttp pydantic `
        python-dotenv rich click
    
    Write-Success "Messiah environment created"
}

# ===========================================
# Ollama
# ===========================================
function Install-Ollama {
    Write-Info "Installing Ollama..."
    
    if (Get-Command ollama -ErrorAction SilentlyContinue) {
        Write-Success "Ollama already installed"
        ollama --version
        return
    }

    winget install --id Ollama.Ollama --silent --accept-source-agreements
    
    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    
    Write-Success "Ollama installed"
    
    # Start Ollama service
    Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 3
    
    # Pull recommended models
    Write-Info "Pulling recommended models (this may take a while)..."
    ollama pull llama3.2
    ollama pull qwen3-embedding:4b
}

# ===========================================
# PostgreSQL Client
# ===========================================
function Install-PostgreSQL {
    Write-Info "Installing PostgreSQL client..."
    
    if (Get-Command psql -ErrorAction SilentlyContinue) {
        Write-Success "PostgreSQL client already installed"
        psql --version
        return
    }

    winget install --id PostgreSQL.PostgreSQL.16 --silent --accept-source-agreements
    
    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    
    Write-Success "PostgreSQL client installed"
}

# ===========================================
# Tailscale
# ===========================================
function Install-Tailscale {
    Write-Info "Installing Tailscale..."
    
    if (Get-Command tailscale -ErrorAction SilentlyContinue) {
        Write-Success "Tailscale already installed"
        tailscale version
        return
    }

    winget install --id Tailscale.Tailscale --silent --accept-source-agreements
    
    Write-Success "Tailscale installed"
    Write-Info "Open Tailscale from system tray to connect"
}

# ===========================================
# Main Installation
# ===========================================
function Main {
    Write-Info "Starting dependency installation..."
    Write-Host ""

    Install-Python
    Write-Host ""
    
    Install-Miniconda
    Write-Host ""
    
    Create-MessiahEnv
    Write-Host ""
    
    Install-Ollama
    Write-Host ""
    
    Install-PostgreSQL
    Write-Host ""
    
    Install-Tailscale
    Write-Host ""

    Write-Success "All dependencies installed successfully!"
    Write-Host ""
    Write-Host "Next steps:"
    Write-Host "  1. Restart PowerShell"
    Write-Host "  2. Activate Messiah environment: conda activate messiah"
    Write-Host "  3. Open Tailscale from system tray and connect"
    Write-Host "  4. Launch Wolf Logic Desktop app"
}

# Run main installation
Main
