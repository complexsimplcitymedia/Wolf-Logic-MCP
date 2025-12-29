#!/usr/bin/env python3
"""
Wolf Logic Memory API - REST API for Memory Ingestion Pipeline
Swagger UI: http://100.110.82.181:8000/docs
"""
import os
import json
import time
import psycopg2
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Initialize FastAPI
app = FastAPI(
    title="Wolf Logic Memory API",
    description="REST API for Memory Ingestion Pipeline - Query memories, upload transcripts, monitor pipeline status",
    version="1.0.0"
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
CLIENT_DUMPS_DIR = Path("/mnt/Wolf-code/Wolf-Ai-Enterptises/Wolf-Logic-MCP/data/client-dumps")
CLIENT_DUMPS_DIR.mkdir(parents=True, exist_ok=True)

# Models
class Memory(BaseModel):
    id: int
    user_id: str
    content: str
    namespace: str
    created_at: str

class MemoryQuery(BaseModel):
    query: str
    namespace: Optional[str] = None
    limit: int = 10

class TranscriptEntry(BaseModel):
    transcript: str
    session: Optional[str] = "api-upload"
    timestamp: Optional[str] = None

class PipelineStatus(BaseModel):
    server_scripty: bool
    swarm_intake: bool
    pgai_queue: bool
    total_memories: int
    latest_memory: str

# Database helper
def get_db_connection():
    """Get PostgreSQL connection"""
    return psycopg2.connect(**DB_CONFIG)

# API Endpoints
@app.get("/", response_model=Dict)
async def root():
    """API root - returns API info"""
    return {
        "name": "Wolf Logic Memory API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "query_memories": "/memories/query",
            "get_memory": "/memories/{memory_id}",
            "upload_transcript": "/transcripts/upload",
            "pipeline_status": "/pipeline/status"
        }
    }

@app.get("/pipeline/status", response_model=PipelineStatus)
async def get_pipeline_status():
    """Get pipeline status - check if all services are running"""
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

@app.post("/memories/query", response_model=List[Memory])
async def query_memories(query: MemoryQuery):
    """Query memories using semantic search"""
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

@app.get("/memories/{memory_id}", response_model=Memory)
async def get_memory(memory_id: int):
    """Get a specific memory by ID"""
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

@app.post("/transcripts/upload")
async def upload_transcript(entry: TranscriptEntry):
    """Upload a transcript entry to client-dumps for processing"""
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

@app.get("/memories/count", response_model=Dict)
async def get_memory_count():
    """Get total memory count by namespace"""
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
