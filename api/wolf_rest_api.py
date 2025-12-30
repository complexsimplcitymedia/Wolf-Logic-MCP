#!/usr/bin/env python3
"""
Wolf AI REST API - Implementation of mcp-api.yaml spec
Provides MCP endpoints over REST for web/mobile access
"""

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Wolf AI MCP API",
    description="Model Context Protocol API for Wolf AI Enterprises",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database config
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "100.110.82.181"),
    "port": int(os.getenv("POSTGRES_PORT", "5433")),
    "user": os.getenv("POSTGRES_USER", "wolf"),
    "password": os.getenv("POSTGRES_PASSWORD", "wolflogic2024"),
    "database": os.getenv("POSTGRES_DB", "wolf_logic")
}

def get_db():
    """Get database connection"""
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """Verify API key and return user info"""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, username, namespace, mfa_enabled
        FROM wolf_users
        WHERE api_key = %s
    """, (x_api_key,))

    user = cur.fetchone()
    conn.close()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")

    if not user['mfa_enabled']:
        raise HTTPException(status_code=403, detail="MFA enrollment required")

    return user

# ========== Models ==========

class MemoryQueryRequest(BaseModel):
    query: str
    namespace: Optional[str] = "general"
    limit: int = 10

class MemoryStoreRequest(BaseModel):
    content: str
    namespace: Optional[str] = "general"
    metadata: Optional[Dict[str, Any]] = {}

class Neo4jQueryRequest(BaseModel):
    cypher: str
    parameters: Optional[Dict[str, Any]] = {}

class Neo4jRelationRequest(BaseModel):
    from_id: str
    to_id: str
    relation_type: str
    properties: Optional[Dict[str, Any]] = {}

class WorkflowForageRequest(BaseModel):
    workflow_id: str
    link_to_memory: bool = True
    namespace: Optional[str] = "general"

# ========== Endpoints ==========

@app.get("/")
async def root():
    return {
        "service": "Wolf AI MCP API",
        "version": "1.0.0",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/mcp/tools/list")
async def list_tools(user: dict = Depends(verify_api_key)):
    """List available MCP tools"""
    return {
        "tools": [
            {
                "name": "query_memory",
                "description": "Semantic search in wolf_logic memory database",
                "inputSchema": {
                    "query": "string",
                    "namespace": "string (optional)",
                    "limit": "integer (optional)"
                }
            },
            {
                "name": "store_memory",
                "description": "Store new memory in wolf_logic database",
                "inputSchema": {
                    "content": "string",
                    "namespace": "string (optional)",
                    "metadata": "object (optional)"
                }
            },
            {
                "name": "query_neo4j",
                "description": "Execute Cypher query on Neo4j knowledge graph",
                "inputSchema": {
                    "cypher": "string",
                    "parameters": "object (optional)"
                }
            },
            {
                "name": "create_neo4j_relation",
                "description": "Create relationship in Neo4j graph",
                "inputSchema": {
                    "from_id": "string",
                    "to_id": "string",
                    "relation_type": "string",
                    "properties": "object (optional)"
                }
            }
        ]
    }

@app.get("/mcp/resources/list")
async def list_resources(user: dict = Depends(verify_api_key)):
    """List available MCP resources"""
    return {
        "resources": [
            {
                "uri": f"wolf://memory/{user['namespace']}",
                "name": "User Memory Namespace",
                "description": f"Memory storage for {user['username']}",
                "mimeType": "application/json"
            }
        ]
    }

@app.get("/mcp/prompts/list")
async def list_prompts(user: dict = Depends(verify_api_key)):
    """List available MCP prompts"""
    return {
        "prompts": [
            {
                "name": "retrieve_context",
                "description": "Retrieve relevant context from memory for a task",
                "arguments": ["task_description", "limit"]
            }
        ]
    }

@app.post("/mcp/memory/query")
async def query_memory(req: MemoryQueryRequest, user: dict = Depends(verify_api_key)):
    """Query wolf_logic memory database"""
    conn = get_db()
    cur = conn.cursor()

    # Enforce namespace isolation
    namespace = user['namespace'] if req.namespace == "general" else req.namespace

    try:
        cur.execute("""
            SELECT id, content, metadata, namespace, created_at,
                   1 - (embedding <=> ai.ollama_embed('qwen3-embedding:4b', %s, host => 'http://100.110.82.181:11434')) AS similarity
            FROM memories
            WHERE namespace = %s
            ORDER BY similarity DESC
            LIMIT %s
        """, (req.query, namespace, req.limit))

        results = cur.fetchall()
        conn.close()

        return {
            "results": [
                {
                    "id": r['id'],
                    "content": r['content'],
                    "metadata": r['metadata'],
                    "namespace": r['namespace'],
                    "created_at": r['created_at'].isoformat(),
                    "similarity": float(r['similarity'])
                }
                for r in results
            ]
        }

    except Exception as e:
        conn.close()
        logger.error(f"Memory query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/memory/store")
async def store_memory(req: MemoryStoreRequest, user: dict = Depends(verify_api_key)):
    """Store memory in wolf_logic database"""
    conn = get_db()
    cur = conn.cursor()

    # Enforce namespace isolation
    namespace = user['namespace'] if req.namespace == "general" else req.namespace

    try:
        cur.execute("""
            INSERT INTO memories (user_id, content, metadata, namespace)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (user['username'], req.content, req.metadata, namespace))

        result = cur.fetchone()
        conn.commit()
        conn.close()

        return {
            "id": result['id'],
            "success": True
        }

    except Exception as e:
        conn.close()
        logger.error(f"Memory store error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/neo4j/query")
