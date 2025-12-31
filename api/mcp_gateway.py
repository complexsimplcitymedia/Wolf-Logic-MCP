#!/usr/bin/env python3
"""
Wolf MCP Gateway - Unified REST API for all MCP servers
Production-ready with Swagger docs, health checks, and full tool exposure
"""

from fastapi import FastAPI, HTTPException, Query, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict, List
from datetime import datetime
from pathlib import Path
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import base64
import os
import json
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Wolf MCP Gateway API",
    description="Unified REST API exposing all MCP server tools - Postgres, Email, WordPress, and Registry",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS for Android app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten for production
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

def get_db_connection():
    """Get PostgreSQL connection with RealDictCursor"""
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

# ============================================================================
# EMAIL CONFIG
# ============================================================================

EMAIL_CONFIG = {
    "from_email": os.getenv('EMAIL_FROM', ''),
    "smtp_server": os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
    "smtp_port": int(os.getenv('SMTP_PORT', '587')),
    "smtp_user": os.getenv('SMTP_USER', ''),
    "smtp_password": os.getenv('SMTP_PASSWORD', '')
}

# ============================================================================
# WORDPRESS CONFIG
# ============================================================================

WP_URL = os.getenv("WORDPRESS_URL", "http://localhost:8082")
WP_USER = os.getenv("WORDPRESS_USER", "")
WP_PASSWORD = os.getenv("WORDPRESS_PASSWORD", "")

auth_string = f"{WP_USER}:{WP_PASSWORD}"
auth_b64 = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')

WP_HEADERS = {
    "Authorization": f"Basic {auth_b64}",
    "Content-Type": "application/json"
}

# ============================================================================
# AUTHENTIK OAUTH CONFIG
# ============================================================================

AUTHENTIK_URL = os.getenv("AUTHENTIK_URL", "https://authentik.complexsimplicityai.com")
AUTHENTIK_TOKEN_URL = f"{AUTHENTIK_URL}/application/o/token/"
AUTHENTIK_USERINFO_URL = f"{AUTHENTIK_URL}/application/o/userinfo/"

security = HTTPBearer()

async def verify_oauth_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify OAuth token with Authentik"""
    token = credentials.credentials
    
    try:
        response = requests.get(
            AUTHENTIK_USERINFO_URL,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
        
        user_info = response.json()
        return user_info  # Contains username, email, etc.
        
    except Exception as e:
        logger.error(f"OAuth verification error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")

# ============================================================================
# INTAKE CONFIG
# ============================================================================

INTAKE_DIR = Path("/mnt/Wolf-code/Wolf-Ai-Enterptises/data/client_dump")
INTAKE_DIR.mkdir(parents=True, exist_ok=True)

# Conversations directory
CONVERSATION_DIR = Path("/mnt/Wolf-code/Wolf-Ai-Enterptises/data/conversations")
CONVERSATION_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class HealthResponse(BaseModel):
    status: str
    service: str
    database: str
    timestamp: str

class QueryRequest(BaseModel):
    sql: str = Field(..., description="SELECT query to execute")
    limit: Optional[int] = Field(100, description="Maximum rows to return")

class SearchMemoriesRequest(BaseModel):
    query: Optional[str] = Field(None, description="Text search query")
    namespace: Optional[str] = Field(None, description="Filter by namespace")
    limit: int = Field(20, description="Maximum results")

class VectorSearchRequest(BaseModel):
    query: str = Field(..., description="Semantic search query")
    limit: int = Field(10, description="Maximum results")

class EmailRequest(BaseModel):
    to: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body (plain text)")
    cc: Optional[str] = Field(None, description="CC recipients (comma-separated)")
    bcc: Optional[str] = Field(None, description="BCC recipients (comma-separated)")

class WordPressPostRequest(BaseModel):
    title: str = Field(..., description="Post title")
    content: str = Field(..., description="Post content (HTML)")
    status: str = Field("draft", description="Post status: draft, publish, pending")
    categories: Optional[List[int]] = Field(None, description="Category IDs")
    tags: Optional[List[int]] = Field(None, description="Tag IDs")

class StandardResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class IntakeRequest(BaseModel):
    text: str = Field(..., description="Text content to ingest")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata")

class ConversationThread(BaseModel):
    title: Optional[str] = Field(None, description="Conversation title/summary")
    messages: List[Dict[str, Any]] = Field(..., description="Array of conversation messages")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Conversation metadata (source, app, etc)")
    source: str = Field(..., description="Client source (android, ios, web, desktop)")

# ============================================================================
# HEALTH & ROOT
# ============================================================================

@app.get("/", response_model=Dict[str, Any])
async def root():
    """API root - service information"""
    return {
        "service": "Wolf MCP Gateway",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "postgres": "/mcp/postgres/*",
            "email": "/mcp/email/*",
            "wordpress": "/mcp/wordpress/*",
            "intake": "/mcp/intake/*",
            "conversations": "/mcp/conversations/*"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check with database connectivity test"""
    db_status = "healthy"
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"

    return HealthResponse(
        status="healthy" if db_status == "healthy" else "degraded",
        service="mcp-gateway",
        database=db_status,
        timestamp=datetime.now().isoformat()
    )

