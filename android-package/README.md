# Wolf Logic Android Packaging

Automated build and packaging system for Wolf Logic Android applications.

## Overview

This directory contains scripts and configuration for building, signing, and distributing Wolf Logic Android applications. Supports both APK (sideloading) and AAB (Google Play Store) formats.

## Quick Start

```bash
# 1. Setup build environment (first time only)
cd android-package/scripts
./setup-build-env.sh

# 2. Build release APK
./build-apk.sh --version 1.0.0

# 3. Find your APK
ls -lh ../releases/
```

## Scripts

### `setup-build-env.sh`

Sets up the complete Android build environment including:
- Android SDK (command line tools)
- JDK 17+
- Node.js 20+
- Gradle wrapper
- Capacitor CLI
- Release keystore generation

**Usage:**
```bash
./setup-build-env.sh
```

**What it installs:**
- **Linux (Debian/Ubuntu)**: Downloads Android SDK, installs OpenJDK 17, Node.js 20
- **macOS**: Uses Homebrew to install android-commandlinetools, openjdk@17, node@20

### `build-apk.sh`

Main build script that:
1. Builds web assets (Vite/React)
2. Syncs with Capacitor
3. Updates version numbers
4. Builds APK and AAB
5. Signs release builds
6. Generates checksums

**Usage:**
```bash
# Build release APK (default)
./build-apk.sh --version 1.0.0

# Build debug APK
./build-apk.sh --debug

# Custom configuration
PROJECT_DIR=/path/to/project ./build-apk.sh --version 2.0.0
```

**Options:**
- `--version VERSION`: Set app version (default: 1.0.0)
- `--debug`: Build debug instead of release
- `--help`: Show help

**Environment Variables:**
- `PROJECT_DIR`: Root project directory (default: parent of android-package)
- `ANDROID_HOME`: Android SDK path (auto-detected)
- `KEYSTORE_PATH`: Path to release keystore (default: ~/.android/wolf-logic-release.keystore)
- `KEY_ALIAS`: Keystore key alias (default: wolf-logic)
- `STORE_PASSWORD`: Keystore password
- `KEY_PASSWORD`: Key password

## Build Output

All build artifacts are saved to `android-package/releases/`:

```
releases/
├── wolf-logic-1.0.0-release-20250101_120000.apk
├── wolf-logic-1.0.0-release-20250101_120000.apk.sha256
├── wolf-logic-1.0.0-release-20250101_120000.aab
├── wolf-logic-1.0.0-release-20250101_120000.aab.sha256
└── wolf-logic-latest.apk -> wolf-logic-1.0.0-release-20250101_120000.apk
```

## APK Types

### Debug APK
- For development and testing
- Not signed with release key
- Includes debugging tools
- Larger file size

### Release APK
- Production-ready
- Signed with release keystore
- Optimized and minified
- Smaller file size
- Ready for distribution

### Android App Bundle (AAB)
- Google Play Store format
- Optimized per-device downloads
- Split APKs for different configurations
- Required for Play Store upload

## Signing Configuration

### Development (Auto-generated)

On first run, `setup-build-env.sh` creates a keystore at `~/.android/wolf-logic-release.keystore`:

```
Keystore: ~/.android/wolf-logic-release.keystore
Alias: wolf-logic
Password: wolf-logic-2024
Validity: 10,000 days
```

**⚠️ For production, create your own keystore with a strong password!**

### Production Keystore

Generate a production keystore:

```bash
keytool -genkey -v \
  -keystore ~/wolf-logic-production.keystore \
  -alias wolf-logic-prod \
  -keyalg RSA \
  -keysize 2048 \
  -validity 10000
```

Then use it:

```bash
KEYSTORE_PATH=~/wolf-logic-production.keystore \
KEY_ALIAS=wolf-logic-prod \
STORE_PASSWORD=your-password \
KEY_PASSWORD=your-password \
./build-apk.sh --version 1.0.0
```

