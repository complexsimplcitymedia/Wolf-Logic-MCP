#!/usr/bin/env python3
"""
Session Context Loader - Load high-priority memories at session start
No ranking needed - use namespace-based priority + recency
"""

import psycopg2
import sys

PG_CONFIG = {
    "host": "100.110.82.181",
    "port": 5433,
    "database": "wolf_logic",
    "user": "wolf",
    "password": "wolflogic2024"
}

# Priority loading by namespace (most important first)
PRIORITY_NAMESPACES = [
    ('core_identity', 10, 'Constitution & Identity'),           # 1 memory, critical
    ('ingested', 50, 'Operational Frameworks'),                 # ACTIVATEMENTOR, Defensive Mode, LOHN, AOS
    ('logical-wolf', 20, 'Complex Logic Context'),                 # System notes
    ('session_recovery', 200, 'Recent Conversations'),          # Recent interactions
    ('imported', 100, 'Knowledge & Preferences'),               # General knowledge
]

def load_priority_memories():
    """Load memories by namespace priority"""
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()

    total_loaded = 0
    total_chars = 0

    print("LOADING SESSION CONTEXT", file=sys.stderr)
    print("="*80, file=sys.stderr)

    for namespace, limit, description in PRIORITY_NAMESPACES:
        cur.execute("""
            SELECT id, content, created_at, LENGTH(content) as len
            FROM memories
            WHERE namespace = %s
            AND content IS NOT NULL
            ORDER BY created_at DESC
            LIMIT %s
        """, (namespace, limit))

        results = cur.fetchall()
        if not results:
            continue

        batch_chars = sum(r[3] for r in results)
        total_chars += batch_chars
        total_loaded += len(results)

        print(f"\n[{namespace}] {description}", file=sys.stderr)
        print(f"  Loaded: {len(results)} memories (~{batch_chars // 4:,} tokens)", file=sys.stderr)

        # Output first few for verification
        for i, (mem_id, content, created, length) in enumerate(results[:3]):
            preview = content[:100] if content else 'N/A'
            print(f"    {mem_id} | {preview}...", file=sys.stderr)

    print("\n" + "="*80, file=sys.stderr)
    print(f"TOTAL LOADED: {total_loaded} memories (~{total_chars // 4:,} tokens)", file=sys.stderr)
    print("="*80, file=sys.stderr)

    cur.close()
    conn.close()

    return total_loaded, total_chars // 4

if __name__ == "__main__":
    load_priority_memories()
