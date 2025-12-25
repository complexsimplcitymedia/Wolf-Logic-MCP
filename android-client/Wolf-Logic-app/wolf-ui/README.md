# WOLF LCD Dashboard - Virtual Display Overhaul

## 🎯 Complete Virtual LCD Dashboard with Qdrant Core Aesthetic

Your custom dashboard is ready! This is a complete overhaul with virtual LCD panels, Qdrant-inspired design, and real-time GPU metrics.

## 🚀 Installation & Deployment

### 1. Install System Service

```bash
# Copy service file to systemd
sudo cp wolf-ui.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable on boot
sudo systemctl enable wolf-ui.service

# Start the service
sudo systemctl start wolf-ui.service

# Check status
sudo systemctl status wolf-ui.service
```

### 2. Or Run Manually (for testing)

```bash
# From the project root
python3 wolf-ui/server.py 3000

# Or specify custom port
python3 wolf-ui/server.py 8080
```

### 3. Access Dashboard

Open in your browser:
```
http://localhost:3000
```

## 📊 Dashboard Features

### Virtual LCD Panels

1. **Memory Bank Panel**
   - Total memories count (from OpenMemory API)
   - Vector embeddings count (from Qdrant)
   - Graph relations count (from Neo4j)
   - Applications count
   - Real-time sync progress bar

2. **AMD GPU Metrics Panel**
   - GPU load percentage
   - Temperature with warning colors
   - VRAM usage
   - Power draw
   - Live 8-bar histogram graph
   - Auto-updates every second

3. **Agent Status Panel**
   - Embedder agent status
   - Categorization agent status
   - Quinn 2.5 status
   - Quinn 3.0 status
   - Queue size counter
   - LED indicators (green = online, amber = warning, red = offline)

4. **LM Studio Panel**
   - Chat model display (Amethyst 13B Mistral)
   - Embedding model display (Qwen3 4B)
   - Endpoint status
   - Connection indicator

5. **Control Center Panel**
   - Init System button
   - Start Embedder button
   - Search Memories button
   - Clear Cache button
   - Refresh All button
   - View Logs button

6. **Activity Log Panel**
   - Real-time operation logs
   - Color-coded messages (green = success, red = error, amber = warning)
   - Auto-scrolling
   - Timestamp for each entry

### Header Bar
- WOLF MCP logo with Qdrant-inspired gradient
- Service status indicators (Backend, OpenMemory, Qdrant, Neo4j)
- LED indicators for each service

### Footer Bar
- System uptime counter
- Last update timestamp
- CPU load percentage

## 🎨 Design Elements

