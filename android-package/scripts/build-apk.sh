#!/bin/bash
# ===========================================
# Wolf Logic Android - Build Release APK
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

# Configuration
PROJECT_DIR="${PROJECT_DIR:-$(pwd)/..}"
APP_DIR="$PROJECT_DIR/md-app"
BUILD_OUTPUT="$PROJECT_DIR/android-package/releases"
VERSION="${VERSION:-1.0.0}"
BUILD_TYPE="${BUILD_TYPE:-release}"

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║          Wolf Logic Android - Build Release APK          ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check for Android SDK
    if [ -z "$ANDROID_HOME" ]; then
        log_error "ANDROID_HOME not set. Please install Android SDK."
        log_info "Set ANDROID_HOME environment variable to your Android SDK path."
        exit 1
    fi
    
    # Check for Java
    if ! command -v java &>/dev/null; then
        log_error "Java not found. Please install JDK 17+."
        exit 1
    fi
    
    # Check for Node.js
    if ! command -v node &>/dev/null; then
        log_error "Node.js not found. Please install Node.js 18+."
        exit 1
    fi
    
    # Check for Gradle
    if ! command -v gradle &>/dev/null; then
        log_warn "Gradle not found in PATH. Will use Gradle wrapper."
    fi
    
    log_success "All prerequisites met"
}

# Build web assets
build_web_assets() {
    log_info "Building web assets..."
    
    cd "$APP_DIR"
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        log_info "Installing npm dependencies..."
        npm install
    fi
    
    # Build for production
    log_info "Running production build..."
    npm run build
    
    log_success "Web assets built"
}

# Sync with Capacitor
sync_capacitor() {
    log_info "Syncing with Capacitor..."
    
    cd "$APP_DIR"
    
    # Ensure Capacitor is installed
    if ! npm list @capacitor/core &>/dev/null; then
        log_info "Installing Capacitor..."
        npm install @capacitor/core @capacitor/cli
    fi
    
    # Sync Android platform
    npx cap sync android
    
    log_success "Capacitor synced"
}

# Update version
update_version() {
    log_info "Updating version to $VERSION..."
    
    # Calculate version code properly for semantic versioning
    # Format: MAJOR * 10000 + MINOR * 100 + PATCH
    # Example: 1.2.3 -> 10203, 10.5.2 -> 100502
    local MAJOR=$(echo "$VERSION" | cut -d. -f1)
    local MINOR=$(echo "$VERSION" | cut -d. -f2)
    local PATCH=$(echo "$VERSION" | cut -d. -f3)
    local VERSION_CODE=$((MAJOR * 10000 + MINOR * 100 + PATCH))
    
    # Update build.gradle
    cd "$APP_DIR/android/app"
    
    # Backup original
    cp build.gradle build.gradle.bak
    
    # Update versionCode and versionName
    sed -i.tmp "s/versionCode [0-9]*/versionCode $VERSION_CODE/" build.gradle
    sed -i.tmp "s/versionName \"[^\"]*\"/versionName \"$VERSION\"/" build.gradle
    
    rm -f build.gradle.tmp
    
    log_success "Version updated to $VERSION (code: $VERSION_CODE)"
}

# Build APK
build_apk() {
    log_info "Building $BUILD_TYPE APK..."
    
    cd "$APP_DIR/android"
    
    # Clean previous build
    ./gradlew clean
    
    # Build APK
    if [ "$BUILD_TYPE" = "release" ]; then
        ./gradlew assembleRelease
    else
        ./gradlew assembleDebug
    fi
    
    log_success "APK built successfully"
}

# Build AAB (Android App Bundle)
build_aab() {
    log_info "Building $BUILD_TYPE AAB..."
    
    cd "$APP_DIR/android"
    
    if [ "$BUILD_TYPE" = "release" ]; then
        ./gradlew bundleRelease
    else
        ./gradlew bundleDebug
    fi
    
    log_success "AAB built successfully"
}

