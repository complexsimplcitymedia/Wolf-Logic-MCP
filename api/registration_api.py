#!/usr/bin/env python3
"""
Wolf AI Registration API
Phone (RCS) + Email dual verification with Authentik SSO integration
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, field_validator
import psycopg2
from psycopg2.extras import RealDictCursor
import secrets
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys
import os
from pathlib import Path
import logging
from datetime import datetime, timedelta
import hashlib
import re

# Add messaging directory to path for RCS client
sys.path.insert(0, str(Path(__file__).parent / "messaging"))
from rcs_client import RCSClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Wolf AI Registration API",
    description="RCS + Email verification with Authentik SSO",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten for production
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

# Email config
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@complexsimplicityai.com")

# RCS client
rcs_client = RCSClient()

def get_db():
    """Get database connection"""
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

def generate_code(length=6):
    """Generate numeric verification code"""
    return ''.join(secrets.choice(string.digits) for _ in range(length))

def generate_api_key():
    """Generate secure API key"""
    return secrets.token_urlsafe(32)

def generate_username(phone_number):
    """Generate username from phone number (last 10 digits)"""
    digits = re.sub(r'\D', '', phone_number)
    return f"user_{digits[-10:]}"

def hash_phone(phone_number):
    """Hash phone number for privacy"""
    return hashlib.sha256(phone_number.encode()).hexdigest()

# ========== Models ==========

class RegistrationRequest(BaseModel):
    phone_number: str
    email: EmailStr

    @field_validator('phone_number')
    def validate_phone(cls, v):
        # Remove all non-digits
        digits = re.sub(r'\D', '', v)
        if len(digits) < 10:
            raise ValueError('Phone number must be at least 10 digits')
        # Ensure + prefix
        if not v.startswith('+'):
            return f'+{digits}'
        return v

class VerificationRequest(BaseModel):
    phone_number: str
    email: EmailStr
    rcs_code: str
    email_code: str

class APIKeyResponse(BaseModel):
    api_key: str
    username: str
    namespace: str
    mcp_url: str

# ========== Database Setup ==========

def init_db():
    """Initialize database tables"""
    conn = get_db()
    cur = conn.cursor()

    # Pending registrations (verification codes)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pending_registrations (
            id SERIAL PRIMARY KEY,
            phone_hash VARCHAR(64) UNIQUE NOT NULL,
            phone_number VARCHAR(20) NOT NULL,
            email VARCHAR(255) NOT NULL,
            rcs_code VARCHAR(10) NOT NULL,
            email_code VARCHAR(10) NOT NULL,
            rcs_verified BOOLEAN DEFAULT FALSE,
            email_verified BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT NOW(),
            expires_at TIMESTAMP NOT NULL
        )
    """)

    # Verified users (completed registration)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS wolf_users (
            id SERIAL PRIMARY KEY,
            phone_hash VARCHAR(64) UNIQUE NOT NULL,
            phone_number VARCHAR(20) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            username VARCHAR(50) UNIQUE NOT NULL,
            namespace VARCHAR(100) NOT NULL,
            api_key VARCHAR(255) UNIQUE NOT NULL,
            authentik_user_id VARCHAR(255),
            mfa_enabled BOOLEAN DEFAULT FALSE,
            api_key_count INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT NOW(),
            last_login TIMESTAMP
        )
    """)

    # API key usage tracking
    cur.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES wolf_users(id),
            api_key VARCHAR(255) UNIQUE NOT NULL,
            device_type VARCHAR(50),
            created_at TIMESTAMP DEFAULT NOW(),
            last_used TIMESTAMP,
            revoked BOOLEAN DEFAULT FALSE
        )
    """)

    conn.commit()
    conn.close()
    logger.info("Database tables initialized")

# ========== Endpoints ==========

@app.on_event("startup")
async def startup():
    init_db()

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "wolf-registration-api"}

@app.post("/register/start")
async def start_registration(req: RegistrationRequest, background_tasks: BackgroundTasks):
    """
    Step 1: Start registration - send RCS + email verification codes
    """
    conn = get_db()
    cur = conn.cursor()

    # Check if phone already registered
    phone_hash = hash_phone(req.phone_number)
    cur.execute("SELECT id FROM wolf_users WHERE phone_hash = %s", (phone_hash,))
    if cur.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Phone number already registered")

    # Check if email already registered
    cur.execute("SELECT id FROM wolf_users WHERE email = %s", (req.email,))
    if cur.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Email already registered")

    # Generate verification codes
    rcs_code = generate_code()
    email_code = generate_code()
    expires_at = datetime.now() + timedelta(minutes=10)

    # Store pending registration
    cur.execute("""
        INSERT INTO pending_registrations
        (phone_hash, phone_number, email, rcs_code, email_code, expires_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (phone_hash)
        DO UPDATE SET
            email = EXCLUDED.email,
            rcs_code = EXCLUDED.rcs_code,
            email_code = EXCLUDED.email_code,
            expires_at = EXCLUDED.expires_at,
            rcs_verified = FALSE,
            email_verified = FALSE
    """, (phone_hash, req.phone_number, req.email, rcs_code, email_code, expires_at))

    conn.commit()
    conn.close()

    # Send RCS verification code
    try:
        rcs_message = f"Wolf AI Verification Code: {rcs_code}\n\nValid for 10 minutes.\nDo not share this code."
        rcs_client.send_message(req.phone_number, rcs_message)
        logger.info(f"RCS code sent to {req.phone_number}")
    except Exception as e:
        logger.error(f"RCS send failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to send RCS verification")

    # Send email verification code (background task)
    background_tasks.add_task(send_email_verification, req.email, email_code)

    return {
        "success": True,
        "message": "Verification codes sent via RCS and email",
        "expires_in_minutes": 10
    }

