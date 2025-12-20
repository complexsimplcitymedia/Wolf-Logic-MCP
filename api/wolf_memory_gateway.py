#!/usr/bin/env python3
"""
Wolf Memory Gateway - Production REST API
Memory operations for 100+ beta testers with HA load balancing

Inspired by Mem0 API structure, powered by Wolf infrastructure
"""

from fastapi import FastAPI, HTTPException, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict, List
from datetime import datetime
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom Swagger UI with Wolf branding
CUSTOM_SWAGGER_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Wolf Memory Gateway API</title>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css" >
    <style>
        body {
            background-color: #0a0a0a;
            margin: 0;
            padding: 0;
        }
        .topbar {
            background-color: #000000 !important;
            border-bottom: 3px solid #dc143c !important;
        }
        .swagger-ui .topbar .download-url-wrapper {
            display: none;
        }
        .swagger-ui .info .title {
            color: #dc143c !important;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-weight: 700;
        }
        .swagger-ui .info .title small {
            background-color: #dc143c;
            color: #000000;
            padding: 5px 10px;
            border-radius: 3px;
            font-weight: bold;
        }
        .swagger-ui .scheme-container {
            background: #1a1a1a;
            border: 1px solid #dc143c;
        }
        .swagger-ui .opblock.opblock-get {
            border-color: #dc143c;
            background: rgba(220, 20, 60, 0.1);
        }
        .swagger-ui .opblock.opblock-post {
            border-color: #8b0000;
            background: rgba(139, 0, 0, 0.1);
        }
        .swagger-ui .opblock.opblock-put {
            border-color: #ff4500;
            background: rgba(255, 69, 0, 0.1);
        }
        .swagger-ui .opblock.opblock-delete {
            border-color: #b22222;
            background: rgba(178, 34, 34, 0.1);
        }
        .swagger-ui .btn.execute {
            background-color: #dc143c;
            border-color: #dc143c;
            color: #ffffff;
        }
        .swagger-ui .btn.execute:hover {
            background-color: #b01030;
        }
        #wolf-logo {
            position: absolute;
            top: 10px;
            right: 20px;
            height: 60px;
            width: auto;
        }
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script>
        window.onload = function() {
            const ui = SwaggerUIBundle({
                url: "/openapi.json",
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIBundle.SwaggerUIStandalonePreset
                ],
                layout: "BaseLayout"
            })
            window.ui = ui
        }
    </script>
</body>
</html>
"""

app = FastAPI(
    title="Wolf Memory Gateway",
    description="Production memory infrastructure for Wolf AI - Built for scale, tested in battle",
    version="1.0.0",
    docs_url=None,  # Custom Swagger UI
    redoc_url="/redoc"
)

# CORS for Android app + web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Lock down in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# DATABASE CONFIG
# ============================================================================

DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "100.110.82.181"),
    "port": int(os.getenv("POSTGRES_PORT", "5433")),
    "user": os.getenv("POSTGRES_USER", "wolf"),
    "password": os.getenv("POSTGRES_PASSWORD", "wolflogic2024"),
    "database": os.getenv("POSTGRES_DB", "wolf_logic")
}

def get_db():
    """Get PostgreSQL connection"""
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class HealthResponse(BaseModel):
    status: str = Field(..., description="Service health status")
    database: str = Field(..., description="Database connection status")
    total_memories: int = Field(..., description="Total memories in database")
    version: str = Field(..., description="API version")
    timestamp: str = Field(..., description="Response timestamp")

class AddMemoryRequest(BaseModel):
    content: str = Field(..., description="Memory content to store")
    user_id: Optional[str] = Field(None, description="User identifier")
    agent_id: Optional[str] = Field(None, description="Agent identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")
    namespace: str = Field("default", description="Memory namespace/category")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class SearchMemoriesRequest(BaseModel):
    query: str = Field(..., description="Search query text")
    user_id: Optional[str] = Field(None, description="Filter by user")
    agent_id: Optional[str] = Field(None, description="Filter by agent")
    session_id: Optional[str] = Field(None, description="Filter by session")
    namespace: Optional[str] = Field(None, description="Filter by namespace")
    limit: int = Field(20, ge=1, le=100, description="Maximum results")

class GetMemoriesRequest(BaseModel):
    user_id: Optional[str] = Field(None, description="Filter by user")
    agent_id: Optional[str] = Field(None, description="Filter by agent")
    session_id: Optional[str] = Field(None, description="Filter by session")
    namespace: Optional[str] = Field(None, description="Filter by namespace")
    limit: int = Field(50, ge=1, le=500, description="Maximum results")

class UpdateMemoryRequest(BaseModel):
    content: Optional[str] = Field(None, description="Updated content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Updated metadata")

class MemoryResponse(BaseModel):
    id: int
    content: str
    namespace: str
    metadata: Optional[Dict[str, Any]]
    created_at: str
    updated_at: str

class StandardResponse(BaseModel):
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Response message")
    data: Optional[Any] = Field(None, description="Response data")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

# ============================================================================
# CUSTOM SWAGGER UI
# ============================================================================

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui():
    """Custom branded Swagger UI"""
    return HTMLResponse(content=CUSTOM_SWAGGER_HTML)

# ============================================================================
# CORE ENDPOINTS
# ============================================================================

@app.get("/", response_model=Dict[str, Any])
async def root():
    """API root - service information"""
    return {
        "service": "Wolf Memory Gateway",
        "version": "1.0.0",
        "status": "operational",
        "documentation": "/docs",
        "health": "/health",
        "endpoints": {
            "add_memory": "POST /memories/add",
            "search_memories": "POST /memories/search",
            "get_memories": "POST /memories/get",
            "update_memory": "PUT /memories/{memory_id}",
            "delete_memory": "DELETE /memories/{memory_id}",
            "stats": "GET /memories/stats"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check with database connectivity and memory count"""
    db_status = "healthy"
    total_memories = 0

    try:
        conn = get_db()
        cursor = conn.cursor()

        # Test connectivity
        cursor.execute("SELECT 1")

        # Get total memory count
        cursor.execute("SELECT COUNT(*) as count FROM memories")
        total_memories = cursor.fetchone()['count']

        cursor.close()
        conn.close()
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        db_status = "unhealthy"

    return HealthResponse(
        status="healthy" if db_status == "healthy" else "degraded",
        database=db_status,
        total_memories=total_memories,
        version="1.0.0",
        timestamp=datetime.now().isoformat()
    )