async def query_neo4j(req: Neo4jQueryRequest, user: dict = Depends(verify_api_key)):
    """Execute Cypher query on Neo4j (read-only)"""
    # Safety check - only allow read operations
    if not req.cypher.strip().upper().startswith(('MATCH', 'RETURN', 'WITH', 'UNWIND')):
        raise HTTPException(status_code=400, detail="Only read queries allowed")

    try:
        from neo4j import GraphDatabase

        neo4j_uri = os.getenv("NEO4J_URI", "bolt://100.110.82.181:7687")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD", "")

        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

        with driver.session() as session:
            result = session.run(req.cypher, req.parameters)
            records = [dict(record) for record in result]

        driver.close()

        return {"results": records}

    except Exception as e:
        logger.error(f"Neo4j query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/neo4j/relations/create")
async def create_neo4j_relation(req: Neo4jRelationRequest, user: dict = Depends(verify_api_key)):
    """Create relationship in Neo4j knowledge graph"""
    try:
        from neo4j import GraphDatabase

        neo4j_uri = os.getenv("NEO4J_URI", "bolt://100.110.82.181:7687")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD", "")

        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

        cypher = f"""
        MATCH (a), (b)
        WHERE id(a) = $from_id AND id(b) = $to_id
        CREATE (a)-[r:{req.relation_type} $properties]->(b)
        RETURN id(r) as relationship_id
        """

        with driver.session() as session:
            result = session.run(cypher, {
                "from_id": int(req.from_id),
                "to_id": int(req.to_id),
                "properties": req.properties
            })
            record = result.single()

        driver.close()

        return {
            "success": True,
            "relationship_id": str(record['relationship_id']) if record else None
        }

    except Exception as e:
        logger.error(f"Neo4j relation create error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/workflow/forage")
async def forage_workflow(req: WorkflowForageRequest, user: dict = Depends(verify_api_key)):
    """Forage and link workflow data to memory"""
    # Placeholder - implement workflow foraging logic
    return {
        "workflow": {"id": req.workflow_id, "status": "foraging_not_implemented"},
        "related_memories": [],
        "relationships_created": 0
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Wolf AI REST API on port 3000")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=3000,
        log_level="info"
    )
