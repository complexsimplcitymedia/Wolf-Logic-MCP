# Query Patterns for Local PostgreSQL

## The Rule

**Query local. Never query 181 for reads.**

Your local `wolf_logic_local` database is synced every 5 minutes from 181. Query it. It's fast. It's local. It doesn't load the hub.

## Connection Pattern

```python
import psycopg2
import os

def get_local_connection():
    """Get connection to local PostgreSQL."""
    return psycopg2.connect(
        host="localhost",
        port=5432,
        dbname="wolf_logic_local",
        user=os.environ.get("LOCAL_PG_USER", os.environ.get("USER")),
        password=os.environ.get("LOCAL_PG_PASSWORD", "")
    )
```

## Basic Queries

### Count All Memories

```python
conn = get_local_connection()
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM memories;")
total = cur.fetchone()[0]
print(f"Total memories: {total}")
conn.close()
```

### Get Recent Memories

```python
cur.execute("""
    SELECT content, namespace, created_at
    FROM memories
    ORDER BY created_at DESC
    LIMIT 20;
""")
for content, namespace, created_at in cur.fetchall():
    print(f"[{namespace}] {created_at}: {content[:100]}...")
```

### Filter by Namespace

```python
# Get scripty memories (conversation transcripts)
cur.execute("""
    SELECT content, created_at
    FROM memories
    WHERE namespace = 'scripty'
    ORDER BY created_at DESC
    LIMIT 50;
""")

# Get core identity rules
cur.execute("""
    SELECT content
    FROM memories
    WHERE namespace = 'core_identity';
""")

# Get job search data
cur.execute("""
    SELECT content, created_at
    FROM memories
    WHERE namespace = 'wolf_hunt'
    ORDER BY created_at DESC
    LIMIT 100;
""")
```

## Text Search (Exact Match)

Use `ILIKE` for case-insensitive pattern matching.

```python
# Find memories mentioning "API"
cur.execute("""
    SELECT content, namespace, created_at
    FROM memories
    WHERE content ILIKE '%API%'
    ORDER BY created_at DESC
    LIMIT 20;
""")

# Find memories about specific topic
search_term = "investor pitch"
cur.execute("""
    SELECT content, namespace, created_at
    FROM memories
    WHERE content ILIKE %s
    ORDER BY created_at DESC
    LIMIT 20;
""", (f"%{search_term}%",))
```

## Time-Based Queries

```python
from datetime import datetime, timedelta

# Last 24 hours
cur.execute("""
    SELECT content, namespace, created_at
    FROM memories
    WHERE created_at >= NOW() - INTERVAL '24 hours'
    ORDER BY created_at DESC;
""")

# Specific date range
start_date = "2025-12-01"
end_date = "2025-12-24"
cur.execute("""
    SELECT content, namespace, created_at
    FROM memories
    WHERE created_at >= %s AND created_at < %s
    ORDER BY created_at;
""", (start_date, end_date))

# This week's scripty entries
cur.execute("""
    SELECT content, created_at
    FROM memories
    WHERE namespace = 'scripty'
      AND created_at >= DATE_TRUNC('week', CURRENT_DATE)
    ORDER BY created_at DESC;
""")
```

## Namespace Analysis

```python
# Count by namespace
cur.execute("""
    SELECT namespace, COUNT(*) as count
    FROM memories
    GROUP BY namespace
    ORDER BY count DESC;
""")
for namespace, count in cur.fetchall():
    print(f"{namespace}: {count}")

# Recent activity by namespace
cur.execute("""
    SELECT namespace, MAX(created_at) as last_activity
    FROM memories
    GROUP BY namespace
    ORDER BY last_activity DESC;
""")
```

## Combined Filters

```python
# Scripty memories from this month mentioning "database"
cur.execute("""
    SELECT content, created_at
    FROM memories
    WHERE namespace = 'scripty'
      AND created_at >= DATE_TRUNC('month', CURRENT_DATE)
      AND content ILIKE '%database%'
    ORDER BY created_at DESC
    LIMIT 30;
""")

# Wolf hunt entries with contact info
cur.execute("""
    SELECT content, created_at
    FROM memories
    WHERE namespace = 'wolf_hunt'
      AND (content ILIKE '%email%' OR content ILIKE '%@%' OR content ILIKE '%linkedin%')
    ORDER BY created_at DESC;
""")
```

## Full-Text Search (If Enabled)

If `memories` has a tsvector column:

```python
# Full-text search
cur.execute("""
    SELECT content, namespace, created_at,
           ts_rank(to_tsvector('english', content), plainto_tsquery('english', %s)) as rank
    FROM memories
    WHERE to_tsvector('english', content) @@ plainto_tsquery('english', %s)
    ORDER BY rank DESC
    LIMIT 20;
""", (search_query, search_query))
```

## Semantic Search (Requires Embeddings)

If your local DB has the `memories_embedding` view synced:

