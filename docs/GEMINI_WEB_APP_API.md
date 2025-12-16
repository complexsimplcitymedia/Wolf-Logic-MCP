# Wolf Logic API Documentation - For Gemini's Web App

## Base URL
```
http://100.110.82.181:8000
```

## Authentication
All endpoints accessible via Tailscale VPN (100.64.0.0/10 network)

---

## Core Endpoints

### Health Check
```http
GET /api/health
```
Returns system health status

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2025-12-16T17:30:00"
}
```

---

### Memory Statistics
```http
GET /api/memory-stats
```
Get comprehensive memory system stats

**Response:**
```json
{
  "total_memories": 87206,
  "total_embeddings": 123644,
  "namespaces": {
    "wolf_story": 15000,
    "scripty": 50000,
    "wolf_hunt": 5000
  },
  "vectorizer_status": {
    "active": true,
    "queue_pending": 44156,
    "processing_rate": "130/sec"
  }
}
```

---

### Memory Count
```http
GET /api/memory/count
```
Simple count of total memories

**Response:**
```json
{
  "count": 87206
}
```

---

### List Namespaces
```http
GET /api/namespaces
```
Get all memory namespaces with counts

**Response:**
```json
[
  {
    "namespace": "wolf_story",
    "count": 15000,
    "last_updated": "2025-12-16T10:00:00"
  },
  {
    "namespace": "scripty",
    "count": 50000,
    "last_updated": "2025-12-16T17:00:00"
  }
]
```

---

## Ingestion Endpoints

### Ingest File
```http
POST /api/ingest/file
Content-Type: application/json
```

**Body:**
```json
{
  "filepath": "/path/to/document.pdf",
  "namespace": "ingested"
}
```

**Response:**
```json
{
  "status": "processing",
  "filepath": "/path/to/document.pdf",
  "task_id": "abc123"
}
```

---

### Bulk Import
```http
POST /api/writers/bulk-import
Content-Type: application/json
```

**Body:**
```json
{
  "directory": "/path/to/documents",
  "namespace": "bulk_import"
}
```

---

## Analysis Endpoints

### YouTube Analysis
```http
POST /api/youtube/analyze
Content-Type: application/json
```

**Body:**
```json
{
  "url": "https://youtube.com/watch?v=xxxxx"
}
```

**Response:**
```json
{
  "status": "processing",
  "video_id": "xxxxx",
  "task_id": "yt_abc123"
}
```

---

### Librarian Search
```http
POST /api/writers/librarian-search
Content-Type: application/json
```

**Body:**
```json
{
  "query": "security vulnerabilities",
  "namespace": "wolf_story",
  "limit": 20
}
```

**Response:**
```json
{
  "results": [
    {
      "id": 12345,
      "content": "Content snippet...",
      "namespace": "wolf_story",
      "similarity": 0.89,
      "created_at": "2025-12-10T10:00:00"
    }
  ],
  "count": 15
}
```

---

### Rank Memories
```http
POST /api/rank-memories
Content-Type: application/json
```

**Body:**
```json
{
  "query": "job applications",
  "limit": 50
}
```

---

## System Control Endpoints

### Scripty Control
```http
POST /api/scripty/start
POST /api/scripty/stop
POST /api/scripty/restart
GET  /api/scripty/status
```

All return `ScriptyStatus`:
```json
{
  "status": "running",
  "pid": 12345,
  "uptime": "2h 30m"
}
```

---

### Logger Control
```http
POST /api/logger/start
POST /api/logger/stop
```

**Response:**
```json
{
  "success": true,
  "message": "Logger started",
  "output": "Process output..."
}
```

---

## System Status Endpoints

### System Processes
```http
GET /api/system/status
```

Returns list of Wolf system processes (scripty, logger, vectorizer, etc.)

**Response:**
```json
[
  {
    "name": "scripty",
    "status": "running",
    "pid": 12345,
    "cpu": "2.5%",
    "memory": "150MB"
  }
]
```

---

### System Uptime
```http
GET /api/system/uptime
```

**Response:**
```json
{
  "uptime": "5 days, 12:30:45",
  "boot_time": "2025-12-11T05:00:00"
}
```

---

### GPU Stats (AMD RX 7900 XT)
```http
GET /api/gpu/stats
```

**Response:**
```json
{
  "name": "AMD Radeon RX 7900 XT",
  "vram_used": "8.5 GB",
  "vram_total": "21.4 GB",
  "utilization": "45%",
  "temperature": "65°C"
}
```

---

## Neo4j Graph Endpoints

### Neo4j Health
```http
GET /api/neo4j/health
```

### Neo4j Stats
```http
GET /api/neo4j/stats
```

### Query Neo4j
```http
POST /api/neo4j/query
Content-Type: application/json
```

**Body:**
```json
{
  "cypher": "MATCH (n:Memory) RETURN count(n)"
}
```

---

## Wolf Hunt Endpoints

**Base URL:** `http://100.110.82.181:5000`

