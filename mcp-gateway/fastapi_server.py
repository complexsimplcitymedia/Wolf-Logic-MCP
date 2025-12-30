"""
MCP Gateway - FastAPI Server
Entry point for Gemini to access Wolf's Librarian

Endpoints:
- POST /query - Query Librarian with semantic search
- POST /recent - Get recent memories
- GET /health - Health check
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import json
from typing import List, Optional

app = FastAPI(
    title="Wolf Intelligence MCP Gateway",
    description="API Gateway for Gemini to access the Librarian",
    version="1.0.0"
)

# CORS for Gemini mobile app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database config
DB_HOST = "100.110.82.181"
DB_PORT = "5433"
DB_NAME = "wolf_logic"
DB_USER = "wolf"
DB_PASS = "wolflogic2024"

class QueryRequest(BaseModel):
    query: str
    namespaces: Optional[List[str]] = ["scripty", "core_identity"]
    limit: Optional[int] = 10

class RecentRequest(BaseModel):
    namespace: Optional[str] = "scripty"
    hours: Optional[int] = 1
    limit: Optional[int] = 20

def execute_psql(sql: str) -> List[str]:
    """Execute PostgreSQL query via psql command"""
    try:
        result = subprocess.run(
            [
                "/usr/bin/env", "psql",
                "-h", DB_HOST,
                "-p", DB_PORT,
                "-U", DB_USER,
                "-d", DB_NAME,
                "-t",  # Tuples only
                "-c", sql
            ],
            env={"PGPASSWORD": DB_PASS},
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            raise Exception(f"psql error: {result.stderr}")

        # Parse output
        lines = [
            line.strip()
            for line in result.stdout.split("\n")
            if line.strip()
        ]
        return lines

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Wolf Intelligence MCP Gateway",
        "librarian": f"{DB_HOST}:{DB_PORT}",
        "database": DB_NAME
    }

@app.post("/query")
async def query_librarian(request: QueryRequest):
    """
    Semantic search query against the Librarian

    Example:
    POST /query
    {
        "query": "What are Wolf's core values?",
        "namespaces": ["core_identity", "scripty"],
        "limit": 10
    }
    """
    # Escape single quotes for SQL
    escaped_query = request.query.replace("'", "''")
    namespaces_str = ", ".join([f"'{ns}'" for ns in request.namespaces])

    sql = f"""
    SELECT content, namespace, created_at
    FROM memories_embedding
    WHERE namespace IN ({namespaces_str})
    ORDER BY embedding <=> ai.ollama_embed('qwen3-embedding:4b', '{escaped_query}')
    LIMIT {request.limit};
    """

    try:
        results = execute_psql(sql)
        return {
            "query": request.query,
            "results_count": len(results),
            "memories": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/recent")
async def get_recent_memories(request: RecentRequest):
    """
    Get recent memories from specified namespace

    Example:
    POST /recent
    {
        "namespace": "scripty",
        "hours": 1,
        "limit": 20
    }
    """
    sql = f"""
    SELECT content, created_at
    FROM memories
    WHERE namespace = '{request.namespace}'
      AND created_at >= NOW() - INTERVAL '{request.hours} hour'
    ORDER BY created_at DESC
    LIMIT {request.limit};
    """

    try:
        results = execute_psql(sql)
        return {
            "namespace": request.namespace,
            "hours": request.hours,
            "results_count": len(results),
            "memories": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/namespaces")
async def list_namespaces():
    """List all available namespaces"""
    sql = "SELECT DISTINCT namespace FROM memories ORDER BY namespace;"

    try:
        results = execute_psql(sql)
        return {
            "namespaces": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    """Get Librarian statistics"""
    sql = """
    SELECT
        (SELECT COUNT(*) FROM memories) as total_memories,
        (SELECT COUNT(*) FROM memories_embedding_store) as vectorized_memories,
        (SELECT COUNT(DISTINCT namespace) FROM memories) as total_namespaces;
    """

    try:
        result = execute_psql(sql)
        # Parse the result (format: "value | value | value")
        if result:
            parts = result[0].split("|")
            return {
                "total_memories": int(parts[0].strip()),
                "vectorized_memories": int(parts[1].strip()),
                "total_namespaces": int(parts[2].strip())
            }
        return {}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
