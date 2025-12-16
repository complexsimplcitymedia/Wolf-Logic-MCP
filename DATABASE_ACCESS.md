# Database Access - MCP Protocol

## PostgreSQL via MCP Server
**Database:** wolf_logic @ 100.110.82.181:5433 (Tailscale)
**Access:** PostgreSQL MCP Server (secured with Authentik OAuth)

### Start MCP Server
```bash
./mcp-servers/start_postgres_mcp.sh
```

### MCP Tools Available
- `query` - Execute read-only SQL (SELECT only)
- `search_memories` - Search through memories by content/namespace
- `vector_search` - Semantic search using embeddings
- `list_tables` - List all database tables
- `describe_table` - Get table schema
- `get_applications` - Query job applications
- `get_stats` - Database health and statistics

### Connection String (Direct - Use MCP Instead)
```
postgresql://wolf:wolflogic2024@100.110.82.181:5433/wolf_logic
```

### Security
- **MCP Server required** - No direct database access from apps
- **OAuth via Authentik** - All MCP requests authenticated
- **Read-only tools** - Only SELECT queries allowed
- **Tailscale network** - Database only accessible via VPN

## Memory Namespaces
| Namespace | Contains |
|-----------|----------|
| wolf_story | Books, narrative content |
| scripty | Session captures (every 5min) |
| ingested | File ingestions |
| core_identity | Constitution, directives |
| session_recovery | Conversation context |
| wolf_hunt | Job search data, applications |
| mem0_import | Legacy imports |
| stenographer | Stenographer captures |
| system_announcements | System-level announcements |

## Librarian
- **Model:** qwen3-embedding:4b (2560 dims, #1 MTEB multilingual)
- **Memories:** 85,858 total
- **Vectorized:** 89,000+ embeddings
- **Worker:** pgai vectorizer (concurrency 4, ~130 embeddings/sec)
