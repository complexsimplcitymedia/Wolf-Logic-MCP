# Client Memory Layer Configuration

## Architecture Overview

Wolf Logic uses a hub-and-spoke memory architecture:

```
                    +------------------------+
                    |  100.110.82.181 (HUB)  |
                    |  The Librarian         |
                    |  PostgreSQL 18.1:5433  |
                    |  wolf_logic database   |
                    +------------------------+
                              ^
              +---------------+---------------+
              |               |               |
       [SUBMIT]          [SUBMIT]          [SUBMIT]
              |               |               |
    +---------+     +---------+     +---------+
    | Desktop |     | Android |     | macOS   |
    | Client  |     | Client  |     | Client  |
    +---------+     +---------+     +---------+
         |               |               |
    [LOCAL DB]      [NO LOCAL]      [LOCAL DB]
    wolf_logic_     (API only)      wolf_logic_
    local                           local
         |                               |
    [QUERY]                         [QUERY]
    (local)                         (local)
```

## Key Principles

1. **All data flows TO 181** - Clients submit text/files to the hub
2. **Processing happens on 181** - Vectorization via qwen3-embedding:4b (2560 dims)
3. **Desktop clients sync FROM 181** - Local PostgreSQL replicas for fast reads
4. **Android clients use API only** - No local database, query through API
5. **Clients ONLY query local** - Never hit 181 for routine reads

## Server-Side Components (181)

### PostgreSQL Database

```bash
# Connection details
Host: 100.110.82.181
Port: 5433
Database: wolf_logic
User: wolf
Password: wolflogic2024

# Stats
Memories: 97,000+
Vectorized entries: 402,000+
Embedding dimensions: 2560
```

### MCP Intake API

```bash
# Endpoint for client submissions
URL: http://100.110.82.181:8002/intake/stream
Method: POST
Auth: OAuth Bearer token

# Request format
{
  "text": "content to ingest",
  "metadata": {
    "source": "client_name",
    "device": "device_info"
  }
}
```

### Swarm Intake Processor

```bash
# Service that processes incoming submissions
Location: /mnt/Wolf-code/Wolf-Ai-Enterptises/Wolf-Logic-MCP/writers/ingest/
Service: swarm-intake.service
Queue directory: /data/client-dumps/
```

### Vectorizer (pgai)

```bash
# Automatic vectorization of new memories
Model: qwen3-embedding:4b
Dimensions: 2560
Scheduler: pgai vectorizer
Table: memories_embedding
```

## Client Types

### Desktop Clients (Linux/macOS)

**Documentation:** `/macro-os/client/`

Desktop clients maintain a local PostgreSQL replica:

```bash
# Local database
Database: wolf_logic_local
Sync: Every 5 minutes from 181
Mode: Read-only replica
Purpose: Fast local queries
```

**Setup requirements:**
- Miniconda3 with Python 3.12
- Local PostgreSQL 16+
- psycopg2, ollama, requests, pydantic
- Cron job for sync

### Android Clients

**Documentation:** `/android-client/`

Android clients are thin - no local database:

```
Submit → MCP Intake API → Processing → Done
```

**Components:**
- Wolf Logic APK (wolflogic-apk/)
- Termux scripts (optional)
- OAuth via Authentik

### macOS Clients

**Documentation:** `/macos-client/`

Same as Linux desktop clients, with Homebrew for PostgreSQL.

## Sync Configuration

### Sync Script (Desktop Clients)

```bash
#!/bin/bash
# /opt/wolf-logic/sync_from_librarian.sh

PGPASSWORD=wolflogic2024 pg_dump \
  -h 100.110.82.181 \
  -p 5433 \
  -U wolf \
  -d wolf_logic \
  --data-only \
  --table=memories \
  > /tmp/memories_sync.sql

psql -d wolf_logic_local < /tmp/memories_sync.sql
rm -f /tmp/memories_sync.sql
```

### Cron Entry

```cron
# Sync every 5 minutes
*/5 * * * * /opt/wolf-logic/sync_from_librarian.sh >> /var/log/wolf_sync.log 2>&1
```

## Authentication

### Authentik OAuth

```yaml
Provider: http://100.110.82.181:9001
Client ID: mcp-intake
Scopes: openid profile email
```

### PostgreSQL Access

```bash
# Direct database access (for sync scripts)
User: wolf
Password: wolflogic2024
Port: 5433
```

## Namespace Reference

| Namespace | Count | Purpose |
|-----------|-------|---------|
| scripty | 46,606 | Session transcripts |
| wolf_story | 16,124 | Books, narratives |
| ingested | 10,864 | File ingestions |
| session_recovery | 9,459 | Session context |
| wolf_hunt | 2,916 | Job search data |
| core_identity | 9 | Constitution |

## Monitoring

### Health Checks

```bash
# Check MCP Intake API
curl http://100.110.82.181:8002/health

# Check PostgreSQL
PGPASSWORD=wolflogic2024 psql -h 100.110.82.181 -p 5433 -U wolf -d wolf_logic -c "SELECT COUNT(*) FROM memories;"

# Check Ollama embeddings
curl http://100.110.82.181:11434/api/tags | grep qwen3-embedding
```

### Sync Verification

```bash
# On 181: Check recent ingestions
SELECT COUNT(*) FROM memories WHERE created_at >= NOW() - INTERVAL '1 hour';

# On client: Check sync freshness
psql -d wolf_logic_local -c "SELECT MAX(created_at) FROM memories;"
```

## Troubleshooting

### Client cannot submit to MCP Intake

1. Check Tailscale: `tailscale status`
2. Check port: `nc -zv 100.110.82.181 8002`
3. Check OAuth token expiry
4. Check API health: `curl http://100.110.82.181:8002/health`

### Sync fails

1. Check PostgreSQL on 181: `nc -zv 100.110.82.181 5433`
2. Check credentials: `PGPASSWORD=wolflogic2024 psql -h 100.110.82.181 ...`
3. Check disk space locally: `df -h`
4. Check sync log: `tail -50 /var/log/wolf_sync.log`

### Local DB is empty

1. Run manual sync: `/opt/wolf-logic/sync_from_librarian.sh`
2. Check schema exists: `psql -d wolf_logic_local -c "\d memories"`
3. If no schema: Re-import from 181

## File Locations

### Server (181)

```
/data/client-dumps/           # Incoming submissions queue
/var/log/swarm-intake.log     # Processor logs
/mnt/Wolf-code/.../writers/   # Ingest scripts
```

### Clients

```
~/.config/wolf-logic/env      # Environment variables
~/wolf-logic-client/scripts/  # Sync scripts
/var/log/wolf_sync.log        # Sync logs
wolf_logic_local              # Local PostgreSQL database
```

## Related Documentation

- `/macro-os/client/README.md` - Desktop client quick start
- `/macro-os/client/architecture.md` - Full architecture explanation
- `/macro-os/client/setup-guide.md` - Desktop setup walkthrough
- `/android-client/MEMORY_LAYER.md` - Android integration
- `/android-client/SETUP.md` - Android setup guide