### Get All Jobs
```http
GET /api/jobs/scraped
```

Returns all 2,916 scraped job listings

**Response:**
```json
{
  "jobs": [
    {
      "id": 1,
      "title": "Senior Software Engineer",
      "company": "Tech Corp",
      "location": "Remote",
      "salary": "$150k-200k",
      "url": "https://...",
      "scraped_at": "2025-12-15T10:00:00"
    }
  ],
  "total": 2916
}
```

### Get Jobs by Board
```http
GET /api/jobs/{board}
```

Boards: `ziprecruiter`, `indeed`, `linkedin`, `dice`, `careerbuilder`, `monster`

---

## Direct Database Access

For advanced queries, Gemini can connect directly via Tailscale:

**Connection String:**
```
postgresql://wolf:wolflogic2024@100.110.82.181:5433/wolf_logic
```

**Tables:**
- `memories` - All memory content
- `memories_embedding_store` - Vector embeddings (2560 dims, qwen3-embedding:4b)
- `job_applications` - Wolf Hunt applications
- `ai.vectorizer` - Vectorizer queue status

---

## MCP Server (For AI Agents)

**Endpoint:** stdio (not HTTP)

**Available Tools:**
- `query` - Execute read-only SQL
- `list_tables` - List all database tables
- `describe_table` - Get table schema
- `search_memories` - Text search memories
- `vector_search` - Semantic search (embeddings)
- `get_applications` - Query job applications
- `get_stats` - Database statistics

---

## Error Responses

All errors return:
```json
{
  "error": "Error message",
  "details": "Detailed error information",
  "timestamp": "2025-12-16T17:30:00"
}
```

**Common Status Codes:**
- `200` - Success
- `400` - Bad Request
- `404` - Not Found
- `500` - Internal Server Error
- `503` - Service Unavailable

---

## Rate Limiting

No rate limiting currently enforced.

**Future Scale:** Will implement MCP-based access control when hitting 100K+ users.

---

## WebSocket Support (Future)

Real-time updates for:
- Vectorizer progress
- Memory ingestion status
- System health monitoring

**Endpoint (not yet active):**
```
ws://100.110.82.181:8000/ws
```

---

## Notes for Gemini

1. **All services accessible via Tailscale** - No localhost dependencies
2. **Database direct access available** - No middleware bottleneck
3. **FastAPI server** - Auto-generated docs at `http://100.110.82.181:8000/docs`
4. **Wolf Hunt UI** - Reference implementation at `http://100.110.82.181:8033`
5. **MCP for AI agents** - Will scale when user base grows
6. **Local-first architecture** - Batch sync model, not real-time
7. **87K+ memories ready** - Fully vectorized and searchable
8. **2,916 jobs scraped** - Ready for application tracking

---

## Getting Paid Architecture

When Wolf gets paid and scales to 100K users:

1. **Users pull once** - 1.3GB database dump from GitHub Release
2. **Local vectorization** - Swarm processing on user devices
3. **Zero server dependency** - Autonomous after initial sync
4. **Context-driven sync** - Trigger at 90% context window (180K tokens)
5. **Batch uploads** - Generate fresh dump, push to GitHub
6. **MCP for scale** - AI agents coordinate across distributed network

**"Watch this shit."** - Wolf, 2025-12-16
