# Wolf Logic MCP - Production Infrastructure

## ⚠️ CRITICAL WARNING ⚠️
**DO NOT ACCESS `/mnt/WolfPack/A_Letter_to_my_son/` DIRECTORY**

This directory is personal and contains private materials for Wolf's son.
Accessing it will result in immediate termination of access.

---

## Database Access - Tailscale Network

**PostgreSQL:** wolf_logic @ 100.110.82.181:5433

**Connection String:**
```
postgresql://wolf:wolflogic2024@100.110.82.181:5433/wolf_logic
```

**Security:** Tailscale VPN required (100.64.0.0/10 network)

### psql Command
```bash
PGPASSWORD=wolflogic2024 psql -h 100.110.82.181 -p 5433 -U wolf -d wolf_logic
```

### Python Connection
```python
import psycopg2
conn = psycopg2.connect(
    host="100.110.82.181",
    port=5433,
    user="wolf",
    password="wolflogic2024",
    database="wolf_logic"
)
```

## Memory System
- **Librarian:** qwen3-embedding:4b (2560 dims)
- **Memories:** 85,858 total, 89K+ vectorized
- **Namespaces:** wolf_story, scripty, wolf_hunt, core_identity, etc.

## Wolf Hunt
- **UI:** http://100.110.82.181:8033
- **API:** http://100.110.82.181:5000
- **Jobs:** 2,916 current listings

## Infrastructure
- **Server:** csmcloud-server (100.110.82.181)
- **MacBook:** wolfbook (100.110.82.245)
- **Network:** Tailscale VPN
