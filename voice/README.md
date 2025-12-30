# Piper Text-to-Speech Voice Server

High-quality, local text-to-speech server for voice AI agents. Powers natural-sounding voice synthesis for calling, interviews, and agent communication.

## Deployment Status

✅ **DEPLOYED AND OPERATIONAL**

- Model: **en_US-ljspeech-high** (109 MB)
- Server: Running on **http://localhost:5050**
- Quality: 22.05 kHz, 16-bit mono PCM audio
- Status: All endpoints tested and verified

## Quick Start

### Start the Server

```bash
source ~/anaconda3/bin/activate messiah
cd /mnt/Wolf-code/Wolf-Ai-Enterptises/voice
python piper_server.py
```

Server will be available at: `http://localhost:5050`

### Test the Server

```bash
# Health check
curl http://localhost:5050/health

# Synthesize text
curl -X POST http://localhost:5050/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "This is an AI agent calling on behalf of the Wolf. When can we schedule an interview?"}'

# Get available models
curl http://localhost:5050/models

# Get version info
curl http://localhost:5050/version
```

### Run Full Test Suite

```bash
source ~/anaconda3/bin/activate messiah
python /mnt/Wolf-code/Wolf-Ai-Enterptises/voice/test_client.py
```

## API Endpoints

### GET /health

Health check endpoint. Returns server status and model status.

**Response:**
```json
{
  "status": "healthy",
  "model": "en_US-ljspeech-high",
  "voice_loaded": true
}
```

### POST /synthesize

Synthesize text to speech. Returns WAV audio file (16-bit PCM, 22050 Hz mono).

**Request:**
```json
{
  "text": "Text to synthesize",
  "speaker_id": 0,           // Optional (default: null, use primary speaker)
  "length_scale": 1.0,       // Optional (1.0 = normal speed, <1.0 = faster, >1.0 = slower)
  "noise_scale": 0.667,      // Optional (controls variation in output, 0.0-1.0)
  "volume": 1.0              // Optional (volume multiplier, default: 1.0)
}
```

**Response:** Binary WAV audio file

**Example:**
```bash
curl -X POST http://localhost:5050/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello world! This is an AI agent.",
    "length_scale": 0.9,
    "volume": 1.0
  }' \
  --output speech.wav
```

### GET /models

Get information about available models.

**Response:**
```json
{
  "models": [
    {
      "name": "en_US-ljspeech-high",
      "language": "en_US",
      "quality": "high",
      "sample_rate": 22050,
      "speakers": 1,
      "loaded": true
    }
  ]
}
```

### GET /version

Get server and Piper version information.

**Response:**
```json
{
  "server": "piper-voice-server",
  "version": "1.0.0",
  "piper_version": "unknown",
  "model": "en_US-ljspeech-high"
}
```

## Installation

### Prerequisites

- Python 3.12+ (Messiah conda environment)
- Debian 13+ (or equivalent Linux)

### Setup

1. **Activate environment:**
   ```bash
   source ~/anaconda3/bin/activate messiah
   ```

2. **Install dependencies:**
   ```bash
   pip install piper-tts flask requests
   ```

3. **Download model:**
   The model is pre-downloaded to: `/mnt/Wolf-code/Wolf-Ai-Enterptises/voice/models/`
   - `en_US-ljspeech-high.onnx` (109 MB)
   - `en_US-ljspeech-high.onnx.json` (5 KB)

4. **Start server:**
   ```bash
   python /mnt/Wolf-code/Wolf-Ai-Enterptises/voice/piper_server.py
   ```

## Systemd Service Setup (requires sudo)

To run the server as a system service:

1. Copy the service file:
   ```bash
   sudo cp /mnt/Wolf-code/Wolf-Ai-Enterptises/voice/piper-voice-server.service /etc/systemd/system/
   ```

