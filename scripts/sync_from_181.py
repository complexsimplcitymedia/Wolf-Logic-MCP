#!/usr/bin/env python3
"""
Sync memories from primary (181) to local postgres
For offline resilience during travel
"""
import psycopg2
import json
from datetime import datetime, timedelta
from psycopg2.extras import Json

PRIMARY = {
    "host": "100.110.82.181",
    "port": 5433,
    "database": "wolf_logic",
    "user": "wolf",
    "password": "wolflogic2024"
}

LOCAL = {
    "host": "localhost",
    "port": 5432,
    "database": "wolf_logic",
    "user": "wolf",
    "password": "wolflogic2024"
}

def sync_memories(days_back=7):
    """Sync recent memories from 181 to localhost"""

    # Connect to both databases
    conn_primary = psycopg2.connect(**PRIMARY)
    conn_local = psycopg2.connect(**LOCAL)

    cur_primary = conn_primary.cursor()
    cur_local = conn_local.cursor()

    # Get memories from last N days
    cutoff = datetime.now() - timedelta(days=days_back)

    cur_primary.execute("""
        SELECT user_id, content, metadata, memory_type, namespace, created_at, updated_at
        FROM memories
        WHERE created_at >= %s
        ORDER BY created_at DESC;
    """, (cutoff,))

    memories = cur_primary.fetchall()
    print(f"Fetched {len(memories)} memories from 181 (last {days_back} days)")

    # Insert into local (with conflict handling)
    synced = 0
    skipped = 0

    for memory in memories:
        user_id, content, metadata, memory_type, namespace, created_at, updated_at = memory

        # Check if already exists (by content + created_at)
        cur_local.execute("""
            SELECT id FROM memories
            WHERE content = %s AND created_at = %s;
        """, (content, created_at))

        if cur_local.fetchone():
            skipped += 1
            continue

        # Insert (convert metadata dict to Json for JSONB)
        cur_local.execute("""
            INSERT INTO memories (user_id, content, metadata, memory_type, namespace, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """, (user_id, content, Json(metadata) if metadata else None, memory_type, namespace, created_at, updated_at))
        synced += 1

    conn_local.commit()

    print(f"Synced: {synced} new memories")
    print(f"Skipped: {skipped} duplicates")

    # Summary
    cur_local.execute("SELECT COUNT(*) FROM memories;")
    local_total = cur_local.fetchone()[0]

    cur_primary.execute("SELECT COUNT(*) FROM memories;")
    primary_total = cur_primary.fetchone()[0]

    print(f"\nLocal total: {local_total}")
    print(f"Primary total: {primary_total}")

    conn_primary.close()
    conn_local.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Sync memories from 181 to localhost')
    parser.add_argument('--days', type=int, default=7, help='Days back to sync (default: 7)')
    args = parser.parse_args()

    sync_memories(args.days)
