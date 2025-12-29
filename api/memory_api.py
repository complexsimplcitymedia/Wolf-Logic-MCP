#!/usr/bin/env python3
"""
Wolf Logic Memory API - REST API for Memory Ingestion Pipeline
Swagger UI: http://100.110.82.181:8001/docs
ReDoc: http://100.110.82.181:8001/redoc
"""
import os
import json
import time
import psycopg2
from datetime import datetime
from pathlib import Path as FilePath
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, UploadFile, File, Query, Body, Path
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Initialize FastAPI
app = FastAPI(
    title="Wolf Logic Memory API",
    description="""
# Wolf Logic Memory Ingestion Pipeline API

Complete REST API for memory ingestion, semantic search, and pipeline monitoring.

## Features
- **Semantic Search**: Query memories using qwen3-embedding:4b
- **Upload Transcripts**: Drop transcripts to client-dumps for auto-processing
- **Pipeline Monitoring**: Real-time status of all services
- **Multi-namespace Support**: Query across scripty, wolf_hunt, core_identity, etc.

## Pipeline Flow
1. Remote nodes upload to `/transcripts/upload`
2. Swarm processes with llama3.2:1b (keywords/summary) + mistral (sentiment)
3. PGAI queue ingests to PostgreSQL
4. pgai vectorizer embeds with qwen3-embedding:4b

## Network
- **Tailscale mesh**: 100.110.0.0/16, 100.250.0.0/16
- **NFS mount**: Available for direct file drops
    """,
    version="1.0.0",
    contact={
        "name": "Wolf AI Enterprises",
        "url": "https://complexsimplicityai.com"
    }
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database config
DB_CONFIG = {
    "host": os.getenv("PGHOST", "100.110.82.181"),
    "port": os.getenv("PGPORT", "5433"),
    "database": os.getenv("PGDATABASE", "wolf_logic"),
    "user": os.getenv("PGUSER", "wolf"),
    "password": os.getenv("PGPASSWORD", "wolflogic2024")
}

# Directories
CLIENT_DUMPS_DIR = FilePath("/mnt/Wolf-code/Wolf-Ai-Enterptises/Wolf-Logic-MCP/data/client-dumps")
CLIENT_DUMPS_DIR.mkdir(parents=True, exist_ok=True)

# Models
class Memory(BaseModel):
    """Memory entry from PostgreSQL"""
    id: int = Field(..., description="Unique memory ID")
    user_id: str = Field(..., description="User who created the memory")
    content: str = Field(..., description="Memory content/text")
    namespace: str = Field(..., description="Memory namespace (scripty, wolf_hunt, core_identity, etc.)")
    created_at: str = Field(..., description="Creation timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 100494,
                "user_id": "wolf",
                "content": "Discussed memory ingestion pipeline implementation",
                "namespace": "scripty",
                "created_at": "2025-12-29 08:48:11.716796-05:00"
            }
        }

class MemoryQuery(BaseModel):
    """Semantic search query parameters"""
    query: str = Field(..., description="Search query for semantic matching", min_length=1)
    namespace: Optional[str] = Field(None, description="Filter by namespace (scripty, wolf_hunt, etc.)")
    limit: int = Field(10, description="Maximum results to return", ge=1, le=100)

    class Config:
        json_schema_extra = {
            "example": {
                "query": "memory ingestion pipeline",
                "namespace": "scripty",
                "limit": 10
            }
        }

class TranscriptEntry(BaseModel):
    """Transcript entry for upload"""
    transcript: str = Field(..., description="Transcript text content", min_length=1)
    session: Optional[str] = Field("api-upload", description="Session identifier")
    timestamp: Optional[str] = Field(None, description="ISO timestamp (defaults to current time)")

    class Config:
        json_schema_extra = {
            "example": {
                "transcript": "USER: How's the memory pipeline? ASSISTANT: Running smoothly with 100K+ memories.",
                "session": "node-245",
                "timestamp": "2025-12-29T09:00:00-05:00"
            }
        }

class PipelineStatus(BaseModel):
    """Pipeline service status"""
    server_scripty: bool = Field(..., description="Server-scripty process running")
    swarm_intake: bool = Field(..., description="Swarm intake processor running")
    pgai_queue: bool = Field(..., description="PGAI queue ingestor running")
    total_memories: int = Field(..., description="Total memories in database")
    latest_memory: str = Field(..., description="Timestamp of most recent memory")

    class Config:
        json_schema_extra = {
            "example": {
                "server_scripty": True,
                "swarm_intake": True,
                "pgai_queue": True,
                "total_memories": 100754,
                "latest_memory": "2025-12-29 09:10:56.263956-05:00"
            }
        }

class NamespaceCount(BaseModel):
    """Memory count by namespace"""
    namespace: str = Field(..., description="Namespace name")
    count: int = Field(..., description="Number of memories in namespace")

class HealthResponse(BaseModel):
    """API health check response"""
    status: str = Field(..., description="API status")
    timestamp: str = Field(..., description="Current server time")
    database: bool = Field(..., description="Database connectivity")
    services: Dict[str, bool] = Field(..., description="Service status")

