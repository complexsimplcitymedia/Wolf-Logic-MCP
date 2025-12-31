#!/bin/bash
# ===========================================
# Wolf Logic Android - Setup Build Environment
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
echo "║       Wolf Logic Android - Setup Build Environment       ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Detect OS
detect_os() {
    case "$(uname -s)" in
        Linux*)     OS="Linux";;
        Darwin*)    OS="macOS";;
        MINGW*|MSYS*|CYGWIN*) OS="Windows";;
        *)          OS="Unknown";;
    esac
    log_info "Detected OS: $OS"
}

# Install Android SDK (Linux)
install_android_sdk_linux() {
    log_info "Installing Android SDK..."
    
    if [ -d "$HOME/Android/Sdk" ]; then
        log_success "Android SDK already installed"
        export ANDROID_HOME="$HOME/Android/Sdk"
        return
    fi
    
    # Install command line tools
    local SDK_TOOLS_URL="https://dl.google.com/android/repository/commandlinetools-linux-10406996_latest.zip"
    local SDK_DIR="$HOME/Android/Sdk"
    local TOOLS_DIR="$SDK_DIR/cmdline-tools"
    
    mkdir -p "$TOOLS_DIR"
    cd "$TOOLS_DIR"
    
    wget -O cmdline-tools.zip "$SDK_TOOLS_URL"
    unzip cmdline-tools.zip
    mv cmdline-tools latest
    rm cmdline-tools.zip
    
    export ANDROID_HOME="$SDK_DIR"
    export PATH="$PATH:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools"
    
    # Accept licenses
    yes | sdkmanager --licenses
    
    # Install required components
    sdkmanager "platform-tools" "platforms;android-34" "build-tools;34.0.0"
    
    # Add to bashrc
    if ! grep -q "ANDROID_HOME" "$HOME/.bashrc"; then
        echo "" >> "$HOME/.bashrc"
        echo "# Android SDK" >> "$HOME/.bashrc"
        echo "export ANDROID_HOME=\"$HOME/Android/Sdk\"" >> "$HOME/.bashrc"
        echo "export PATH=\"\$PATH:\$ANDROID_HOME/cmdline-tools/latest/bin:\$ANDROID_HOME/platform-tools\"" >> "$HOME/.bashrc"
    fi
    
    log_success "Android SDK installed"
    log_info "Please restart your shell or run: source ~/.bashrc"
}

# Install Android SDK (macOS)
install_android_sdk_macos() {
    log_info "Installing Android SDK..."
    
    if [ -d "$HOME/Library/Android/sdk" ]; then
        log_success "Android SDK already installed"
        export ANDROID_HOME="$HOME/Library/Android/sdk"
        return
    fi
    
    # Use Homebrew
    if command -v brew &>/dev/null; then
        brew install --cask android-commandlinetools
        export ANDROID_HOME="$HOME/Library/Android/sdk"
        export PATH="$PATH:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools"
        
        # Install components
        yes | sdkmanager --licenses
        sdkmanager "platform-tools" "platforms;android-34" "build-tools;34.0.0"
        
        # Add to shell config
        local SHELL_CONFIG="$HOME/.zshrc"
        if [ -f "$HOME/.bashrc" ]; then
            SHELL_CONFIG="$HOME/.bashrc"
        fi
        
        if ! grep -q "ANDROID_HOME" "$SHELL_CONFIG"; then
            echo "" >> "$SHELL_CONFIG"
            echo "# Android SDK" >> "$SHELL_CONFIG"
            echo "export ANDROID_HOME=\"$HOME/Library/Android/sdk\"" >> "$SHELL_CONFIG"
            echo "export PATH=\"\$PATH:\$ANDROID_HOME/cmdline-tools/latest/bin:\$ANDROID_HOME/platform-tools\"" >> "$SHELL_CONFIG"
        fi
        
        log_success "Android SDK installed"
    else
        log_error "Homebrew not found. Please install it first."
        exit 1
    fi
}

# Install JDK
install_jdk() {
    log_info "Checking Java Development Kit..."
    
    if command -v java &>/dev/null; then
        local JAVA_VERSION=$(java -version 2>&1 | head -n 1 | cut -d'"' -f2)
        log_success "JDK already installed: $JAVA_VERSION"
        return
    fi
    
    case "$OS" in
        Linux)
            sudo apt update
            sudo apt install -y openjdk-17-jdk
            ;;
        macOS)
            brew install openjdk@17
            sudo ln -sfn /opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk /Library/Java/JavaVirtualMachines/openjdk-17.jdk
            ;;
        *)
            log_error "Please install JDK 17+ manually"
            exit 1
            ;;
    esac
    
    log_success "JDK installed"
}

