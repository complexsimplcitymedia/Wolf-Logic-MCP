#!/usr/bin/env python3
"""
MCP Intake Stream
OAuth-secured endpoint for text ingestion, memory queries, manual embedding triggers
Separate from MCP Gateway to prevent overload and cross-stream contamination
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict, List
from datetime import datetime, timedelta
from pathlib import Path
import logging
import requests
import json
import uuid
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Wolf Intake API",
    description="OAuth-secured text stream intake for remote clients",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# OAUTH CONFIG
# ============================================================================

AUTHENTIK_URL = os.getenv("AUTHENTIK_URL", "https://authentik.complexsimplicityai.com")
AUTHENTIK_USERINFO = f"{AUTHENTIK_URL}/application/o/userinfo/"

security = HTTPBearer()

# ============================================================================
# INTAKE CONFIG
# ============================================================================

INTAKE_DIR = Path("/mnt/Wolf-code/Wolf-Ai-Enterptises/Wolf-Logic-MCP/data/client-dumps")
INTAKE_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# MODELS
# ============================================================================

class IntakeRequest(BaseModel):
    text: str = Field(..., description="Text content to ingest", min_length=1)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional metadata")

class StandardResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: str

# ============================================================================
# OAUTH VERIFICATION
# ============================================================================

async def verify_oauth_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Verify OAuth token with Authentik and return user info"""
    try:
        response = requests.get(
            AUTHENTIK_USERINFO,
            headers={"Authorization": f"Bearer {credentials.credentials}"},
            timeout=10
        )
        response.raise_for_status()
        user_info = response.json()
        
        logger.info(f"Authenticated user: {user_info.get('preferred_username', 'unknown')}")
        return user_info
        
    except requests.exceptions.RequestException as e:
        logger.error(f"OAuth verification failed: {e}")
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired authentication token"
        )

# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/", response_model=Dict[str, Any])
async def root():
    """API root"""
    return {
        "service": "MCP Intake Stream",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "intake": "/intake/stream",
            "stats": "/intake/stats"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check"""
    return HealthResponse(
        status="healthy",
        service="mcp-intake-stream",
        timestamp=datetime.now().isoformat()
    )

@app.post("/intake/stream",
          response_model=StandardResponse,
          summary="Submit Text Stream",
          description="Submit text content for processing (OAuth required)")
async def intake_stream(
    request: IntakeRequest,
    user_info: Dict[str, Any] = Depends(verify_oauth_token)
):
    """
    Accept text stream from authenticated client
    Writes to client_dump for swarm processing
    """
    try:
        # Extract user details
        username = user_info.get("preferred_username", "unknown")
        user_email = user_info.get("email", "")
        
        # Generate unique file ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_id = str(uuid.uuid4())[:8]
        filename = f"{username}_{timestamp}_{file_id}.json"
        
        # Build intake data
        intake_data = {
            "username": username,
            "user_email": user_email,
            "text": request.text,
            "metadata": request.metadata,
            "timestamp": datetime.now().isoformat(),
            "file_id": file_id
        }
        
        # Write to client_dump
        file_path = INTAKE_DIR / filename
        with open(file_path, 'w') as f:
            json.dump(intake_data, f, indent=2)
        
        logger.info(f"Intake saved: {filename} ({len(request.text)} chars)")
        
        return StandardResponse(
            success=True,
            message="Text stream accepted for processing",
            data={
                "file_id": file_id,
                "username": username,
                "text_length": len(request.text),
                "queue_file": filename
            }
        )
        
    except Exception as e:
        logger.error(f"Intake error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/intake/stats",
         response_model=StandardResponse,
         summary="Queue Statistics",
         description="Get intake queue statistics")
async def intake_stats():
    """Get intake queue statistics"""
    try:
        files = list(INTAKE_DIR.glob("*.json"))
        
        # Count files from last hour
        one_hour_ago = datetime.now() - timedelta(hours=1)
        recent_files = [
            f for f in files
            if datetime.fromtimestamp(f.stat().st_mtime) > one_hour_ago
        ]
        
        # Group by username
        by_user = {}
        for file in files:
            username = file.name.split('_')[0]
            by_user[username] = by_user.get(username, 0) + 1
        
        return StandardResponse(
            success=True,
            message="Queue statistics retrieved",
            data={
                "total_files": len(files),
                "last_hour": len(recent_files),
                "by_user": by_user,
                "queue_directory": str(INTAKE_DIR)
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
    
    # Support multiple workers for load distribution
    port = int(os.getenv("INTAKE_PORT", "8002"))
    workers = int(os.getenv("INTAKE_WORKERS", "4"))  # Default 4 workers to handle concurrent load
    
    logger.info(f"Starting MCP Intake Stream on port {port}")
    logger.info(f"Workers: {workers} (set INTAKE_WORKERS to adjust)")
    logger.info(f"Intake directory: {INTAKE_DIR}")
    logger.info(f"OAuth provider: {AUTHENTIK_URL}")
    logger.info(f"Swagger UI: http://100.110.82.181:{port}/docs")
    logger.info(f"Production: Deploy behind nginx/haproxy for multi-port load balancing")
    
    uvicorn.run(
        "mcp_intake_stream:app",
        host="0.0.0.0",
        port=port,
        workers=workers,
        reload=False,
        log_level="info",
        access_log=True
    )