# Database helper
def get_db_connection():
    """Get PostgreSQL connection"""
    return psycopg2.connect(**DB_CONFIG)

# API Endpoints
@app.get("/",
    summary="API Root",
    description="Returns API information and available endpoints",
    response_model=Dict[str, Any],
    tags=["Info"])
async def root():
    """
    ## API Root Endpoint

    Returns basic API information including version, documentation links, and available endpoints.

    **Use this endpoint to:**
    - Verify API is running
    - Get links to Swagger UI and ReDoc
    - Discover available endpoints
    """
    return {
        "name": "Wolf Logic Memory API",
        "version": "1.0.0",
        "status": "operational",
        "docs": {
            "swagger": "http://100.110.82.181:8001/docs",
            "redoc": "http://100.110.82.181:8001/redoc"
        },
        "endpoints": {
            "health": "/health",
            "query_memories": "/memories/query",
            "get_memory": "/memories/{memory_id}",
            "list_namespaces": "/namespaces",
            "memory_count": "/memories/count",
            "upload_transcript": "/transcripts/upload",
            "pipeline_status": "/pipeline/status"
        }
    }

@app.get("/health",
    summary="Health Check",
    description="Check API and database health",
    response_model=HealthResponse,
    tags=["Monitoring"])
async def health_check():
    """
    ## Health Check Endpoint

    Returns comprehensive health status including:
    - API operational status
    - Database connectivity
    - Pipeline services status

    **Use this for:**
    - Monitoring/alerting systems
    - Load balancer health checks
    - Debugging connectivity issues
    """
    import subprocess

    def check_process(name):
        try:
            result = subprocess.run(['pgrep', '-f', name], capture_output=True)
            return result.returncode == 0
        except:
            return False

    # Test database connection
    db_healthy = False
    try:
        conn = get_db_connection()
        conn.close()
        db_healthy = True
    except:
        pass

    return HealthResponse(
        status="healthy" if db_healthy else "degraded",
        timestamp=datetime.now().isoformat(),
        database=db_healthy,
        services={
            "server_scripty": check_process("server-scripty.py"),
            "swarm_intake": check_process("swarm_intake_processor.py"),
            "pgai_queue": check_process("pgai_queue_ingestor.py")
        }
    )

@app.get("/pipeline/status",
    summary="Pipeline Status",
    description="Get real-time status of all pipeline services",
    response_model=PipelineStatus,
    tags=["Monitoring"])
async def get_pipeline_status():
    """
    ## Pipeline Status Endpoint

    Returns real-time status of the memory ingestion pipeline:
    - **server_scripty**: Session transcription capture
    - **swarm_intake**: Processing with llama3.2:1b + mistral
    - **pgai_queue**: PostgreSQL ingestion
    - **Memory statistics**: Total count and latest timestamp

    **Use this for:**
    - Dashboard monitoring
    - Alerting when services are down
    - Tracking memory growth over time
    """
    import subprocess

    def check_process(name):
        try:
            result = subprocess.run(['pgrep', '-f', name], capture_output=True)
            return result.returncode == 0
        except:
            return False

    # Get memory count
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*), MAX(created_at) FROM memories")
        count, latest = cur.fetchone()
        cur.close()
        conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return PipelineStatus(
        server_scripty=check_process("server-scripty.py"),
        swarm_intake=check_process("swarm_intake_processor.py"),
        pgai_queue=check_process("pgai_queue_ingestor.py"),
        total_memories=count,
        latest_memory=str(latest) if latest else "None"
    )

@app.post("/memories/query",
    summary="Query Memories",
    description="Semantic search across memories using qwen3-embedding:4b",
    response_model=List[Memory],
    tags=["Memories"])
