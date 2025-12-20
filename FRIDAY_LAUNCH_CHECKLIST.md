# Friday Launch Checklist - Wolf AI Beta

## ✅ Completed

### 1. MCP Server (Python)
- [x] `wolf_api_mcp.py` - MCP server wrapping REST API
- [x] 8 tools implemented (memory query/store, Neo4j, workflow)
- [x] Configuration files and launcher scripts
- [x] README documentation

### 2. Registration System
- [x] RCS + Email dual verification
- [x] Phone number as primary identity
- [x] Duplicate prevention (phone hash)
- [x] API key generation
- [x] Namespace isolation per user
- [x] Database schema (pending_registrations, wolf_users, api_keys)

### 3. Authentik Integration
- [x] User provisioning API client
- [x] MFA enforcement policy
- [x] Beta users group management
- [x] MFA status checking
- [x] Enrollment link generation

### 4. REST API
- [x] Wolf AI REST API matching mcp-api.yaml spec
- [x] API key authentication middleware
- [x] Namespace-isolated memory access
- [x] Neo4j integration (read + write)
- [x] Memory semantic search
- [x] Tools/Resources/Prompts endpoints

### 5. Docker Deployment
- [x] Registration API Dockerfile
- [x] Wolf REST API Dockerfile
- [x] Docker Compose configuration
- [x] Network isolation

## 🔧 Required Before Launch

### 1. Environment Variables
Create `.env` file in `/mnt/Wolf-code/Wolf-Ai-Enterptises/api/`:
```bash
AUTHENTIK_API_TOKEN=<get_from_authentik>
SMTP_USER=<gmail_address>
SMTP_PASSWORD=<gmail_app_password>
NEO4J_PASSWORD=<neo4j_password>
```

### 2. RCS Configuration
Ensure RCS client is configured:
```bash
cd /mnt/Wolf-code/Wolf-Ai-Enterptises/messaging
python rcs_client.py setup \
  --client-id <melrose_client_id> \
  --client-secret <melrose_secret> \
  --bot-id <bot_id>
```

### 3. Authentik Setup
1. Create API token in Authentik UI
2. Create "beta-users" group
3. Run MFA enforcement setup:
```bash
cd /mnt/Wolf-code/Wolf-Ai-Enterptises/api
source ~/anaconda3/bin/activate messiah
python authentik_client.py
```

### 4. Database Initialization
```bash
# Registration API will auto-create tables on first run
# OR manually:
source ~/anaconda3/bin/activate messiah
python -c "from registration_api import init_db; init_db()"
```

### 5. Deploy Services
```bash
cd /mnt/Wolf-code/Wolf-Ai-Enterptises/api
docker compose -f docker-compose.wolf-api.yml up -d
```

### 6. Update Caddyfile
Add to Caddyfile on Wolfbook (100.110.82.245):
```caddy
# Registration API
register.complexsimplicityai.com {
  import custom_wildcard_tls
  import security_headers
  reverse_proxy http://100.110.82.181:8765
}

# Wolf REST API (already exists as wolf-logic-mcp.complexsimplicityai.com)
# Update to port 3000 instead of 8765
```

Reload Caddy:
```bash
ssh -i ~/.ssh/id_ed25519 complexsimplicity@100.110.82.245 "sudo systemctl reload caddy"
```

## 🧪 Testing Flow

### 1. Registration
```bash
curl -X POST https://register.complexsimplicityai.com/register/start \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+1234567890",
    "email": "test@example.com"
  }'
```

Check phone for RCS code and email for email code.

```bash
curl -X POST https://register.complexsimplicityai.com/register/verify \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+1234567890",
    "email": "test@example.com",
    "rcs_code": "123456",
    "email_code": "654321"
  }'
```

Response includes API key and username.

### 2. MFA Enrollment
User must configure MFA in Authentik before API access:
1. Login to auth.complexsimplicityai.com
2. Configure TOTP/FIDO2/Biometric
3. Complete enrollment

### 3. Test API Access
```bash
curl https://wolf-logic-mcp.complexsimplicityai.com/mcp/tools/list \
  -H "X-API-Key: <api_key_from_registration>"
```

### 4. Test MCP Server
Add to Claude Desktop config:
```json
{
  "mcpServers": {
    "wolf-api": {
      "command": "python",
      "args": [
        "/mnt/Wolf-code/Wolf-Ai-Enterptises/mcp-servers/wolf_api_mcp.py"
      ],
      "env": {
        "WOLF_API_URL": "https://wolf-logic-mcp.complexsimplicityai.com",
        "WOLF_API_KEY": "<api_key>"
      }
    }
  }
}
```

## 📱 Android App Integration

### Registration Flow
1. User enters phone + email in app
2. App calls `/register/start`
3. User enters codes from RCS + email
4. App calls `/register/verify`
5. App stores API key locally
6. User completes MFA enrollment in WebView (auth.complexsimplicityai.com)
7. App can now make authenticated requests

### API Calls
```kotlin
// Example
val response = httpClient.get("https://wolf-logic-mcp.complexsimplicityai.com/mcp/memory/query") {
    header("X-API-Key", apiKey)
    setBody(MemoryQueryRequest(
        query = "authentication implementation",
        namespace = "general",
        limit = 10
    ))
}
```

## 🚨 Security Notes

- Phone numbers are hashed (SHA-256) before storage
- API keys are 32-byte URL-safe tokens
- MFA required before API access enabled
- Namespace isolation enforced at API level
- Read-only Neo4j queries only
- CORS configured (tighten for production)

## 📊 Monitoring

Check service status:
```bash
docker ps | grep wolf
docker logs wolf-registration-api
docker logs wolf-rest-api
```

Check database:
```bash
PGPASSWORD=wolflogic2024 psql -h 100.110.82.181 -p 5433 -U wolf -d wolf_logic -c "SELECT COUNT(*) FROM wolf_users;"
```

Check Authentik users:
```bash
curl https://auth.complexsimplicityai.com/api/v3/core/users/ \
  -H "Authorization: Bearer <authentik_token>"
```

## 🎯 Friday Success Criteria

- [ ] User can register via RCS + email
- [ ] MFA enforcement works in Authentik
- [ ] API key authentication works
- [ ] Memory operations isolated by namespace
- [ ] MCP server connects to REST API
- [ ] Claude Desktop can use MCP tools
- [ ] Android app can authenticate and query memory

## 📞 Support Contacts

If issues arise:
1. Check Docker logs
2. Verify environment variables
3. Test each component independently
4. Check Caddy routing
5. Verify Tailscale connectivity

---

**Built for Friday, December 20, 2025**
**Wolf AI Enterprises - Beta Launch**