def send_email_verification(email: str, code: str):
    """Send email verification code"""
    try:
        msg = MIMEMultipart()
        msg['From'] = FROM_EMAIL
        msg['To'] = email
        msg['Subject'] = "Wolf AI - Email Verification Code"

        body = f"""
        <html>
        <body>
            <h2>Wolf AI Email Verification</h2>
            <p>Your verification code is:</p>
            <h1 style="color: #0066cc; letter-spacing: 5px;">{code}</h1>
            <p>This code will expire in 10 minutes.</p>
            <p>Do not share this code with anyone.</p>
            <hr>
            <p style="color: #666; font-size: 12px;">
                If you did not request this code, please ignore this email.
            </p>
        </body>
        </html>
        """

        msg.attach(MIMEText(body, 'html'))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)

        logger.info(f"Email verification sent to {email}")
    except Exception as e:
        logger.error(f"Email send failed: {e}")

@app.post("/register/verify", response_model=APIKeyResponse)
async def verify_registration(req: VerificationRequest):
    """
    Step 2: Verify codes and complete registration
    Returns API key after successful verification
    MFA must be configured in Authentik before API key becomes active
    """
    conn = get_db()
    cur = conn.cursor()

    phone_hash = hash_phone(req.phone_number)

    # Get pending registration
    cur.execute("""
        SELECT * FROM pending_registrations
        WHERE phone_hash = %s AND expires_at > NOW()
    """, (phone_hash,))

    pending = cur.fetchone()
    if not pending:
        conn.close()
        raise HTTPException(status_code=400, detail="No pending registration or codes expired")

    # Verify codes
    if pending['rcs_code'] != req.rcs_code:
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid RCS verification code")

    if pending['email_code'] != req.email_code:
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid email verification code")

    # Generate user credentials
    username = generate_username(req.phone_number)
    api_key = generate_api_key()
    namespace = username  # Namespace = username for isolation

    # Create user
    cur.execute("""
        INSERT INTO wolf_users
        (phone_hash, phone_number, email, username, namespace, api_key)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (phone_hash, req.phone_number, req.email, username, namespace, api_key))

    user_id = cur.fetchone()['id']

    # Track API key
    cur.execute("""
        INSERT INTO api_keys (user_id, api_key, device_type)
        VALUES (%s, %s, %s)
    """, (user_id, api_key, 'initial'))

    # Delete pending registration
    cur.execute("DELETE FROM pending_registrations WHERE phone_hash = %s", (phone_hash,))

    conn.commit()
    conn.close()

    logger.info(f"User registered: {username} ({req.email})")

    # Create Authentik user with MFA requirement
    from authentik_client import AuthentikClient
    authentik = AuthentikClient()
    authentik_user_id = authentik.create_user(username, req.email, req.phone_number)

    if authentik_user_id:
        # Add to beta users group
        authentik.add_user_to_group(authentik_user_id, "beta-users")

        # Update user record with Authentik ID
        cur.execute("""
            UPDATE wolf_users SET authentik_user_id = %s WHERE id = %s
        """, (authentik_user_id, user_id))
        conn.commit()

    conn.close()

    return APIKeyResponse(
        api_key=api_key,
        username=username,
        namespace=namespace,
        mcp_url=f"https://wolf-logic-mcp.complexsimplicityai.com/{username}"
    )

@app.get("/user/{api_key}/status")
async def get_user_status(api_key: str):
    """Check user registration and MFA status"""
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT username, email, namespace, mfa_enabled, created_at
        FROM wolf_users
        WHERE api_key = %s
    """, (api_key,))

    user = cur.fetchone()
    conn.close()

    if not user:
        raise HTTPException(status_code=404, detail="Invalid API key")

    return {
        "username": user['username'],
        "email": user['email'],
        "namespace": user['namespace'],
        "mfa_enabled": user['mfa_enabled'],
        "registered_at": user['created_at'].isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Wolf AI Registration API on port 8765")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8765,
        log_level="info"
    )