async def query_memories(query: MemoryQuery = Body(..., example={
    "query": "memory ingestion pipeline implementation",
    "namespace": "scripty",
    "limit": 10
})):
    """
    ## Semantic Memory Search

    Search memories using natural language queries. Uses qwen3-embedding:4b for semantic similarity matching.

    **Query Parameters:**
    - `query`: Natural language search query
    - `namespace`: Filter by namespace (optional)
    - `limit`: Maximum results (1-100, default 10)

    **Available Namespaces:**
    - `scripty`: Session transcripts (46K+)
    - `wolf_story`: Books & narratives (16K+)
    - `ingested`: Document ingestions (10K+)
    - `session_recovery`: Context recovery (9K+)
    - `wolf_hunt`: Job search data (2K+)
    - `core_identity`: Core values/directives (9)

    **Example Query:**
    ```json
    {
        "query": "How does the memory pipeline work?",
        "namespace": "scripty",
        "limit": 5
    }
    ```
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        if query.namespace:
            sql = """
                SELECT id, user_id, content, namespace, created_at::text
                FROM memories_embedding
                WHERE namespace = %s
                ORDER BY embedding <=> ai.ollama_embed('qwen3-embedding:4b', %s)
                LIMIT %s
            """
            cur.execute(sql, (query.namespace, query.query, query.limit))
        else:
            sql = """
                SELECT id, user_id, content, namespace, created_at::text
                FROM memories_embedding
                ORDER BY embedding <=> ai.ollama_embed('qwen3-embedding:4b', %s)
                LIMIT %s
            """
            cur.execute(sql, (query.query, query.limit))

        results = cur.fetchall()
        cur.close()
        conn.close()

        return [Memory(
            id=r[0],
            user_id=r[1],
            content=r[2],
            namespace=r[3],
            created_at=r[4]
        ) for r in results]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query error: {str(e)}")

@app.get("/memories/{memory_id}",
    summary="Get Memory by ID",
    description="Retrieve a specific memory using its unique ID",
    response_model=Memory,
    tags=["Memories"])
async def get_memory(
    memory_id: int = Path(..., description="Unique memory ID", example=100494)
):
    """
    ## Get Specific Memory

    Retrieve a single memory by its unique ID.

    **Use this when:**
    - Following up on a search result
    - Direct memory reference from external systems
    - Debugging specific memory entries
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, user_id, content, namespace, created_at::text
            FROM memories
            WHERE id = %s
        """, (memory_id,))
        result = cur.fetchone()
        cur.close()
        conn.close()

        if not result:
            raise HTTPException(status_code=404, detail="Memory not found")

        return Memory(
            id=result[0],
            user_id=result[1],
            content=result[2],
            namespace=result[3],
            created_at=result[4]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/transcripts/upload",
    summary="Upload Transcript",
    description="Upload a transcript to client-dumps for automatic pipeline processing",
    tags=["Transcripts"],
    responses={
        200: {
            "description": "Transcript uploaded successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "message": "Transcript uploaded to pipeline",
                        "file": "transcript_20251229.jsonl",
                        "session": "node-245"
                    }
                }
            }
        }
    })
async def upload_transcript(entry: TranscriptEntry = Body(..., example={
    "transcript": "USER: Test message from remote node. ASSISTANT: Received and processing.",
    "session": "node-245",
    "timestamp": "2025-12-29T09:00:00-05:00"
})):
    """
    ## Upload Transcript

    Upload a transcript entry for processing by the memory pipeline.

    **Processing Flow:**
    1. Transcript written to `data/client-dumps/transcript_YYYYMMDD.jsonl`
    2. Swarm-intake picks up and processes (30-second polling)
    3. Keywords extracted (llama3.2:1b)
    4. Sentiment analyzed (mistral)
    5. Ingested to PostgreSQL
    6. Vectorized by pgai (qwen3-embedding:4b)

    **Remote Nodes:**
    Instead of API, remote nodes can mount via NFS:
    ```bash
    mount -t nfs 100.110.82.181:/mnt/.../client-dumps /mnt/wolf-client-dumps
    echo '{json}' >> /mnt/wolf-client-dumps/transcript_YYYYMMDD.jsonl
    ```
    """
    try:
        # Create transcript entry
        timestamp = entry.timestamp or datetime.now().isoformat()
        transcript_data = {
            "transcript": entry.transcript,
            "session": entry.session,
            "timestamp": timestamp
        }

        # Write to client-dumps
        today = datetime.now().strftime("%Y%m%d")
        output_file = CLIENT_DUMPS_DIR / f"transcript_{today}.jsonl"

        with open(output_file, 'a') as f:
            f.write(json.dumps(transcript_data) + '\n')

        return {
            "status": "success",
            "message": "Transcript uploaded to pipeline",
            "file": output_file.name,
            "session": entry.session
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")

@app.get("/namespaces",
    summary="List Namespaces",
    description="Get list of all available namespaces with memory counts",
    response_model=Dict[str, Any],
    tags=["Memories"])
async def list_namespaces():
    """
    ## List All Namespaces

    Returns all namespaces with their memory counts, sorted by count descending.

    **Use this to:**
    - Discover available namespaces for filtering
    - Monitor namespace growth over time
    - Identify largest memory categories
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT namespace, COUNT(*) as count
            FROM memories
            GROUP BY namespace
            ORDER BY count DESC
        """)
        results = cur.fetchall()
        cur.close()
        conn.close()

        namespaces = [
            {"namespace": r[0], "count": r[1]}
            for r in results
        ]

        return {
            "namespaces": namespaces,
            "total_namespaces": len(namespaces),
            "total_memories": sum(r[1] for r in results)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/memories/count",
    summary="Memory Count",
    description="Get total memory count by namespace (legacy endpoint, use /namespaces instead)",
    response_model=Dict[str, Any],
    tags=["Memories"],
    deprecated=True)
async def get_memory_count():
    """
    ## Memory Count (Deprecated)

    **Use `/namespaces` instead** - provides better structured data.

    Returns memory counts grouped by namespace.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT namespace, COUNT(*) as count
            FROM memories
            GROUP BY namespace
            ORDER BY count DESC
        """)
        results = cur.fetchall()
        cur.close()
        conn.close()

        return {
            "namespaces": {r[0]: r[1] for r in results},
            "total": sum(r[1] for r in results)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