# ============================================================================
# POSTGRES MCP TOOLS
# ============================================================================

@app.post("/mcp/postgres/query",
          response_model=StandardResponse,
          summary="Execute SQL Query",
          description="Execute read-only SQL SELECT query on wolf_logic database")
async def postgres_query(request: QueryRequest):
    """Execute read-only SQL query (SELECT only)"""
    try:
        # Safety check - only allow SELECT
        if not request.sql.strip().upper().startswith("SELECT"):
            raise HTTPException(status_code=400, detail="Only SELECT queries allowed")

        # Add LIMIT if not present
        sql = request.sql
        if "LIMIT" not in sql.upper():
            sql = f"{sql} LIMIT {request.limit}"

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(sql)
        results = cursor.fetchall()
        cursor.close()
        conn.close()

        return StandardResponse(
            success=True,
            message=f"Query returned {len(results)} rows",
            data={"rows": results, "count": len(results)}
        )

    except Exception as e:
        logger.error(f"Query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mcp/postgres/tables",
         response_model=StandardResponse,
         summary="List Database Tables",
         description="List all tables in wolf_logic database with sizes")
async def postgres_list_tables():
    """List all database tables with row counts and sizes"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
            FROM pg_tables
            WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
            ORDER BY schemaname, tablename
        """)

        tables = cursor.fetchall()
        cursor.close()
        conn.close()

        return StandardResponse(
            success=True,
            message=f"Found {len(tables)} tables",
            data={"tables": tables, "count": len(tables)}
        )

    except Exception as e:
        logger.error(f"List tables error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mcp/postgres/table/{table_name}",
         response_model=StandardResponse,
         summary="Describe Table Schema",
         description="Get detailed column information for a table")
async def postgres_describe_table(table_name: str):
    """Get table schema and column information"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                column_name,
                data_type,
                character_maximum_length,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position
        """, (table_name,))

        columns = cursor.fetchall()
        cursor.close()
        conn.close()

        if not columns:
            raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")

        return StandardResponse(
            success=True,
            message=f"Table '{table_name}' has {len(columns)} columns",
            data={"table": table_name, "columns": columns}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Describe table error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/postgres/search-memories",
          response_model=StandardResponse,
          summary="Search Memories",
          description="Search memories by content or namespace (text search)")