2. Enable and start:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable piper-voice-server
   sudo systemctl start piper-voice-server
   ```

3. Check status:
   ```bash
   sudo systemctl status piper-voice-server
   journalctl -u piper-voice-server -f
   ```

## Model Information

### en_US-ljspeech-high

- **Quality:** High (22.05 kHz, 16-bit PCM)
- **Size:** 109 MB
- **Parameters:** 28-32M
- **Speaker:** Female (LJSpeech dataset)
- **Language:** English (US)
- **Speed:** ~1-2 seconds per sentence (depending on length)

## Architecture

```
/mnt/Wolf-code/Wolf-Ai-Enterptises/voice/
├── piper_server.py              # Main Flask server
├── test_client.py               # Test suite
├── piper-voice-server.service   # Systemd service file
├── models/
│   ├── en_US-ljspeech-high.onnx        # ONNX model (109 MB)
│   └── en_US-ljspeech-high.onnx.json   # Config file
└── README.md                    # This file
```

## Integration Examples

### Python Client

```python
import requests

def synthesize(text, speed=1.0, volume=1.0):
    response = requests.post(
        'http://localhost:5050/synthesize',
        json={
            'text': text,
            'length_scale': speed,
            'volume': volume
        },
        timeout=30
    )

    if response.status_code == 200:
        return response.content  # Binary WAV data
    else:
        raise Exception(response.text)

# Usage
audio_data = synthesize("Call scheduled for tomorrow at 2 PM")
with open('call.wav', 'wb') as f:
    f.write(audio_data)
```

### JavaScript/Node.js

```javascript
async function synthesize(text) {
    const response = await fetch('http://localhost:5050/synthesize', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({text: text})
    });

    if (response.ok) {
        const blob = await response.blob();
        return new Audio(URL.createObjectURL(blob));
    }
    throw new Error(await response.text());
}

// Usage
const audio = await synthesize("Interview confirmed");
audio.play();
```

## Performance Characteristics

- **Synthesis Time:** ~0.5-2s per sentence
- **Response Latency:** 100-500ms average
- **Memory Usage:** ~500 MB (model loaded)
- **CPU Usage:** Single-threaded, ~80% during synthesis
- **Concurrent Requests:** Flask default (single-threaded, but thread-safe for Piper)

## Troubleshooting

### Port 5050 already in use

```bash
# Find process using port 5050
lsof -i :5050

# Kill the process
pkill -f piper_server
```

### ONNX Runtime Errors

Ensure ONNX Runtime is properly installed:
```bash
source ~/anaconda3/bin/activate messiah
pip install --upgrade onnxruntime
```

### Model Not Found

Verify model files exist:
```bash
ls -lh /mnt/Wolf-code/Wolf-Ai-Enterptises/voice/models/
```

Should show:
- `en_US-ljspeech-high.onnx` (109 MB)
- `en_US-ljspeech-high.onnx.json` (5 KB)

## Test Results

All endpoints tested and passing:

```
Health............................................ PASS
Models............................................ PASS
Version........................................... PASS
Synthesis......................................... PASS
Synthesis with params............................. PASS

All tests passed!
```

Generated test audio:
- **test_1.wav:** "This is an AI agent calling on behalf of the Wolf..." (204 KB)
- **test_2.wav:** "Hello there! How are you today?" (74 KB)
- **test_3.wav:** "The quick brown fox jumps over the lazy dog." (151 KB)

All files verified as valid 16-bit PCM WAVE audio at 22050 Hz mono.

## Development & Customization

### Available Parameters

- **length_scale:** Adjust phoneme duration (0.5 = 2x faster, 2.0 = 2x slower)
- **noise_scale:** Control output variation (0.0 = deterministic, 1.0 = maximum variation)
- **volume:** Adjust output volume level (0.5 = 50%, 1.0 = 100%, 2.0 = 200%)

### Additional Piper Models

To use different English models, download from Hugging Face:
https://huggingface.co/rhasspy/piper-voices

Other available quality levels:
- `en_US-ljspeech-low` (8 kHz, fastest)
- `en_US-ljspeech-medium` (16 kHz, balanced)
- `en_US-ljspeech-high` (22 kHz, highest quality) **← Current**

## Sources

- [OHF-Voice Piper Repository](https://github.com/OHF-Voice/piper1-gpl)
- [Hugging Face Piper Voices](https://huggingface.co/rhasspy/piper-voices)
- [Original Rhasspy Piper](https://github.com/rhasspy/piper)

## License

Piper is licensed under GPLv3. This server wrapper follows the same license.

## Status

- **Last Updated:** 2025-12-02
- **Deployed:** ✅ Yes
- **Running:** ✅ Yes (localhost:5050)
- **Tests:** ✅ All Passing
