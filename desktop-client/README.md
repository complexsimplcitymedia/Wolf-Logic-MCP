# Wolf Logic Desktop Client

Cross-platform desktop application for Wolf Logic Memory & Context Protocol system.

## Features

- 🖥️ Native desktop experience (Windows, macOS, Linux)
- 🔒 Secure OAuth 2.0 authentication via Authentik
- 💾 Local configuration storage
- 🔄 Auto-update functionality
- 🎨 Modern, intuitive UI
- 📦 Dependency management helper

## Installation

### Download Pre-built Binaries

Download the latest release for your platform:

- **Windows**: `Wolf-Logic-MCP-Setup-1.0.0.exe` (Installer) or `Wolf-Logic-MCP-1.0.0-portable.exe` (Portable)
- **macOS**: `Wolf-Logic-MCP-1.0.0.dmg` or `Wolf-Logic-MCP-1.0.0-mac.zip`
- **Linux**: `Wolf-Logic-MCP-1.0.0.AppImage`, `wolf-logic-mcp_1.0.0_amd64.deb`, or `wolf-logic-mcp-1.0.0.x86_64.rpm`

### Build from Source

```bash
# Clone the repository
git clone https://github.com/complexsimplcitymedia/Wolf-Logic-MCP.git
cd Wolf-Logic-MCP/desktop-client

# Install dependencies
npm install

# Build TypeScript
npm run build

# Run in development mode
npm run dev

# Package for production
npm run package

# Build for specific platform
npm run package:win    # Windows
npm run package:mac    # macOS
npm run package:linux  # Linux

# Build for all platforms
npm run package:all
```

## Configuration

On first launch, configure your server connection:

1. Open **Settings** from the sidebar
2. Enter your **Server URL** (e.g., `http://100.110.82.181:8002`)
3. Enter your **Authentik URL** (e.g., `http://100.110.82.181:9001`)
4. Enter your **API Key** (obtained from registration)
5. Enter your **Username**
6. Click **Save Settings**

## Dependencies

Wolf Logic Desktop requires these dependencies on your system:

### Required

- **Python 3.12+**: Backend processing
- **Anaconda/Miniconda**: Environment management (Messiah env)
- **Ollama**: Local LLM runtime
- **PostgreSQL Client**: Database connectivity
- **Tailscale** (recommended): VPN for secure server access

### Installation Helpers

The app includes dependency checking and guided installation:

1. Go to **Dependencies** in the sidebar
2. Click **Check All** to verify installed dependencies
3. Click **Install Missing** for guided installation

### Manual Installation

#### Windows

```powershell
# Install Python
winget install Python.Python.3.12

# Install Anaconda
winget install Anaconda.Miniconda3

# Install Ollama
winget install Ollama.Ollama

# Install PostgreSQL client
winget install PostgreSQL.PostgreSQL

# Install Tailscale
winget install Tailscale.Tailscale
```

#### macOS

```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python@3.12
brew install --cask miniconda
brew install ollama
brew install postgresql@16
brew install --cask tailscale
```

#### Linux (Debian/Ubuntu)

```bash
# Python
sudo apt update
sudo apt install python3.12 python3-pip

# Miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh

# Ollama
curl -fsSL https://ollama.com/install.sh | sh

# PostgreSQL client
sudo apt install postgresql-client-16

# Tailscale
curl -fsSL https://tailscale.com/install.sh | sh
```

## Development

### Project Structure

```
desktop-client/
├── src/
│   ├── main.ts       # Main process (Electron)
│   └── preload.ts    # Preload script (context bridge)
├── renderer/
│   └── index.html    # UI (HTML/CSS/JS)
├── assets/
│   ├── icon.png      # App icon (PNG)
│   ├── icon.ico      # Windows icon
│   └── icon.icns     # macOS icon
├── dist/             # Compiled TypeScript
├── release/          # Built packages
├── package.json      # Dependencies and build config
└── tsconfig.json     # TypeScript config
```

### Scripts

- `npm run dev` - Run in development mode with hot reload
- `npm run build` - Compile TypeScript to JavaScript
- `npm run build:watch` - Watch mode for development
- `npm run package` - Build for current platform
- `npm run package:all` - Build for all platforms

### Adding Features

1. **Main Process** (`src/main.ts`): Electron main process, IPC handlers, system integration
2. **Preload** (`src/preload.ts`): Context bridge between main and renderer
3. **Renderer** (`renderer/index.html`): UI and client-side logic

## Troubleshooting

### App won't start

- **Windows**: Check if Windows Defender is blocking the app
- **macOS**: Right-click and select "Open" to bypass Gatekeeper
- **Linux**: Make the AppImage executable: `chmod +x Wolf-Logic-MCP-*.AppImage`

### Connection fails

1. Verify server URL is correct
2. Check Tailscale is connected (if using VPN)
3. Test server accessibility: `curl http://100.110.82.181:8002/health`
4. Check firewall settings

### Dependencies not found

1. Go to **Dependencies** page
2. Click **Check All**
3. Manually install missing dependencies
4. Restart the app

## Security

- API keys are stored encrypted in electron-store
- OAuth tokens use secure HTTP-only cookies
- All external links open in default browser
- Auto-update uses secure HTTPS channels

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](../LICENSE) for details.

## Support

- **Documentation**: https://github.com/complexsimplcitymedia/Wolf-Logic-MCP
- **Issues**: https://github.com/complexsimplcitymedia/Wolf-Logic-MCP/issues
- **Server Status**: Check your configured server's `/health` endpoint

---

**Built with ❤️ by Complex Simplicity Media**
