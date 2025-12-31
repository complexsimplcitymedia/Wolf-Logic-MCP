# CI/CD Pipeline Documentation

## Overview

Wolf Logic MCP uses GitHub Actions for continuous integration and deployment. The pipelines automate building, testing, security scanning, and releasing desktop and Android applications.

## Workflows

### 1. Build Desktop Apps (`.github/workflows/build-desktop.yml`)

Builds cross-platform desktop applications for Windows, macOS, and Linux.

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main`
- Version tags (e.g., `v1.0.0`)
- Manual dispatch

**Jobs:**
- **build-desktop**: Builds for all three platforms in parallel
  - Linux: AppImage, .deb, .rpm
  - macOS: .dmg, .zip
  - Windows: .exe (installer and portable)
- **create-release**: Creates GitHub release on version tags
- **notify**: Reports build status

**Artifacts:**
- Retained for 30 days
- Uploaded to GitHub Releases on tags

**Configuration:**

The workflow requires these secrets for code signing (optional):

```
# macOS code signing
MAC_CERTIFICATE          # Base64-encoded .p12 certificate
MAC_CERTIFICATE_PASSWORD # Certificate password
APPLE_ID                 # Apple ID email
APPLE_ID_PASSWORD        # App-specific password

# Windows code signing
WIN_CERTIFICATE          # Base64-encoded .pfx certificate
WIN_CERTIFICATE_PASSWORD # Certificate password
```

### 2. Build Android App (`.github/workflows/build-android.yml`)

Builds Android APK and AAB packages.

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main`
- Version tags (e.g., `v1.0.0`)
- Manual dispatch

**Jobs:**
- **build-android**: Builds APK (debug or release) and AAB
- **create-release**: Creates GitHub release on version tags
- **notify**: Reports build status

**Artifacts:**
- Debug builds: 30 days retention
- Release builds: 90 days retention
- Uploaded to GitHub Releases on tags

**Configuration:**

The workflow requires these secrets for release signing:

```
ANDROID_KEYSTORE_BASE64  # Base64-encoded keystore file
ANDROID_KEY_ALIAS        # Key alias (default: wolf-logic)
ANDROID_STORE_PASSWORD   # Keystore password
ANDROID_KEY_PASSWORD     # Key password
```

**Setting up keystore:**

```bash
# 1. Generate keystore
keytool -genkey -v \
  -keystore wolf-logic-release.keystore \
  -alias wolf-logic \
  -keyalg RSA \
  -keysize 2048 \
  -validity 10000

# 2. Encode to base64
base64 wolf-logic-release.keystore | tr -d '\n' > keystore.base64

# 3. Add to GitHub Secrets
# Go to: Settings > Secrets and variables > Actions > New repository secret
# Name: ANDROID_KEYSTORE_BASE64
# Value: Contents of keystore.base64
```

### 3. Security & Testing (`.github/workflows/security-testing.yml`)

Comprehensive security scanning and code quality checks.

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main`
- Weekly schedule (Sundays at midnight)
- Manual dispatch

**Jobs:**
- **codeql-analysis**: CodeQL security analysis for JavaScript, Python, TypeScript
- **dependency-scan**: npm audit and pip-audit for vulnerability scanning
- **secret-scan**: TruffleHog for secret detection
- **lint-code**: ESLint, flake8, pylint
- **test-scripts**: Bash syntax validation
- **docker-security**: Trivy vulnerability scanner for Docker configs
- **summary**: Aggregates all results

**Artifacts:**
- Security audit reports (JSON format)
- Retained for 90 days

## Release Process

### Automated Release

1. **Tag a version:**
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. **Workflows trigger automatically:**
   - Desktop builds for all platforms
   - Android APK and AAB builds
   - Security scans

3. **Release created:**
   - GitHub Release with all artifacts
   - Checksums generated
   - Release notes from tag message

### Manual Release

1. Go to: Actions > Build Desktop Apps (or Build Android App)
2. Click "Run workflow"
3. Select branch
4. Enter version number (optional)
5. Click "Run workflow"

## Secrets Management

### Required Secrets

| Secret | Used By | Purpose |
|--------|---------|---------|
| `ANDROID_KEYSTORE_BASE64` | build-android.yml | Android release signing |
| `ANDROID_KEY_ALIAS` | build-android.yml | Keystore key alias |
| `ANDROID_STORE_PASSWORD` | build-android.yml | Keystore password |
| `ANDROID_KEY_PASSWORD` | build-android.yml | Key password |
| `MAC_CERTIFICATE` | build-desktop.yml | macOS code signing |
| `MAC_CERTIFICATE_PASSWORD` | build-desktop.yml | macOS cert password |
| `APPLE_ID` | build-desktop.yml | Apple ID for notarization |
| `APPLE_ID_PASSWORD` | build-desktop.yml | App-specific password |
| `WIN_CERTIFICATE` | build-desktop.yml | Windows code signing |
| `WIN_CERTIFICATE_PASSWORD` | build-desktop.yml | Windows cert password |

### Adding Secrets

1. Go to: Repository > Settings > Secrets and variables > Actions
2. Click "New repository secret"
3. Enter name and value
4. Click "Add secret"

**Never commit secrets to the repository!**

## Build Matrix

### Desktop Builds

| Platform | Formats | Build Time | Size |
|----------|---------|------------|------|
| Linux | AppImage, .deb, .rpm | ~5 min | ~80 MB |
| macOS | .dmg, .zip | ~8 min | ~120 MB |
| Windows | .exe (installer), .exe (portable) | ~6 min | ~90 MB |

### Android Builds

| Type | Format | Build Time | Size |
|------|--------|------------|------|
| Debug | APK | ~3 min | ~50 MB |
| Release | APK, AAB | ~5 min | ~30 MB |

## Caching

### Node.js Dependencies

```yaml
- uses: actions/setup-node@v4
  with:
    cache: 'npm'
    cache-dependency-path: '**/package-lock.json'