### Qdrant Core Aesthetic
- Color palette inspired by Qdrant's brand gradient (#24386c → #7289da)
- LCD green primary display color (#00ff41)
- Dark background with subtle scanline animation
- Beveled panel borders with inset shadows
- Glowing LED indicators with pulse animations

### Virtual LCD Features
- Monospace "Courier New" font for authentic LCD look
- Glowing text shadows on active elements
- Progress bars with gradient fills
- Bar graph visualizations
- Hover effects with border glow
- Responsive grid layout (3-column → 2-column → 1-column)

## 🔌 API Integration

### Wolf Backend (Port 4500)
- `/api/wolf/init` - Initialize system
- `/api/wolf/status` - Get agent status
- `/api/wolf/search` - Search memories
- `/api/wolf/clear` - Clear cache
- `/api/wolf/gpu-stats` - GPU metrics (NEW!)

### OpenMemory API (Port 8765)
- `/api/v1/stats` - Memory statistics
- Authenticated with X-API-Key header

### Qdrant (Port 6333)
- `/collections` - Vector collections
- Points count for each collection

### LM Studio (Port 1234)
- `/v1/models` - List loaded models

## 🖥️ GPU Metrics Integration

### Supported Methods (in priority order):

1. **LACT (Linux AMD Control Tool)** - Best option
   ```bash
   # Install LACT
   yay -S lact
   
   # Enable daemon
   sudo systemctl enable --now lactd
   ```

2. **Radeontop** - Fallback option
   ```bash
   sudo apt install radeontop
   # or
   yay -S radeontop
   ```

3. **Sysfs** - Direct kernel interface
   - Reads from `/sys/class/drm/card*/device/hwmon/`
   - No installation needed

4. **Mock Data** - Testing/demo
   - Generated based on CPU usage
   - Realistic values for demonstration

## 📁 Project Structure

```
wolf-ui/
├── index.html              # Main dashboard HTML
├── server.py              # Python HTTP server with GPU endpoint
├── static/
│   ├── css/
│   │   └── lcd-dashboard.css   # Virtual LCD styling
│   └── js/
│       └── dashboard.js        # Real-time API integration
└── README.md              # This file

wolf-ui.service            # Systemd service file
wolf_gpu_metrics.py        # GPU metrics module for Wolf Backend
```

## 🔧 Configuration

### Update API Endpoints

Edit `wolf-ui/static/js/dashboard.js`:

```javascript
this.config = {
    wolfBackend: 'http://localhost:4500',   // Wolf Backend API
    openMemory: 'http://localhost:8765',    // OpenMemory API
    qdrant: 'http://localhost:6333',        // Qdrant
    neo4j: 'http://localhost:7474',         // Neo4j
    lmStudio: 'http://localhost:1234',      // LM Studio
    updateInterval: 2000,                   // 2 seconds
    gpuUpdateInterval: 1000,                // 1 second
};
```

### Change Port

```bash
# In wolf-ui.service
ExecStart=/usr/bin/python3 /path/to/wolf-ui/server.py 3000
#                                                       ^^^^ change port

# Or via environment variable
WOLF_UI_PORT=8080 python3 wolf-ui/server.py
```

## 🔍 Troubleshooting

### Dashboard Not Loading
```bash
# Check service status
sudo systemctl status wolf-ui.service

# View logs
sudo journalctl -u wolf-ui.service -f

# Check port availability
sudo netstat -tulpn | grep 3000
```

### No GPU Metrics
```bash
# Install LACT for best results
yay -S lact
sudo systemctl enable --now lactd

# Test LACT CLI
lact info --json

# Check permissions
sudo usermod -aG video $USER
```

### Services Not Showing Online
```bash
# Verify Wolf Backend is running
curl http://localhost:4500/health

# Verify OpenMemory API
curl -H "X-API-Key: wolf-permanent-api-key-2024-never-expires" \
  http://localhost:8765/api/v1/stats

# Check Qdrant
curl http://localhost:6333/collections

# Restart Wolf Backend with GPU support
sudo systemctl restart wolf-logic-flask.service
```

## 🎯 Next Steps

1. **Start the Dashboard**
   ```bash
   sudo systemctl start wolf-ui.service
   ```

2. **Open Browser**
   ```
   http://localhost:3000
   ```

3. **Start Processing Memories**
   - Click "INIT SYSTEM" button
   - Click "START EMBEDDER" button
   - Watch the sync progress in real-time!

4. **Monitor Your System**
   - GPU metrics update every second
   - Memory stats update every 2 seconds
   - Agent status shows processing queue

## 🌟 Features Highlights

✅ Pure Python HTTP server (no Docker, no npm)
✅ Systemd service with auto-restart
✅ Virtual LCD aesthetic with Qdrant branding
✅ Real-time GPU metrics (AMD LACT integration)
✅ Live memory statistics from all sources
✅ Agent status monitoring
✅ Interactive control buttons
✅ Activity logging
✅ Responsive design
✅ Animated scanlines and glowing effects
✅ Color-coded status indicators

---

**Your 6-month journey is about to pay off!** 🐺

This dashboard gives you complete visibility into your memory processing pipeline with a beautiful virtual LCD interface inspired by Qdrant's core aesthetic.