```python
# Note: Semantic search requires the embedding extension
# and a local ollama instance for query embedding

# This example assumes pgai extension is available locally
cur.execute("""
    SELECT content, namespace, created_at
    FROM memories_embedding
    ORDER BY embedding <=> ai.ollama_embed('qwen3-embedding:4b', %s)
    LIMIT 10;
""", (query_text,))
```

**Important:** Semantic search locally requires:
1. pgvector extension installed
2. pgai extension installed
3. Ollama running locally with qwen3-embedding:4b
4. `memories_embedding` view synced from 181

For most clients, stick to text search. Semantic search is best done through the hub.

## Reusable Query Functions

```python
#!/usr/bin/env python3
"""Wolf Logic local query library."""

import psycopg2
import os
from datetime import datetime, timedelta
from typing import List, Tuple, Optional

def get_connection():
    """Get local PostgreSQL connection."""
    return psycopg2.connect(
        host="localhost",
        port=5432,
        dbname="wolf_logic_local",
        user=os.environ.get("LOCAL_PG_USER", os.environ.get("USER")),
        password=os.environ.get("LOCAL_PG_PASSWORD", "")
    )

def search_memories(
    query: str,
    namespace: Optional[str] = None,
    limit: int = 20,
    hours_ago: Optional[int] = None
) -> List[Tuple[str, str, datetime]]:
    """
    Search memories by text content.

    Args:
        query: Search term (case-insensitive)
        namespace: Filter to specific namespace
        limit: Max results
        hours_ago: Only search memories from last N hours

    Returns:
        List of (content, namespace, created_at) tuples
    """
    conn = get_connection()
    cur = conn.cursor()

    sql = """
        SELECT content, namespace, created_at
        FROM memories
        WHERE content ILIKE %s
    """
    params = [f"%{query}%"]

    if namespace:
        sql += " AND namespace = %s"
        params.append(namespace)

    if hours_ago:
        sql += " AND created_at >= NOW() - INTERVAL '%s hours'"
        params.append(hours_ago)

    sql += " ORDER BY created_at DESC LIMIT %s"
    params.append(limit)

    cur.execute(sql, params)
    results = cur.fetchall()
    conn.close()
    return results

def get_recent_memories(
    namespace: str,
    limit: int = 50
) -> List[Tuple[str, datetime]]:
    """Get most recent memories from a namespace."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT content, created_at
        FROM memories
        WHERE namespace = %s
        ORDER BY created_at DESC
        LIMIT %s;
    """, (namespace, limit))
    results = cur.fetchall()
    conn.close()
    return results

def get_namespace_stats() -> List[Tuple[str, int]]:
    """Get memory counts by namespace."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT namespace, COUNT(*)
        FROM memories
        GROUP BY namespace
        ORDER BY COUNT(*) DESC;
    """)
    results = cur.fetchall()
    conn.close()
    return results

def memory_count() -> int:
    """Get total memory count."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM memories;")
    count = cur.fetchone()[0]
    conn.close()
    return count


# Example usage
if __name__ == "__main__":
    print(f"Total memories: {memory_count()}")
    print("\nNamespace stats:")
    for ns, count in get_namespace_stats()[:5]:
        print(f"  {ns}: {count}")

    print("\nRecent scripty entries:")
    for content, created_at in get_recent_memories("scripty", 5):
        print(f"  [{created_at}] {content[:80]}...")
```

## Performance Tips

1. **Always use LIMIT** - Don't fetch 97k rows when you need 20
2. **Filter by namespace first** - Reduces scan size dramatically
3. **Add time constraints** - `created_at >= NOW() - INTERVAL '7 days'` is faster than full table scan
4. **Create indexes locally** (if queries are slow):

```sql
-- Index on namespace
CREATE INDEX IF NOT EXISTS idx_memories_namespace ON memories(namespace);

-- Index on created_at
CREATE INDEX IF NOT EXISTS idx_memories_created_at ON memories(created_at);

-- Composite index for common queries
CREATE INDEX IF NOT EXISTS idx_memories_ns_created ON memories(namespace, created_at DESC);
```

## When to Force Sync

If you need data newer than your last sync:

```bash
# Manual sync
~/wolf-logic-client/scripts/sync_from_librarian.sh

# Verify
psql -d wolf_logic_local -c "SELECT MAX(created_at) FROM memories;"
```

## When to Query 181 Directly (Rare)

Only query 181 directly if:
1. Your local DB is empty (initial setup)
2. Sync is broken and you need immediate data
3. You need real-time data (sync lag unacceptable)

```python
def get_hub_connection():
    """Get connection to 181 (USE SPARINGLY)."""
    return psycopg2.connect(
        host="100.110.82.181",
        port=5433,
        dbname="wolf_logic",
        user="wolf",
        password="wolflogic2024"
    )
```

**Routine queries should NEVER hit 181.** That's what your local DB is for.