async def postgres_search_memories(request: SearchMemoriesRequest):
    """Search memories by content or namespace"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        conditions = []
        params = []

        if request.query:
            conditions.append("content ILIKE %s")
            params.append(f"%{request.query}%")

        if request.namespace:
            conditions.append("namespace = %s")
            params.append(request.namespace)

        where_clause = " AND ".join(conditions) if conditions else "TRUE"
        params.append(request.limit)

        sql = f"""
            SELECT id, namespace, content, metadata, created_at, updated_at
            FROM memories
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT %s
        """

        cursor.execute(sql, params)
        results = cursor.fetchall()
        cursor.close()
        conn.close()

        return StandardResponse(
            success=True,
            message=f"Found {len(results)} memories",
            data={"memories": results, "count": len(results)}
        )

    except Exception as e:
        logger.error(f"Search memories error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mcp/postgres/stats",
         response_model=StandardResponse,
         summary="Database Statistics",
         description="Get memory database statistics and counts")
async def postgres_stats():
    """Get database statistics"""
    try:
        conn = get_db_connection()
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

        # Recent activity
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
            message="Database statistics retrieved",
            data={
                "total_memories": total,
                "last_24h": last_24h,
                "top_namespaces": namespaces
            }
        )

    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# EMAIL MCP TOOLS
# ============================================================================

@app.post("/mcp/email/send",
          response_model=StandardResponse,
          summary="Send Email",
          description="Send email via SMTP (supports Gmail, Outlook, custom servers)")
async def email_send(request: EmailRequest):
    """Send an email via SMTP"""

    # Validate configuration
    if not all([EMAIL_CONFIG['from_email'], EMAIL_CONFIG['smtp_user'], EMAIL_CONFIG['smtp_password']]):
        raise HTTPException(
            status_code=503,
            detail="Email service not configured. Set EMAIL_FROM, SMTP_USER, SMTP_PASSWORD environment variables."
        )

    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['from_email']
        msg['To'] = request.to
        msg['Subject'] = request.subject

        if request.cc:
            msg['Cc'] = request.cc
        if request.bcc:
            msg['Bcc'] = request.bcc

        # Attach body
        msg.attach(MIMEText(request.body, 'plain'))

        # Send email
        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
            server.starttls()
            server.login(EMAIL_CONFIG['smtp_user'], EMAIL_CONFIG['smtp_password'])

            recipients = [request.to]
            if request.cc:
                recipients.extend([e.strip() for e in request.cc.split(',')])
            if request.bcc:
                recipients.extend([e.strip() for e in request.bcc.split(',')])

            server.send_message(msg, from_addr=EMAIL_CONFIG['from_email'], to_addrs=recipients)

        return StandardResponse(
            success=True,
            message=f"Email sent successfully to {request.to}",
            data={
                "from": EMAIL_CONFIG['from_email'],
                "to": request.to,
                "subject": request.subject
            }
        )

    except Exception as e:
        logger.error(f"Email send error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# WORDPRESS MCP TOOLS
# ============================================================================

def wp_request(endpoint: str, method: str = "GET", data: dict = None) -> dict:
    """Make request to WordPress REST API"""
    url = f"{WP_URL}/wp-json/wp/v2/{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, headers=WP_HEADERS)
        elif method == "POST":
            response = requests.post(url, headers=WP_HEADERS, json=data)
        elif method == "PUT":
            response = requests.put(url, headers=WP_HEADERS, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=WP_HEADERS)
        else:
            return {"error": f"Unsupported method: {method}"}

        response.raise_for_status()
        return response.json() if response.text else {"success": True}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

@app.get("/mcp/wordpress/posts",
         response_model=StandardResponse,
         summary="List WordPress Posts",
         description="List all WordPress posts with optional filtering")
async def wordpress_list_posts(
    per_page: int = Query(10, description="Posts per page"),
    status: str = Query("publish", description="Post status filter")
):
    """List WordPress posts"""
    try:
        result = wp_request(f"posts?per_page={per_page}&status={status}")

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return StandardResponse(
            success=True,
            message=f"Retrieved {len(result) if isinstance(result, list) else 0} posts",
            data={"posts": result}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"WordPress list posts error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mcp/wordpress/posts/{post_id}",
         response_model=StandardResponse,
         summary="Get WordPress Post",
         description="Get a specific WordPress post by ID")
async def wordpress_get_post(post_id: int):
    """Get a specific WordPress post"""
    try:
        result = wp_request(f"posts/{post_id}")

        if "error" in result:
            raise HTTPException(status_code=404, detail=f"Post {post_id} not found")

        return StandardResponse(
            success=True,
            message=f"Retrieved post {post_id}",
            data={"post": result}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"WordPress get post error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/wordpress/posts",
          response_model=StandardResponse,
          summary="Create WordPress Post",
          description="Create a new WordPress post")
async def wordpress_create_post(request: WordPressPostRequest):
    """Create a new WordPress post"""
    try:
        data = {
            "title": request.title,
            "content": request.content,
            "status": request.status
        }

        if request.categories:
            data["categories"] = request.categories
        if request.tags:
            data["tags"] = request.tags

        result = wp_request("posts", method="POST", data=data)

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return StandardResponse(
            success=True,
            message=f"Post created successfully (ID: {result.get('id', 'unknown')})",
            data={"post": result}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"WordPress create post error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# INTAKE MCP TOOLS
# ============================================================================

@app.post("/mcp/intake/stream",
          response_model=StandardResponse,
          summary="Intake Text Stream",
          description="Receive text stream from remote clients (requires Authentik OAuth)")
async def intake_stream(
    request: IntakeRequest,
    user_info: dict = Depends(verify_oauth_token)
):
    """
    Receive text stream from authenticated clients
    - Requires Authentik OAuth token
    - Writes to client_dump/{username}_{timestamp}_{uuid}.json
    - Queued for swarm processing (categorization + sentiment)
    """
    try:
        username = user_info.get("preferred_username", user_info.get("sub", "unknown"))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_id = str(uuid.uuid4())[:8]
        
        filename = f"{username}_{timestamp}_{file_id}.json"
        filepath = INTAKE_DIR / filename
        
        intake_data = {
            "username": username,
            "user_email": user_info.get("email"),
            "text": request.text,
            "metadata": request.metadata or {},
            "timestamp": datetime.now().isoformat(),
            "file_id": file_id
        }
        
        with open(filepath, 'w') as f:
            json.dump(intake_data, f, indent=2)
        
        logger.info(f"[INTAKE] Received stream from {username}: {len(request.text)} chars -> {filename}")
        
        return StandardResponse(
            success=True,
            message=f"Text intake successful - queued for swarm processing",
            data={
                "file_id": file_id,
                "filename": filename,
                "username": username,
                "text_length": len(request.text),
                "queue_path": str(filepath)
            }
        )
        
    except Exception as e:
        logger.error(f"Intake error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mcp/intake/stats",
         response_model=StandardResponse,
         summary="Intake Statistics",
         description="Get intake queue statistics")
async def intake_stats():
    """Get intake queue statistics"""
    try:
        files = list(INTAKE_DIR.glob("*.json"))
        
        # Count by user
        user_counts = {}
        for f in files:
            username = f.stem.split('_')[0]
            user_counts[username] = user_counts.get(username, 0) + 1
        
        # Recent intakes (last hour)
        hour_ago = datetime.now().timestamp() - 3600
        recent = [f for f in files if f.stat().st_mtime > hour_ago]
        
        return StandardResponse(
            success=True,
            message="Intake statistics retrieved",
            data={
                "total_queued": len(files),
                "last_hour": len(recent),
                "by_user": user_counts,
                "queue_path": str(INTAKE_DIR)
            }
        )
        
    except Exception as e:
        logger.error(f"Intake stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# CONVERSATION THREADS
# ============================================================================

@app.post("/mcp/conversations/submit",
          response_model=StandardResponse,
          summary="Submit Conversation Thread",
          description="Submit full conversation thread for ingestion and analysis")
async def submit_conversation_thread(
    request: ConversationThread,
    user_info: dict = Depends(verify_oauth_token)
):
    """
    Submit a full conversation thread from any client
    - Validates message structure
    - Stores with rich metadata
    - Queues for ingestion agent processing
    """
    try:
        username = user_info.get("preferred_username", user_info.get("sub", "unknown"))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        thread_id = str(uuid.uuid4())[:8]
        
        # Build filename: conversation_{source}_{username}_{timestamp}_{id}.json
        filename = f"conversation_{request.source}_{username}_{timestamp}_{thread_id}.json"
        filepath = CONVERSATION_DIR / filename
        
        # Validate messages structure
        if not request.messages or len(request.messages) == 0:
            raise HTTPException(status_code=400, detail="Conversation must contain at least one message")
        
        # Build conversation data
        conversation_data = {
            "thread_id": thread_id,
            "username": username,
            "user_email": user_info.get("email"),
            "source": request.source,
            "title": request.title or f"Conversation {timestamp}",
            "messages": request.messages,
            "message_count": len(request.messages),
            "metadata": request.metadata or {},
            "submitted_at": datetime.now().isoformat(),
            "status": "queued"
        }
        
        # Write to conversation directory
        with open(filepath, 'w') as f:
            json.dump(conversation_data, f, indent=2)
        
        logger.info(f"[CONVERSATION] {username} ({request.source}): {len(request.messages)} messages -> {filename}")
        
        return StandardResponse(
            success=True,
            message=f"Conversation thread accepted - {len(request.messages)} messages queued for processing",
            data={
                "thread_id": thread_id,
                "filename": filename,
                "username": username,
                "source": request.source,
                "message_count": len(request.messages),
                "queue_path": str(filepath)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Conversation submission error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mcp/conversations/list",
         response_model=StandardResponse,
         summary="List User Conversations",
         description="List conversation threads for authenticated user")
async def list_user_conversations(
    user_info: dict = Depends(verify_oauth_token),
    limit: int = Query(20, description="Maximum conversations to return")
):
    """List conversations for the authenticated user"""
    try:
        username = user_info.get("preferred_username", user_info.get("sub", "unknown"))
        
        # Find all conversations for this user (pattern: conversation_{source}_{username}_*.json)
        pattern = f"conversation_*_{username}_*.json"
        user_conversations = list(CONVERSATION_DIR.glob(pattern))
        user_conversations.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        user_conversations = user_conversations[:limit]
        
        # Load conversation metadata
        conversations = []
        for conv_file in user_conversations:
            try:
                with open(conv_file, 'r') as f:
                    conv_data = json.load(f)
                    conversations.append({
                        "thread_id": conv_data.get("thread_id"),
                        "title": conv_data.get("title"),
                        "source": conv_data.get("source"),
                        "message_count": conv_data.get("message_count"),
                        "submitted_at": conv_data.get("submitted_at"),
                        "status": conv_data.get("status", "unknown"),
                        "filename": conv_file.name
                    })
            except Exception as e:
                logger.warning(f"Failed to load {conv_file}: {e}")
                continue
        
        return StandardResponse(
            success=True,
            message=f"Found {len(conversations)} conversations for {username}",
            data={
                "username": username,
                "conversations": conversations,
                "count": len(conversations)
            }
        )
        
    except Exception as e:
        logger.error(f"List conversations error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mcp/conversations/{thread_id}",
         response_model=StandardResponse,
         summary="Get Conversation Thread",
         description="Retrieve full conversation thread by ID")
async def get_conversation_thread(
    thread_id: str,
    user_info: dict = Depends(verify_oauth_token)
):
    """Get full conversation thread by thread_id"""
    try:
        username = user_info.get("preferred_username", user_info.get("sub", "unknown"))
        
        # Find conversation file with this thread_id
        pattern = f"conversation_*_{username}_*_{thread_id}.json"
        matches = list(CONVERSATION_DIR.glob(pattern))
        
        if not matches:
            raise HTTPException(status_code=404, detail=f"Conversation {thread_id} not found")
        
        # Load conversation data
        with open(matches[0], 'r') as f:
            conversation = json.load(f)
        
        # Verify ownership
        if conversation.get("username") != username:
            raise HTTPException(status_code=403, detail="Access denied to this conversation")
        
        return StandardResponse(
            success=True,
            message=f"Retrieved conversation {thread_id}",
            data={"conversation": conversation}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get conversation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mcp/conversations/stats",
         response_model=StandardResponse,
         summary="Conversation Statistics",
         description="Get conversation intake statistics")
async def conversation_stats():
    """Get conversation statistics across all users"""
    try:
        files = list(CONVERSATION_DIR.glob("conversation_*.json"))
        
        # Count by user and source
        by_user = {}
        by_source = {}
        total_messages = 0
        
        for conv_file in files:
            try:
                with open(conv_file, 'r') as f:
                    data = json.load(f)
                    username = data.get("username", "unknown")
                    source = data.get("source", "unknown")
                    msg_count = data.get("message_count", 0)
                    
                    by_user[username] = by_user.get(username, 0) + 1
                    by_source[source] = by_source.get(source, 0) + 1
                    total_messages += msg_count
            except:
                continue
        
        # Recent conversations (last 24h)
        day_ago = datetime.now().timestamp() - 86400
        recent = [f for f in files if f.stat().st_mtime > day_ago]
        
        return StandardResponse(
            success=True,
            message="Conversation statistics retrieved",
            data={
                "total_conversations": len(files),
                "total_messages": total_messages,
                "last_24h": len(recent),
                "by_user": by_user,
                "by_source": by_source,
                "queue_path": str(CONVERSATION_DIR)
            }
        )
        
    except Exception as e:
        logger.error(f"Conversation stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    # Get port from environment or use default
    port = int(os.getenv("GATEWAY_PORT", "8001"))

    logger.info(f"Starting Wolf MCP Gateway on port {port}")
    logger.info(f"Swagger UI: http://localhost:{port}/docs")

    uvicorn.run(
        "mcp_gateway:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Disable in production
        log_level="info",
        access_log=True
    )