```

Caches `node_modules` based on `package-lock.json` hash.

### Gradle Dependencies

Gradle wrapper automatically caches dependencies between builds.

## Troubleshooting

### Build Fails on Desktop

**Issue:** Electron builder fails
```
Error: Cannot find module 'electron'
```

**Solution:** Ensure dependencies are installed:
```yaml
- run: npm ci
  working-directory: desktop-client
```

### Android Build Fails

**Issue:** Gradle daemon not found
```
Error: Could not find or load main class org.gradle.wrapper.GradleWrapperMain
```

**Solution:** Make gradlew executable:
```yaml
- run: |
    chmod +x gradlew
    ./gradlew assembleRelease
  working-directory: md-app/android
```

### Secret Scan False Positives

**Issue:** TruffleHog flags test data as secrets

**Solution:** Add to `.trufflehog-ignore`:
```
# Test data patterns
test/fixtures/**
docs/examples/**
```

### CodeQL Analysis Timeout

**Issue:** Analysis takes too long

**Solution:** Limit languages:
```yaml
strategy:
  matrix:
    language: ['javascript', 'typescript']  # Remove 'python' if needed
```

## Performance Optimization

### Parallel Builds

Desktop builds run in parallel across three runners:
- Saves ~10 minutes per build
- Cost: 3x runner minutes

### Conditional Jobs

Release jobs only run on tags:
```yaml
if: startsWith(github.ref, 'refs/tags/v')
```

### Artifact Retention

- Debug builds: 30 days
- Release builds: 90 days
- Security reports: 90 days

## Monitoring

### Build Status

Check workflow status:
```bash
gh run list --workflow=build-desktop.yml
gh run list --workflow=build-android.yml
gh run list --workflow=security-testing.yml
```

### Logs

View logs:
```bash
gh run view <run-id> --log
```

### Badges

Add to README.md:
```markdown
![Desktop Build](https://github.com/complexsimplcitymedia/Wolf-Logic-MCP/workflows/Build%20Desktop%20Apps/badge.svg)
![Android Build](https://github.com/complexsimplcitymedia/Wolf-Logic-MCP/workflows/Build%20Android%20App/badge.svg)
![Security](https://github.com/complexsimplcitymedia/Wolf-Logic-MCP/workflows/Security%20%26%20Testing/badge.svg)
```

## Best Practices

1. **Test locally first:**
   ```bash
   # Desktop
   cd desktop-client
   npm run build
   npm run package
   
   # Android
   cd android-package/scripts
   ./build-apk.sh --debug
   ```

2. **Use semantic versioning:**
   - `v1.0.0` - Major release
   - `v1.1.0` - Minor (new features)
   - `v1.0.1` - Patch (bug fixes)

3. **Tag releases consistently:**
   ```bash
   git tag -a v1.0.0 -m "Release 1.0.0: Initial public release"
   git push origin v1.0.0
   ```

4. **Review security scans:**
   - Check CodeQL alerts weekly
   - Fix high-severity vulnerabilities immediately
   - Update dependencies regularly

5. **Keep secrets secure:**
   - Rotate passwords annually
   - Use different keystores for dev/prod
   - Back up keystores securely

## Future Improvements

- [ ] Add integration tests
- [ ] Implement staged rollouts
- [ ] Add performance benchmarks
- [ ] Automate changelog generation
- [ ] Add rollback automation
- [ ] Implement blue-green deployments for server
- [ ] Add smoke tests post-deployment
- [ ] Integrate with TestFlight (iOS) and Google Play Internal Testing

## Support

For CI/CD issues:
1. Check workflow logs in GitHub Actions
2. Review this documentation
3. Open an issue with logs attached
4. Tag with `ci-cd` label

---

**Last Updated:** 2025-01-01
**Maintained By:** Complex Simplicity Media