**Important:**
- Store keystore file securely (encrypted backup)
- Never commit keystore to git
- Document passwords in secure password manager
- Keep copy in multiple secure locations

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Build Android

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup JDK
        uses: actions/setup-java@v4
        with:
          distribution: 'temurin'
          java-version: '17'
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - name: Setup Android SDK
        uses: android-actions/setup-android@v3
      
      - name: Decode keystore
        run: |
          echo "${{ secrets.KEYSTORE_BASE64 }}" | base64 -d > release.keystore
      
      - name: Build APK
        env:
          KEYSTORE_PATH: ./release.keystore
          KEY_ALIAS: ${{ secrets.KEY_ALIAS }}
          STORE_PASSWORD: ${{ secrets.STORE_PASSWORD }}
          KEY_PASSWORD: ${{ secrets.KEY_PASSWORD }}
          VERSION: ${{ github.ref_name }}
        run: |
          cd android-package/scripts
          ./build-apk.sh --version ${VERSION#v}
      
      - name: Upload APK
        uses: actions/upload-artifact@v4
        with:
          name: app-release
          path: android-package/releases/*.apk
```

## Distribution

### Sideloading (APK)

1. Enable "Unknown Sources" in Android settings
2. Transfer APK to device:
   ```bash
   adb push releases/wolf-logic-latest.apk /sdcard/Download/
   ```
3. Install via file manager or:
   ```bash
   adb install releases/wolf-logic-latest.apk
   ```

### Google Play Store (AAB)

1. Build AAB:
   ```bash
   ./build-apk.sh --version 1.0.0
   ```
2. Upload to Google Play Console
3. Complete store listing
4. Submit for review

### F-Droid

1. Create metadata in `fdroid/`:
   ```
   fdroid/
   └── metadata/
       └── com.wolf.mdapp.yml
   ```
2. Submit to F-Droid repository
3. Ensure FOSS compliance (no proprietary dependencies)

## Troubleshooting

### Android SDK not found

```bash
export ANDROID_HOME=$HOME/Android/Sdk
export PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin
```

### Gradle build fails

```bash
# Clean and retry
cd ../md-app/android
./gradlew clean
cd ../../android-package/scripts
./build-apk.sh --version 1.0.0
```

### Keystore issues

```bash
# Verify keystore
keytool -list -v -keystore ~/.android/wolf-logic-release.keystore

# Generate new keystore
./setup-build-env.sh  # Will skip existing keystore
```

### Node modules issues

```bash
cd ../md-app
rm -rf node_modules package-lock.json
npm install
cd ../android-package/scripts
./build-apk.sh --version 1.0.0
```

## Version Management

Version format: `MAJOR.MINOR.PATCH`

Examples:
- `1.0.0` - Initial release
- `1.1.0` - New features
- `1.1.1` - Bug fixes
- `2.0.0` - Breaking changes

Version code is automatically calculated: `1.0.0` → `100`, `1.2.3` → `123`

## Testing

### Manual Testing

```bash
# Build debug APK
./build-apk.sh --debug

# Install on connected device
adb install -r ../releases/wolf-logic-*-debug-*.apk

# View logs
adb logcat | grep WolfLogic
```

### Automated Testing

```bash
cd ../md-app/android
./gradlew test
./gradlew connectedAndroidTest  # Requires connected device
```

## Dependencies

### System Requirements
- Linux or macOS
- 8GB+ RAM
- 20GB+ disk space
- Internet connection

### Software Requirements
- JDK 17+
- Node.js 18+
- Android SDK (API 34+)
- Gradle 8.0+ (via wrapper)

## Security Best Practices

1. **Never commit keystores or passwords**
   - Add to `.gitignore`
   - Use environment variables
   - Store in secure vault

2. **Use different keystores for debug/release**
   - Debug: Auto-generated
   - Release: Production keystore

3. **Enable ProGuard/R8 for release**
   - Code obfuscation
   - Size optimization
   - Already configured in build.gradle

4. **Verify APK signatures**
   ```bash
   apksigner verify --print-certs releases/wolf-logic-latest.apk
   ```

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](../LICENSE) for details.

---

**Built with ❤️ by Complex Simplicity Media**
