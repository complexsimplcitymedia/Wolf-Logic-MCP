# MCP Intake Pipeline - Complete Flow

## Overview
Multi-stage pipeline for processing client text streams with AI analysis before database insertion.

## Architecture

```
┌─────────────────────┐
│  Remote Clients     │
│  (OAuth secured)    │
└──────┬──────────────┘
       │ POST /intake/stream
       ▼
┌─────────────────────┐
│ MCP Intake Stream   │  Port 8002 (FastAPI)
│ (intake_api.py)     │  OAuth via Authentik
└──────┬──────────────┘
       │ writes JSON
       ▼
┌─────────────────────┐
│  /data/client-dumps │  Shared directory
│                     │  ├─ server-scripty (local transcripts)
│                     │  └─ MCP intake (remote streams)
└──────┬──────────────┘
       │ watches
       ▼
┌─────────────────────┐
│ Swarm Processor     │  (swarm_intake_processor.py)
│ - Keyword categorize│  Uses: keyword matching
│ - Sentiment analyze │  Uses: Mistral (Ollama)
└──────┬──────────────┘
       │ writes processed
       ▼
┌─────────────────────┐
│  /data/pgai-queue   │  Processed + analyzed
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│      pgai           │  PostgreSQL extension
│  - Embedding        │  Uses: qwen3-embedding:4b
│  - DB insertion     │  Table: memories
└─────────────────────┘
```

## Components

### 1. MCP Intake Stream API
**File:** `api/intake_api.py`
**Port:** 8002
**Auth:** OAuth via Authentik

**Endpoints:**
- `POST /intake/stream` - Submit text for processing
- `GET /intake/stats` - Queue statistics
- `GET /health` - Health check
- `GET /docs` - Swagger UI

**Client Example:**
```bash
curl -X POST http://100.110.82.181:8002/intake/stream \
  -H "Authorization: Bearer $OAUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your text content here",
    "metadata": {"source": "mobile_app", "version": "1.0"}
  }'
```

### 2. server-scripty
**File:** `scripty/server-scripty.py`
**Purpose:** Local Claude session transcription (verbatim)

**What it does:**
- Watches `~/.claude/projects/**/*.jsonl`
- Captures full exchanges (user + assistant)
- Writes verbatim JSON to `/data/client-dumps/`
- NO processing, NO summarization

### 3. Swarm Intake Processor
**File:** `writers/ingest/swarm_intake_processor.py`
**Purpose:** Keyword categorization + sentiment analysis

**Processing:**
1. **Keyword Categorization** (keyword matching)
   - Categories: development, infrastructure, project_management, documentation, personal, ai_model, system
   - Returns list of matching categories

2. **Sentiment Analysis** (Mistral via Ollama)
   - Score 1-5 (1=very negative, 5=very positive)
   - Includes reasoning

**Output format:**
```json
{
  "source_file": "user_20251224_120000_abc123.json",
  "username": "wolf",
  "text": "Original text...",
  "categories": ["development", "ai_model"],
  "sentiment": {
    "score": 4,
    "reasoning": "Constructive and solution-oriented",
    "model": "mistral:latest"
  },
  "namespace": "client_intake",
  "processed_timestamp": "2025-12-24T12:00:00"
}
```

### 4. pgai Vectorizer
**Component:** PostgreSQL extension (pgai)
**Purpose:** Embedding + database insertion

**Configuration:** (to be added to pgai setup)
- Watch directory: `/data/pgai-queue/`
- Embedding model: `qwen3-embedding:4b` (Ollama)
- Target table: `memories`
- Namespace: `client_intake` (from processed data)

## Directory Structure

```
/mnt/Wolf-code/Wolf-Ai-Enterptises/Wolf-Logic-MCP/data/
├── client-dumps/          # Raw intake (server-scripty + MCP API)
├── processed-intake/      # Archive of processed files
└── pgai-queue/           # Processed + analyzed → pgai picks up
```

## Deployment

### Install Services

```bash
cd /mnt/Wolf-code/Wolf-Ai-Enterptises/Wolf-Logic-MCP/server-configuration

# Copy systemd services
sudo cp systemd/mcp-intake-stream.service /etc/systemd/system/
sudo cp systemd/swarm-intake.service /etc/systemd/system/
sudo cp systemd/server-scripty.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable mcp-intake-stream.service
sudo systemctl enable swarm-intake.service
sudo systemctl enable server-scripty.service

# Start services
sudo systemctl start mcp-intake-stream.service
sudo systemctl start swarm-intake.service
sudo systemctl start server-scripty.service
```

### Verify Services

```bash
# Check status
sudo systemctl status mcp-intake-stream
sudo systemctl status swarm-intake
sudo systemctl status server-scripty

# Check logs
sudo journalctl -u mcp-intake-stream -f
sudo journalctl -u swarm-intake -f
sudo journalctl -u server-scripty -f

# Test MCP API
curl http://100.110.82.181:8002/health

# Check queue stats
curl http://100.110.82.181:8002/intake/stats
```

### Monitor Pipeline

