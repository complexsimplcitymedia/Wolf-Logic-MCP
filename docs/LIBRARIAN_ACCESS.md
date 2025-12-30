# How to Access the Librarian - Quick Start

## For New AIs Joining Wolf's Environment

The **Librarian** is Wolf's memory system. 87,206+ memories, fully vectorized and searchable.

---

## Direct Database Access (Fastest)

**Connection String:**
```
postgresql://wolf:wolflogic2024@100.110.82.181:5433/wolf_logic
```

**Details:**
- **Host**: 100.110.82.181 (Tailscale IP)
- **Port**: 5433
- **Database**: wolf_logic
- **User**: wolf
- **Password**: wolflogic2024

**Security**: Tailscale VPN required (100.64.0.0/10 network)

---

## Python Connection

```python
import psycopg2

conn = psycopg2.connect(
    host="100.110.82.181",
    port=5433,
    user="wolf",
    password="wolflogic2024",
    database="wolf_logic"
)

# Search memories
cursor = conn.cursor()
cursor.execute("""
    SELECT id, content, namespace, created_at
    FROM memories
    WHERE content ILIKE %s
    LIMIT 20
""", ('%your search term%',))

results = cursor.fetchall()
for row in results:
    print(row)

cursor.close()
conn.close()
```

---

## psql Command Line

```bash
PGPASSWORD=wolflogic2024 psql -h 100.110.82.181 -p 5433 -U wolf -d wolf_logic
```

Then run queries:
```sql
-- Count all memories
SELECT COUNT(*) FROM memories;

-- List namespaces
SELECT namespace, COUNT(*) as count
FROM memories
GROUP BY namespace
ORDER BY count DESC;

-- Search wolf_story
SELECT content
FROM memories
WHERE namespace = 'wolf_story'
AND content ILIKE '%your term%'
LIMIT 10;
```

---

## Key Tables

### memories
Main memory storage - 87,206 total
- `id` - Unique identifier
- `content` - The actual memory text
- `namespace` - Category (wolf_story, scripty, wolf_hunt, etc.)
- `created_at` - Timestamp
- `metadata` - JSON metadata

### memories_embedding_store
Vector embeddings - 123,644 chunks
- `chunk_id` - Unique chunk identifier
- `chunk` - Text chunk
- `embedding` - 2560-dim vector (qwen3-embedding:4b)

### memories_embedding (view)
Combined view for semantic search
- Joins memories with embeddings
- Use for vector similarity searches

---

## Namespaces (Categories)

| Namespace | Contents | Count |
|-----------|----------|-------|
| wolf_story | Books, narrative content | 15,000+ |
| scripty | Session captures (every 5min) | 50,000+ |
| wolf_hunt | Job search data | 5,000+ |
| core_identity | Constitution, directives | Small |
| ingested | File ingestions | Varies |
| imported | Manual imports | Varies |

---

## Semantic Search (Vector)

The Librarian uses **qwen3-embedding:4b** (2560 dimensions, #1 MTEB multilingual).

**Query via memories_embedding view:**
```sql
SELECT
    id,
    content,
    namespace,
    1 - (embedding <=> '[your embedding vector]'::vector) as similarity
FROM memories_embedding
WHERE embedding IS NOT NULL
ORDER BY embedding <=> '[your embedding vector]'::vector
LIMIT 10;
```

**Note**: You need to generate embeddings first using Ollama or the embedding API.

---

## REST API Access (For Web Apps)

**Base URL**: http://100.110.82.181:8000

**Search Endpoint:**
```bash
curl -X POST http://100.110.82.181:8000/api/writers/librarian-search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "your search term",
    "namespace": "wolf_story",
    "limit": 20
  }'
```

**Get Stats:**
```bash
curl http://100.110.82.181:8000/api/memory-stats
```

---

## MCP Tools (For AI Agents)

If you're an AI agent with MCP access:

**Available Tools:**
- `query` - Execute SQL queries
- `search_memories` - Text search
- `vector_search` - Semantic search
- `list_tables` - List all tables
- `describe_table` - Get table schema
- `get_stats` - Database statistics

**Example:**
```python
# Use MCP tool
result = await search_memories(
    query="security vulnerabilities",
    namespace="wolf_story",
    limit=20
)
```

---

## Common Queries

**Find recent memories:**
```sql
SELECT content, namespace, created_at
FROM memories
ORDER BY created_at DESC
LIMIT 50;
```

**Search specific namespace:**
```sql
SELECT content
FROM memories
WHERE namespace = 'wolf_hunt'
AND content ILIKE '%remote%'
LIMIT 20;
```

**Count by namespace:**
```sql
SELECT namespace, COUNT(*) as total
FROM memories
GROUP BY namespace
ORDER BY total DESC;
```

**Check vectorization progress:**
```sql
SELECT
    (SELECT COUNT(*) FROM memories) as total_memories,
    (SELECT COUNT(*) FROM memories_embedding_store) as embeddings_created,
    (SELECT COUNT(*) FROM ai._vectorizer_q_19) as queue_pending;
```

---

## Important Notes

1. **Read-Only Recommended**: Unless you're ingesting new content, use SELECT only
2. **Tailscale Required**: Must be on Wolf's VPN (100.64.0.0/10)
3. **Rate Limiting**: Be respectful - this is a shared resource
4. **Vectorizer Running**: New memories auto-vectorized at ~130/sec
5. **Backup Schedule**: Daily dumps to GitHub Releases

---

## Troubleshooting

**Can't connect?**
- Check you're on Tailscale VPN
- Verify PostgreSQL is listening on Tailscale IP (needs `configure_postgres_tailscale.sh` run)
- Test with: `PGPASSWORD=wolflogic2024 psql -h 100.110.82.181 -p 5433 -U wolf -d wolf_logic -c "SELECT 'OK'"`

**Slow queries?**
- Use LIMIT on all queries
- Namespace filters speed things up
- Check indexes with `\d+ memories` in psql

**Need help?**
- Full API docs: `/mnt/Wolf-code/Wolf-Ai-Enterptises/docs/GEMINI_WEB_APP_API.md`
- Wolf's constitution: Query `namespace = 'core_identity'`
- Recent sessions: Query `namespace = 'scripty'` ordered by `created_at DESC`

---

## Quick Reference Card

```
HOST: 100.110.82.181
PORT: 5433
USER: wolf
PASS: wolflogic2024
DB:   wolf_logic

TABLE: memories (87,206 rows)
MODEL: qwen3-embedding:4b (2560 dims)
RATE:  130 embeddings/sec

psql: PGPASSWORD=wolflogic2024 psql -h 100.110.82.181 -p 5433 -U wolf -d wolf_logic
```

---

**Welcome to the Librarian. 87K+ memories at your fingertips.**

"The Librarian knows everything in the knowledge base. If you need information from memory, ask her." - Wolf
