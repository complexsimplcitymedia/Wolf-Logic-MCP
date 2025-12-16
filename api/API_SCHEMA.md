# Wolf AI FastAPI Server - API Schema Documentation

Complete FastAPI server with Pydantic schemas for all dashboard buttons.

## Server Details

**File:** `/mnt/Wolf-code/Wolf-Ai-Enterptises/api/fastapi_server.py`
**Port:** 8000
**Docs:** http://localhost:8000/docs (Interactive Swagger UI)

## Start Server

```bash
source ~/anaconda3/bin/activate messiah
cd /mnt/Wolf-code/Wolf-Ai-Enterptises/api
python fastapi_server.py
```

Or with uvicorn:
```bash
uvicorn fastapi_server:app --host 0.0.0.0 --port 8000 --reload
```

---

## API Endpoints

### Health & Status

#### `GET /`
Root endpoint - API info

#### `GET /api/health`
Health check with database status

---

### Memory Statistics

#### `GET /api/memory-stats`
**Response Schema:** `MemoryStats`
```json
{
  "total_memories": 30469,
  "today_count": 1247,
  "last_hour_count": 89,
  "last_updated": "2025-12-02T16:00:00",
  "top_namespace": {
    "name": "wolf_story",
    "count": 13309
  },
  "avg_per_day_7d": 2156,
  "timestamp": "2025-12-02T16:11:44"
}
```

#### `GET /api/memory-count`
Fast simple count
```json
{
  "total_memories": 30469
}
```

---

### Scripty Control

#### `POST /api/scripty/start`
**Response Schema:** `ScriptyStatus`
```json
{
  "running": true,
  "pid": 12345,
  "uptime_minutes": null,
  "log_file": "/tmp/scripty.log",
  "message": "Scripty started successfully",
  "status": "started"
}
```

#### `POST /api/scripty/stop`
Stop scripty daemon

#### `GET /api/scripty/status`
Get current status

#### `POST /api/scripty/restart`
Restart scripty daemon

---

### Dashboard Control

#### `POST /api/dashboard/refresh?days=30`
**Response Schema:** `DashboardRefreshResponse`
```json
{
  "success": true,
  "message": "Dashboard generated successfully",
  "charts": {
    "timeline": "/path/to/timeline.png",
    "namespaces": "/path/to/namespaces.png",
    "hourly": "/path/to/hourly.png"
  },
  "html_dashboard": "/path/to/dashboard.html",
  "charts_dir": "/mnt/Wolf-code/Wolf-Ai-Enterptises/metrics/charts",
  "generated_at": "2025-12-02T16:11:44"
}
```

#### `GET /api/dashboard/charts`
Get paths to current chart files

---

### File Ingestion

#### `POST /api/ingest/file`
**Request Schema:** `IngestRequest`
```json
{
  "filepath": "/path/to/file.pdf"
}
```

**Response Schema:** `IngestResponse`
```json
{
  "success": true,
  "message": "PDF ingested successfully: file.pdf",
  "file": "file.pdf",
  "file_type": "pdf",
  "chunks_stored": 145,
  "pages_processed": 23
}
```

---

### Session Logger Control

#### `POST /api/logger/start`
Start session logger (dailies)

#### `POST /api/logger/stop`
Stop session logger

**Response Schema:** `CommandResponse`
```json
{
  "success": true,
  "message": "Session logger started",
  "data": null,
  "timestamp": "2025-12-02T16:11:44"
}
```

---

### Utilities

#### `POST /api/rank-memories`
Rank memories by importance

#### `POST /api/youtube/analyze`
**Request Schema:** `YouTubeRequest`
```json
{
  "url": "https://youtube.com/watch?v=...",
  "frame_interval": 15,
  "store": true
}
```

Runs in background, returns immediately

#### `GET /api/logs?lines=50`
Get recent log entries
```json
{
  "logs": "log content here...",
  "lines": 50
}
```

#### `GET /api/system/status`
**Response Schema:** `List[ProcessStatusResponse]`
```json
[
  {
    "process_name": "scripty",
    "running": true,
    "count": 1,
    "pids": [12345]
  },
  {
    "process_name": "session_logger",
    "running": false,
    "count": 0,
    "pids": []
  }
]
```

---

### Database Queries

#### `GET /api/namespaces`
Get all namespaces with statistics
```json
[
  {
    "namespace": "wolf_story",
    "count": 13309,
    "first_entry": "2024-11-01T10:00:00",
    "last_entry": "2025-12-02T16:00:00"
  }
]
```

---

## Pydantic Schemas

All request/response schemas defined in the FastAPI server:

- `CommandResponse` - Standard command response
- `MemoryStats` - Memory system statistics
- `ScriptyStatus` - Scripty daemon status
- `DashboardRefreshResponse` - Dashboard generation result
- `IngestRequest` - File ingestion request
- `IngestResponse` - File ingestion result
- `YouTubeRequest` - YouTube analysis request
- `ProcessStatusResponse` - Process status info

---

## Interactive Documentation

FastAPI auto-generates interactive docs:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

Test all endpoints directly from the browser.

---

## CORS Enabled

All origins allowed for development. Restrict in production.

---

## Dependencies

Install with:
```bash
pip install -r requirements.txt
```

- fastapi
- uvicorn[standard]
- pydantic
- psycopg2-binary
- python-multipart