```bash
# Watch client dumps (raw intake)
watch -n 1 'ls -lh /mnt/Wolf-code/Wolf-Ai-Enterptises/Wolf-Logic-MCP/data/client-dumps/'

# Watch pgai queue (processed)
watch -n 1 'ls -lh /mnt/Wolf-code/Wolf-Ai-Enterptises/Wolf-Logic-MCP/data/pgai-queue/'

# Swarm processor stats
python /mnt/Wolf-code/Wolf-Ai-Enterptises/Wolf-Logic-MCP/writers/ingest/swarm_intake_processor.py stats
```

## OAuth Setup (Authentik)

### Create Application
1. Navigate to Authentik admin: `http://100.110.82.181:9001`
2. Applications → Create
3. Configure:
   - Name: MCP Intake Stream
   - Slug: mcp-intake
   - Provider: OAuth2/OIDC
   - Client ID: mcp-intake
   - Client Secret: (generate)
   - Redirect URIs: Not required (API only)

### Get OAuth Token (for testing)
```bash
# Use Authentik's token endpoint
curl -X POST https://auth.complexsimplicityai.com/application/o/token/ \
  -d "grant_type=client_credentials" \
  -d "client_id=mcp-intake" \
  -d "client_secret=YOUR_SECRET"
```

## Data Flow Example

### 1. Client submits text
```json
POST /intake/stream
{
  "text": "Fixed the authentication bug in the API",
  "metadata": {"source": "mobile"}
}
```

### 2. MCP API writes to client-dumps
```json
{
  "username": "wolf",
  "user_email": "wolf@example.com",
  "text": "Fixed the authentication bug in the API",
  "metadata": {"source": "mobile"},
  "timestamp": "2025-12-24T12:00:00",
  "file_id": "abc123"
}
```

### 3. Swarm processor analyzes
- Categories: `["development", "infrastructure"]`
- Sentiment: `{"score": 4, "reasoning": "Constructive fix"}`

### 4. Writes to pgai-queue
```json
{
  "username": "wolf",
  "text": "Fixed the authentication bug in the API",
  "categories": ["development", "infrastructure"],
  "sentiment": {"score": 4, "reasoning": "Constructive fix"},
  "namespace": "client_intake",
  "processed_timestamp": "2025-12-24T12:00:05"
}
```

### 5. pgai embeds + inserts to DB
- Embedding: qwen3-embedding:4b generates 2560-dim vector
- Insert: `memories` table, namespace `client_intake`

## Troubleshooting

### MCP Intake API not starting
```bash
# Check port availability
sudo netstat -tulpn | grep 8002

# Check logs
sudo journalctl -u mcp-intake-stream -n 50

# Test manually
cd /mnt/Wolf-code/Wolf-Ai-Enterptises/Wolf-Logic-MCP/api
source ~/anaconda3/bin/activate messiah
python intake_api.py
```

### Swarm processor not processing files
```bash
# Check if watching
sudo journalctl -u swarm-intake -n 50

# Verify Ollama
curl http://localhost:11434/api/tags | jq '.models[] | .name' | grep mistral

# Test sentiment manually
curl http://localhost:11434/api/generate -d '{
  "model": "mistral:latest",
  "prompt": "Rate sentiment 1-5: This is great!",
  "stream": false
}'
```

### Files stuck in client-dumps
```bash
# Check swarm processor is running
sudo systemctl status swarm-intake

# Check file permissions
ls -la /mnt/Wolf-code/Wolf-Ai-Enterptises/Wolf-Logic-MCP/data/client-dumps/

# Manual test
python /mnt/Wolf-code/Wolf-Ai-Enterptises/Wolf-Logic-MCP/writers/ingest/swarm_intake_processor.py
```

### pgai not picking up files
```bash
# Check pgai vectorizer config
PGPASSWORD=wolflogic2024 psql -h 100.110.82.181 -p 5433 -U wolf -d wolf_logic \
  -c "SELECT * FROM ai.vectorizer_status;"

# Verify queue directory
ls -la /mnt/Wolf-code/Wolf-Ai-Enterptises/Wolf-Logic-MCP/data/pgai-queue/
```

## Performance Tuning

### MCP Intake API
- Workers: Set `INTAKE_WORKERS=8` for high traffic
- Port: Change `INTAKE_PORT=8003` if needed
- Deploy behind Caddy for TLS + load balancing

### Swarm Processor
- Model: Use `mistral-small:22b` for faster sentiment (vs mistral:latest)
- Parallel processing: Run multiple instances with different file patterns
- Resource limits: Adjust Nice value in systemd service

### pgai
- Batch size: Configure vectorizer batch size
- Embedding model: qwen3-embedding:4b already optimal (2560 dims, #1 MTEB)

## Security

1. **OAuth required** for MCP Intake API (Authentik)
2. **No DB writes** except via pgai (enforced)
3. **File permissions** on data directories (group: thewolfwalksalone)
4. **TLS** via Caddy for production deployment
5. **Rate limiting** (add nginx/Caddy limits if needed)
