# Wolf Intelligence MCP Gateway

API Gateway for Gemini to access the Librarian (100K+ memories).

## Architecture

```
Gemini (Android/Mobile)
    ↓ HTTP/REST
MCP Gateway (FastAPI) :8080
    ↓ PostgreSQL
Librarian (100.110.82.181:5433)
    ↓
99K+ Memories (qwen3-embedding:4b)
```

## Endpoints

### POST /query
Semantic search query against the Librarian.

**Request:**
```json
{
  "query": "What are Wolf's core values?",
  "namespaces": ["core_identity", "scripty"],
  "limit": 10
}
```

**Response:**
```json
{
  "query": "What are Wolf's core values?",
  "results_count": 10,
  "memories": [...]
}
```

### POST /recent
Get recent memories from specified namespace.

**Request:**
```json
{
  "namespace": "scripty",
  "hours": 1,
  "limit": 20
}
```

### GET /health
Health check endpoint.

### GET /namespaces
List all available namespaces.

### GET /stats
Get Librarian statistics.

## Run with Docker

```bash
cd mcp-gateway
docker-compose up -d
```

Gateway will be available at: `http://localhost:8080`

## Run Locally (without Docker)

```bash
cd mcp-gateway
pip install -r requirements.txt
python fastapi_server.py
```

## Test

```bash
# Health check
curl http://localhost:8080/health

# Query Librarian
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Wolf'\''s philosophy?"}'

# Get recent memories
curl -X POST http://localhost:8080/recent \
  -H "Content-Type: application/json" \
  -d '{"namespace": "scripty", "hours": 1}'

# Get stats
curl http://localhost:8080/stats
```

## Swagger Docs

Once running, visit: `http://localhost:8080/docs`

## For Gemini Integration

Point Gemini's API endpoint to:
- Local: `http://localhost:8080`
- Network: `http://<your-mac-ip>:8080`
- Tailscale: `http://100.x.x.x:8080`

Use POST /query endpoint for all Librarian queries.