# Install Node.js
install_nodejs() {
    log_info "Checking Node.js..."
    
    if command -v node &>/dev/null; then
        local NODE_VERSION=$(node --version)
        log_success "Node.js already installed: $NODE_VERSION"
        return
    fi
    
    case "$OS" in
        Linux)
            curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
            sudo apt install -y nodejs
            ;;
        macOS)
            brew install node@20
            ;;
        *)
            log_error "Please install Node.js 18+ manually"
            exit 1
            ;;
    esac
    
    log_success "Node.js installed"
}

# Install Gradle
install_gradle() {
    log_info "Checking Gradle..."
    
    if command -v gradle &>/dev/null; then
        local GRADLE_VERSION=$(gradle --version | grep "Gradle" | cut -d' ' -f2)
        log_success "Gradle already installed: $GRADLE_VERSION"
        return
    fi
    
    log_info "Gradle will be installed via Gradle Wrapper"
    log_success "Gradle Wrapper will be used"
}

# Generate keystore for release signing
generate_keystore() {
    log_info "Checking release keystore..."
    
    local KEYSTORE_PATH="$HOME/.android/wolf-logic-release.keystore"
    
    if [ -f "$KEYSTORE_PATH" ]; then
        log_success "Release keystore already exists"
        return
    fi
    
    log_info "Generating release keystore..."
    mkdir -p "$HOME/.android"
    
    # Prompt for password or use environment variable
    local STORE_PASS="${ANDROID_KEYSTORE_PASSWORD:-}"
    if [ -z "$STORE_PASS" ]; then
        log_warn "ANDROID_KEYSTORE_PASSWORD not set, using prompted password"
        read -sp "Enter keystore password: " STORE_PASS
        echo ""
    fi
    
    keytool -genkey -v \
        -keystore "$KEYSTORE_PATH" \
        -alias wolf-logic \
        -keyalg RSA \
        -keysize 2048 \
        -validity 10000 \
        -storepass "$STORE_PASS" \
        -keypass "$STORE_PASS" \
        -dname "CN=Wolf Logic, OU=Development, O=Complex Simplicity Media, L=City, ST=State, C=US"
    
    log_success "Release keystore generated at $KEYSTORE_PATH"
    log_warn "Store your password securely! Set ANDROID_KEYSTORE_PASSWORD env var to avoid prompts."
}

# Install Capacitor
install_capacitor() {
    log_info "Checking Capacitor..."
    
    local PROJECT_DIR="${PROJECT_DIR:-$(pwd)/..}"
    local APP_DIR="$PROJECT_DIR/md-app"
    
    if [ ! -d "$APP_DIR" ]; then
        log_warn "App directory not found: $APP_DIR"
        return
    fi
    
    cd "$APP_DIR"
    
    if npm list @capacitor/core &>/dev/null; then
        log_success "Capacitor already installed"
        return
    fi
    
    log_info "Installing Capacitor..."
    npm install @capacitor/core @capacitor/cli @capacitor/android
    
    log_success "Capacitor installed"
}

# Main setup
main() {
    log_info "Setting up Android build environment..."
    echo ""
    
    detect_os
    echo ""
    
    install_jdk
    echo ""
    
    install_nodejs
    echo ""
    
    case "$OS" in
        Linux)
            install_android_sdk_linux
            ;;
        macOS)
            install_android_sdk_macos
            ;;
        *)
            log_error "Unsupported OS: $OS"
            log_info "Please install Android SDK manually"
            exit 1
            ;;
    esac
    echo ""
    
    install_gradle
    echo ""
    
    generate_keystore
    echo ""
    
    install_capacitor
    echo ""
    
    log_success "Build environment setup complete!"
    echo ""
    echo "Next steps:"
    echo "  1. Restart your terminal or run: source ~/.bashrc (Linux) or source ~/.zshrc (macOS)"
    echo "  2. Run: ./build-apk.sh to build the Android app"
    echo ""
    echo "Environment variables:"
    echo "  ANDROID_HOME: $ANDROID_HOME"
    echo "  JAVA_HOME: $JAVA_HOME"
}

# Run main
main
