# Android Client Setup Guide

## Prerequisites

- Android device with Android 8.0+ (API 26+)
- ARM64 architecture (most modern devices)
- Tailscale installed and connected to Wolf Logic network
- Access to 100.110.82.181

## Step 1: Install Tailscale

1. Install Tailscale from Google Play Store
2. Open Tailscale and sign in with Wolf Logic account
3. Enable VPN when prompted
4. Verify connection:
   - Open terminal app (Termux recommended)
   - Run: `ping 100.110.82.181`
   - Should get responses

## Step 2: Install Wolf Logic APK

### Method A: ADB Install (Recommended)

Connect device to computer with ADB:

```bash
# On computer with adb
cd /path/to/Wolf-Logic-MCP/android-client/wolflogic-apk

# Install all split APKs
adb install-multiple \
  base.apk \
  split_config.arm64_v8a.apk \
  split_config.en.apk \
  split_config.xxhdpi.apk
```

### Method B: Direct Install

1. Copy APK files to device
2. Enable "Install from unknown sources" in Settings
3. Open file manager
4. Navigate to APK location
5. Tap `base.apk` to install
6. Install split APKs if prompted

## Step 3: Configure OAuth

1. Open Wolf Logic app
2. Tap "Login"
3. You'll be redirected to Authentik (100.110.82.181:9001)
4. Enter Wolf Logic credentials
5. Grant permissions when prompted
6. App will receive OAuth token automatically

### Manual Token Configuration (Development)

If OAuth flow fails, configure manually:

```kotlin
// In app settings or SharedPreferences
val prefs = getSharedPreferences("wolf_logic", MODE_PRIVATE)
prefs.edit().putString("oauth_token", "your-token-here").apply()
```

## Step 4: Verify Connection

1. Open Wolf Logic app
2. Go to Settings > Connection Test
3. Verify:
   - Hub connectivity: GREEN
   - OAuth status: Authenticated
   - MCP Intake: Available

Or test via Termux:

```bash
# Test MCP endpoint
curl -X GET http://100.110.82.181:8002/health

# Expected response:
# {"status":"healthy","timestamp":"..."}
```

## Step 5: Configure Sync Settings

In app Settings:

| Setting | Recommended Value | Purpose |
|---------|-------------------|---------|
| Auto-sync | ON | Sync pending items when online |
| Sync interval | 15 minutes | WorkManager periodic sync |
| Buffer size | 500 chars | Batch submissions |
| Flush delay | 5 seconds | Wait before sending buffer |

## Termux Setup (Advanced Users)

For developers and power users, Termux provides command-line access.

### Install Termux

1. Install Termux from F-Droid (NOT Play Store - that version is outdated)
2. Open Termux
3. Run: `termux-setup-storage` (grants file access)

### Setup Development Environment

```bash
# Update packages
pkg update && pkg upgrade -y

# Install essentials
pkg install python git openssh curl -y

# Install Python packages
pip install requests pydantic

# Clone Wolf Logic MCP
git clone https://github.com/wolflogic/Wolf-Logic-MCP
cd Wolf-Logic-MCP/android-client
```

### Run Mobile GUI

```bash
cd ~/Wolf-Logic-MCP/android-client
python mobile_wolf_gui.py
```

### Run Termux Control Script

```bash
python termux_gui_control.py
```

## Directory Structure

After setup, your android-client directory contains:

```
android-client/
├── MEMORY_LAYER.md      # Memory layer integration docs
├── SETUP.md             # This file
├── mobile_wolf_gui.py   # Termux GUI script
├── termux_gui_control.py # Termux control interface
├── Wolf-Logic-app/      # Full Android application source
│   ├── backend.py       # FastAPI backend
│   ├── control_app.py   # UI controller
│   └── wolf-ui/         # React Native UI
└── wolflogic-apk/       # Compiled APK files
    ├── base.apk
    ├── split_config.arm64_v8a.apk
    ├── split_config.en.apk
    └── split_config.xxhdpi.apk
```

## Quick Test: Submit a Memory

After setup, test the full flow:

### Using the App

1. Open Wolf Logic app
2. Tap "New Note"
3. Type: "Test memory from Android client"
4. Tap "Submit"
5. Wait for confirmation toast

### Using Termux

```bash
curl -X POST http://100.110.82.181:8002/intake/stream \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Test from Termux CLI",
    "metadata": {
      "source": "termux",
      "device": "'"$(getprop ro.product.model)"'"
    }
  }'
```

### Verify on 181

SSH to 181 and check:

```bash
# Check client-dumps for your submission
ls -la /data/client-dumps/ | head -5

# Check if memory was processed
PGPASSWORD=wolflogic2024 psql -h localhost -p 5433 -U wolf -d wolf_logic \
  -c "SELECT content, created_at FROM memories WHERE content ILIKE '%Test%' ORDER BY created_at DESC LIMIT 5;"
```

## Troubleshooting

### App won't install

```bash
# Check architecture
adb shell getprop ro.product.cpu.abi
# Should be: arm64-v8a

# Uninstall old version first
adb uninstall com.wolflogic.mcp
```

### Cannot reach 100.110.82.181

1. Open Tailscale app
2. Check connection status (should show "Connected")
3. Toggle VPN off and on
4. Check if 181 is in your Tailscale network

### OAuth callback fails

1. Check AndroidManifest.xml has correct intent filter:
   ```xml
   <intent-filter>
       <action android:name="android.intent.action.VIEW" />
       <category android:name="android.intent.category.DEFAULT" />
       <category android:name="android.intent.category.BROWSABLE" />
       <data android:scheme="wolflogic" android:host="oauth" android:path="/callback" />
   </intent-filter>
   ```
2. Verify redirect URI is registered in Authentik

### Submissions fail silently

1. Check network connectivity
2. Check OAuth token isn't expired
3. Look at app logs: `adb logcat | grep WolfLogic`

## Security Notes

1. **OAuth tokens** are stored in Android Keystore (encrypted)
2. **No credentials** are stored in plaintext
3. **TLS** should be enabled for production (use Caddy on 181)
4. **Tailscale** provides network-layer encryption

## Next Steps

- Read [MEMORY_LAYER.md](./MEMORY_LAYER.md) for architecture details
- Read [../android-client.md](../android-client.md) for API reference
- Check [../macos-client.md](../macos-client.md) if also setting up macOS