# ============================================================================
# MEMORY OPERATIONS
# ============================================================================

@app.post("/memories/add",
          response_model=StandardResponse,
          summary="Add Memory",
          description="Store a new memory with optional user/agent/session identifiers")
async def add_memory(request: AddMemoryRequest):
    """Add a new memory to the database"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Build metadata
        metadata = request.metadata or {}
        if request.user_id:
            metadata['user_id'] = request.user_id
        if request.agent_id:
            metadata['agent_id'] = request.agent_id
        if request.session_id:
            metadata['session_id'] = request.session_id

        # Insert memory
        cursor.execute("""
            INSERT INTO memories (user_id, content, namespace, metadata, created_at, updated_at)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
            RETURNING id, content, namespace, metadata, created_at, updated_at
        """, (
            request.user_id or 'system',
            request.content,
            request.namespace,
            json.dumps(metadata)
        ))

        memory = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()

        return StandardResponse(
            success=True,
            message="Memory added successfully",
            data={
                "memory_id": memory['id'],
                "namespace": memory['namespace'],
                "created_at": memory['created_at'].isoformat()
            }
        )

    except Exception as e:
        logger.error(f"Add memory error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/memories/search",
          response_model=StandardResponse,
          summary="Search Memories",
          description="Search memories using text matching with optional filters")
async def search_memories(request: SearchMemoriesRequest):
    """Search memories by text query with entity filtering"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Build WHERE clause
        conditions = ["content ILIKE %s"]
        params = [f"%{request.query}%"]

        if request.namespace:
            conditions.append("namespace = %s")
            params.append(request.namespace)

        if request.user_id:
            conditions.append("metadata->>'user_id' = %s")
            params.append(request.user_id)

        if request.agent_id:
            conditions.append("metadata->>'agent_id' = %s")
            params.append(request.agent_id)

        if request.session_id:
            conditions.append("metadata->>'session_id' = %s")
            params.append(request.session_id)

        where_clause = " AND ".join(conditions)
        params.append(request.limit)

        # Execute search
        cursor.execute(f"""
            SELECT id, content, namespace, metadata, created_at, updated_at
            FROM memories
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT %s
        """, params)

        results = cursor.fetchall()
        cursor.close()
        conn.close()

        # Format results
        memories = [{
            'id': r['id'],
            'content': r['content'],
            'namespace': r['namespace'],
            'metadata': r['metadata'],
            'created_at': r['created_at'].isoformat(),
            'updated_at': r['updated_at'].isoformat()
        } for r in results]

        return StandardResponse(
            success=True,
            message=f"Found {len(memories)} memories",
            data={"memories": memories, "count": len(memories)}
        )

    except Exception as e:
        logger.error(f"Search memories error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/memories/get",
          response_model=StandardResponse,
          summary="Get Memories",
          description="Retrieve memories with entity-based filtering")