# Sign APK (if release)
sign_apk() {
    if [ "$BUILD_TYPE" != "release" ]; then
        log_info "Skipping signing (debug build)"
        return
    fi
    
    log_info "Signing APK..."
    
    # Check for keystore
    local KEYSTORE_PATH="${KEYSTORE_PATH:-$HOME/.android/wolf-logic-release.keystore}"
    local KEY_ALIAS="${KEY_ALIAS:-wolf-logic}"
    local STORE_PASSWORD="${STORE_PASSWORD:-}"
    local KEY_PASSWORD="${KEY_PASSWORD:-}"
    
    if [ ! -f "$KEYSTORE_PATH" ]; then
        log_warn "Keystore not found at $KEYSTORE_PATH"
        log_info "Generate one with: keytool -genkey -v -keystore $KEYSTORE_PATH -alias $KEY_ALIAS -keyalg RSA -keysize 2048 -validity 10000"
        log_warn "APK is unsigned"
        return
    fi
    
    if [ -z "$STORE_PASSWORD" ] || [ -z "$KEY_PASSWORD" ]; then
        log_warn "STORE_PASSWORD or KEY_PASSWORD not set. APK is unsigned."
        return
    fi
    
    local UNSIGNED_APK="$APP_DIR/android/app/build/outputs/apk/release/app-release-unsigned.apk"
    local SIGNED_APK="$APP_DIR/android/app/build/outputs/apk/release/app-release-signed.apk"
    local ALIGNED_APK="$APP_DIR/android/app/build/outputs/apk/release/app-release.apk"
    
    # Sign
    "$ANDROID_HOME/build-tools/"*/apksigner sign \
        --ks "$KEYSTORE_PATH" \
        --ks-key-alias "$KEY_ALIAS" \
        --ks-pass "pass:$STORE_PASSWORD" \
        --key-pass "pass:$KEY_PASSWORD" \
        --out "$SIGNED_APK" \
        "$UNSIGNED_APK"
    
    # Align
    "$ANDROID_HOME/build-tools/"*/zipalign -v 4 "$SIGNED_APK" "$ALIGNED_APK"
    
    log_success "APK signed and aligned"
}

# Copy outputs
copy_outputs() {
    log_info "Copying build outputs..."
    
    mkdir -p "$BUILD_OUTPUT"
    
    local TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    local APK_DIR="$APP_DIR/android/app/build/outputs/apk/$BUILD_TYPE"
    local AAB_DIR="$APP_DIR/android/app/build/outputs/bundle/$BUILD_TYPE"
    
    # Copy APK
    if [ -f "$APK_DIR/app-$BUILD_TYPE.apk" ]; then
        cp "$APK_DIR/app-$BUILD_TYPE.apk" "$BUILD_OUTPUT/wolf-logic-$VERSION-$BUILD_TYPE-$TIMESTAMP.apk"
        log_success "APK copied to: $BUILD_OUTPUT/wolf-logic-$VERSION-$BUILD_TYPE-$TIMESTAMP.apk"
    fi
    
    # Copy AAB
    if [ -f "$AAB_DIR/app-$BUILD_TYPE.aab" ]; then
        cp "$AAB_DIR/app-$BUILD_TYPE.aab" "$BUILD_OUTPUT/wolf-logic-$VERSION-$BUILD_TYPE-$TIMESTAMP.aab"
        log_success "AAB copied to: $BUILD_OUTPUT/wolf-logic-$VERSION-$BUILD_TYPE-$TIMESTAMP.aab"
    fi
    
    # Create latest symlinks
    if [ "$BUILD_TYPE" = "release" ]; then
        ln -sf "wolf-logic-$VERSION-$BUILD_TYPE-$TIMESTAMP.apk" "$BUILD_OUTPUT/wolf-logic-latest.apk"
        log_info "Created symlink: $BUILD_OUTPUT/wolf-logic-latest.apk"
    fi
}

# Generate checksums
generate_checksums() {
    log_info "Generating checksums..."
    
    cd "$BUILD_OUTPUT"
    
    for file in *.apk *.aab 2>/dev/null; do
        if [ -f "$file" ] && [ ! -L "$file" ]; then
            sha256sum "$file" > "$file.sha256"
            log_info "Generated checksum for $file"
        fi
    done
    
    log_success "Checksums generated"
}

# Main build process
main() {
    log_info "Starting Android build process..."
    echo ""
    
    check_prerequisites
    echo ""
    
    build_web_assets
    echo ""
    
    sync_capacitor
    echo ""
    
    update_version
    echo ""
    
    build_apk
    echo ""
    
    # Build AAB if release
    if [ "$BUILD_TYPE" = "release" ]; then
        build_aab
        echo ""
    fi
    
    sign_apk
    echo ""
    
    copy_outputs
    echo ""
    
    generate_checksums
    echo ""
    
    log_success "Build completed successfully!"
    echo ""
    echo "Build artifacts:"
    ls -lh "$BUILD_OUTPUT"/*.apk "$BUILD_OUTPUT"/*.aab 2>/dev/null || true
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --version)
            VERSION="$2"
            shift 2
            ;;
        --debug)
            BUILD_TYPE="debug"
            shift
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --version VERSION   Set version (default: 1.0.0)"
            echo "  --debug            Build debug instead of release"
            echo "  --help             Show this help"
            echo ""
            echo "Environment variables:"
            echo "  PROJECT_DIR        Root project directory"
            echo "  ANDROID_HOME       Android SDK path"
            echo "  KEYSTORE_PATH      Path to release keystore"
            echo "  KEY_ALIAS          Keystore key alias"
            echo "  STORE_PASSWORD     Keystore password"
            echo "  KEY_PASSWORD       Key password"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Run '$0 --help' for usage"
            exit 1
            ;;
    esac
done

# Run main
main
