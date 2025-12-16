# Piper Voice Server - Quick Start Guide

## Start the Server

```bash
source ~/anaconda3/bin/activate messiah
cd /mnt/Wolf-code/Wolf-Ai-Enterptises/voice
python piper_server.py
```

Server will be ready at: **http://localhost:5050**

## Test with cURL

```bash
# Health check
curl http://localhost:5050/health

# Synthesize speech
curl -X POST http://localhost:5050/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "This is an AI agent calling on behalf of the Wolf. When can we schedule an interview?"}' \
  --output speech.wav

# Play the audio
ffplay speech.wav  # or: aplay speech.wav / paplay speech.wav
```

## Python Quick Integration

```python
import requests

# Synthesize speech
response = requests.post(
    'http://localhost:5050/synthesize',
    json={'text': 'Hello! This is a test message.'}
)

# Save as WAV file
with open('output.wav', 'wb') as f:
    f.write(response.content)

print(f"Generated {len(response.content)} bytes of audio")
```

## Available Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Check server status |
| `/synthesize` | POST | Convert text to speech (returns WAV file) |
| `/models` | GET | List available models |
| `/version` | GET | Get server version info |

## Synthesis Parameters

```json
{
  "text": "Required: text to synthesize",
  "speaker_id": null,        "Optional: speaker ID (default: null)",
  "length_scale": 1.0,       "Optional: speed (0.8=faster, 1.2=slower)",
  "noise_scale": 0.667,      "Optional: variation (0.0=uniform, 1.0=max)",
  "volume": 1.0              "Optional: volume (1.0=normal)"
}
```

## Examples

### Normal Speed
```bash
curl -X POST http://localhost:5050/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Call scheduled for tomorrow at two PM"}' \
  --output call.wav
```

### Faster Speech
```bash
curl -X POST http://localhost:5050/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Call scheduled for tomorrow at two PM", "length_scale": 0.8}' \
  --output call_fast.wav
```

### Slower Speech
```bash
curl -X POST http://localhost:5050/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Call scheduled for tomorrow at two PM", "length_scale": 1.3}' \
  --output call_slow.wav
```

### Quieter Audio
```bash
curl -X POST http://localhost:5050/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Call scheduled for tomorrow at two PM", "volume": 0.7}' \
  --output call_quiet.wav
```

## Run Full Test Suite

```bash
source ~/anaconda3/bin/activate messiah
python /mnt/Wolf-code/Wolf-Ai-Enterptises/voice/test_client.py
```

## Stop the Server

Press `Ctrl+C` while the server is running, or:

```bash
pkill -f piper_server.py
```

## Documentation

- **Full README:** `/mnt/Wolf-code/Wolf-Ai-Enterptises/voice/README.md`
- **Deployment Report:** `/mnt/Wolf-code/Wolf-Ai-Enterptises/voice/DEPLOYMENT_REPORT.md`
- **Test Suite:** `/mnt/Wolf-code/Wolf-Ai-Enterptises/voice/test_client.py`

## Troubleshooting

**Port 5050 already in use?**
```bash
pkill -f piper_server.py
sleep 2
# Restart server
```

**Model not found?**
```bash
ls -lh /mnt/Wolf-code/Wolf-Ai-Enterptises/voice/models/
# Should show: en_US-ljspeech-high.onnx (109 MB)
```

**Server won't start?**
```bash
source ~/anaconda3/bin/activate messiah
python /mnt/Wolf-code/Wolf-Ai-Enterptises/voice/piper_server.py
# Check error messages
```

---
**Ready to use!** Start the server and synthesize speech.