async def get_memories(request: GetMemoriesRequest):
    """Get memories filtered by user/agent/session/namespace"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Build WHERE clause
        conditions = []
        params = []

        if request.namespace:
            conditions.append("namespace = %s")
            params.append(request.namespace)

        if request.user_id:
            conditions.append("metadata->>'user_id' = %s")
            params.append(request.user_id)

        if request.agent_id:
            conditions.append("metadata->>'agent_id' = %s")
            params.append(request.agent_id)

        if request.session_id:
            conditions.append("metadata->>'session_id' = %s")
            params.append(request.session_id)

        where_clause = " AND ".join(conditions) if conditions else "TRUE"
        params.append(request.limit)

        # Execute query
        cursor.execute(f"""
            SELECT id, content, namespace, metadata, created_at, updated_at
            FROM memories
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT %s
        """, params)

        results = cursor.fetchall()
        cursor.close()
        conn.close()

        # Format results
        memories = [{
            'id': r['id'],
            'content': r['content'],
            'namespace': r['namespace'],
            'metadata': r['metadata'],
            'created_at': r['created_at'].isoformat(),
            'updated_at': r['updated_at'].isoformat()
        } for r in results]

        return StandardResponse(
            success=True,
            message=f"Retrieved {len(memories)} memories",
            data={"memories": memories, "count": len(memories)}
        )

    except Exception as e:
        logger.error(f"Get memories error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/memories/{memory_id}",
         response_model=StandardResponse,
         summary="Update Memory",
         description="Update memory content or metadata")
async def update_memory(memory_id: int, request: UpdateMemoryRequest):
    """Update an existing memory"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Build update fields
        updates = []
        params = []

        if request.content:
            updates.append("content = %s")
            params.append(request.content)

        if request.metadata:
            updates.append("metadata = %s")
            params.append(json.dumps(request.metadata))

        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        updates.append("updated_at = NOW()")
        params.append(memory_id)

        # Execute update
        cursor.execute(f"""
            UPDATE memories
            SET {", ".join(updates)}
            WHERE id = %s
            RETURNING id, content, namespace, metadata, updated_at
        """, params)

        memory = cursor.fetchone()

        if not memory:
            raise HTTPException(status_code=404, detail=f"Memory {memory_id} not found")

        conn.commit()
        cursor.close()
        conn.close()

        return StandardResponse(
            success=True,
            message=f"Memory {memory_id} updated successfully",
            data={
                "memory_id": memory['id'],
                "updated_at": memory['updated_at'].isoformat()
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update memory error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/memories/{memory_id}",
            response_model=StandardResponse,
            summary="Delete Memory",
            description="Remove a memory from the database")
async def delete_memory(memory_id: int):
    """Delete a memory by ID"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM memories WHERE id = %s RETURNING id", (memory_id,))
        deleted = cursor.fetchone()

        if not deleted:
            raise HTTPException(status_code=404, detail=f"Memory {memory_id} not found")

        conn.commit()
        cursor.close()
        conn.close()

        return StandardResponse(
            success=True,
            message=f"Memory {memory_id} deleted successfully",
            data={"memory_id": memory_id}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete memory error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memories/stats",
         response_model=StandardResponse,
         summary="Memory Statistics",
         description="Get database statistics and namespace breakdown")
async def memory_stats():
    """Get memory database statistics"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Total memories
        cursor.execute("SELECT COUNT(*) as total FROM memories")
        total = cursor.fetchone()['total']

        # Namespace breakdown
        cursor.execute("""
            SELECT namespace, COUNT(*) as count
            FROM memories
            GROUP BY namespace
            ORDER BY count DESC
            LIMIT 10
        """)
        namespaces = cursor.fetchall()

        # Recent activity (last 24h)
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM memories
            WHERE created_at > NOW() - INTERVAL '24 hours'
        """)
        last_24h = cursor.fetchone()['count']

        cursor.close()
        conn.close()

        return StandardResponse(
            success=True,
            message="Statistics retrieved",
            data={
                "total_memories": total,
                "last_24h": last_24h,
                "top_namespaces": [dict(n) for n in namespaces]
            }
        )

    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("GATEWAY_PORT", "8001"))

    logger.info(f"🐺 Wolf Memory Gateway starting on port {port}")
    logger.info(f"📚 Database: {DB_CONFIG['database']} @ {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    logger.info(f"📖 Documentation: http://localhost:{port}/docs")

    uvicorn.run(
        "wolf_memory_gateway:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info",
        access_log=True
    )
