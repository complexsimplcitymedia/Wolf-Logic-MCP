#!/usr/bin/env python3
"""
Postgres Backup Sync Script - 1 Hour Lag Protection
Syncs new memories from production (5433) to backup (5434) with 1-hour delay
Keeps backup in read-only mode except during sync windows
"""

import psycopg2
from datetime import datetime, timedelta
import time
import sys

# Database configurations
# SOURCE: Docker backup (real-time from production)
SOURCE_CONFIG = {
    'host': 'localhost',
    'port': 5434,
    'user': 'wolf',
    'password': 'wolflogic2024',
    'database': 'wolf_logic'
}

# BACKUP: WolfPack native (1-hour lag, ultimate safety)
BACKUP_CONFIG = {
    'host': '100.110.82.181',
    'port': 5435,
    'user': 'wolf',
    'password': 'wolflogic2024',
    'database': 'wolf_logic'
}

LAG_HOURS = 1  # 1 hour lag for safety buffer

def log(message):
    """Log with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")
    sys.stdout.flush()

def set_readonly(conn, readonly=True):
    """Set database to read-only or read-write mode"""
    mode = "ON" if readonly else "OFF"
    old_autocommit = conn.autocommit
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(f"ALTER DATABASE wolf_logic SET default_transaction_read_only = {mode};")
    conn.autocommit = old_autocommit
    log(f"Backup database set to {'READ-ONLY' if readonly else 'READ-WRITE'} mode")

def get_sync_cutoff():
    """Get the cutoff timestamp (1 hour ago)"""
    return datetime.now() - timedelta(hours=LAG_HOURS)

def get_last_backup_timestamp(backup_conn):
    """Get the most recent created_at timestamp in backup"""
    with backup_conn.cursor() as cur:
        cur.execute("SELECT MAX(created_at) FROM memories;")
        result = cur.fetchone()[0]
        return result if result else datetime.min

def sync_memories(source_conn, backup_conn):
    """Sync memories from source (Docker) to backup (WolfPack) with 1-hour lag"""

    # Get cutoff time (1 hour ago)
    cutoff = get_sync_cutoff()

    # Get last backup timestamp
    last_backup = get_last_backup_timestamp(backup_conn)

    log(f"Sync window: {last_backup} to {cutoff}")

    # Fetch new memories from source within the window
    with source_conn.cursor() as source_cur:
        source_cur.execute("""
            SELECT id, user_id, content, metadata, memory_type, namespace, created_at, updated_at
            FROM memories
            WHERE created_at > %s AND created_at <= %s
            ORDER BY created_at ASC;
        """, (last_backup, cutoff))

        new_memories = source_cur.fetchall()

    if not new_memories:
        log(f"No new memories to sync (cutoff: {cutoff})")
        return 0

    # Insert new memories into backup
    with backup_conn.cursor() as backup_cur:
        for memory in new_memories:
            backup_cur.execute("""
                INSERT INTO memories (id, user_id, content, metadata, memory_type, namespace, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    user_id = EXCLUDED.user_id,
                    content = EXCLUDED.content,
                    metadata = EXCLUDED.metadata,
                    memory_type = EXCLUDED.memory_type,
                    namespace = EXCLUDED.namespace,
                    created_at = EXCLUDED.created_at,
                    updated_at = EXCLUDED.updated_at;
            """, memory)

        backup_conn.commit()

    log(f"Synced {len(new_memories)} memories to backup")
    return len(new_memories)

def sync_embeddings(source_conn, backup_conn):
    """Sync embeddings from source (Docker) to backup (WolfPack)"""

    # Get last embedding UUID in backup
    with backup_conn.cursor() as cur:
        cur.execute("SELECT embedding_uuid FROM memories_embedding_store ORDER BY embedding_uuid DESC LIMIT 1;")
        result = cur.fetchone()
        last_uuid = result[0] if result else None

    # Fetch new embeddings from source
    with source_conn.cursor() as source_cur:
        if last_uuid:
            source_cur.execute("""
                SELECT embedding_uuid, id, chunk_seq, chunk, embedding
                FROM memories_embedding_store
                WHERE embedding_uuid > %s
                ORDER BY embedding_uuid ASC;
            """, (last_uuid,))
        else:
            source_cur.execute("""
                SELECT embedding_uuid, id, chunk_seq, chunk, embedding
                FROM memories_embedding_store
                ORDER BY embedding_uuid ASC;
            """)

        new_embeddings = source_cur.fetchall()

    if not new_embeddings:
        log("No new embeddings to sync")
        return 0

    # Insert new embeddings into backup
    with backup_conn.cursor() as backup_cur:
        for embedding in new_embeddings:
            backup_cur.execute("""
                INSERT INTO memories_embedding_store (embedding_uuid, id, chunk_seq, chunk, embedding)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (embedding_uuid) DO NOTHING;
            """, embedding)

        backup_conn.commit()

    log(f"Synced {len(new_embeddings)} embeddings to backup")
    return len(new_embeddings)

def run_sync():
    """Execute one sync cycle"""
    log("=== Starting sync cycle ===")

    source_conn = None
    backup_conn = None

    try:
        # Connect to source (Docker backup, read-only)
        source_conn = psycopg2.connect(**SOURCE_CONFIG)
        source_conn.set_session(readonly=True, autocommit=False)
        log("Connected to source database (Docker backup, read-only)")

        # Connect to backup (WolfPack native)
        backup_conn = psycopg2.connect(**BACKUP_CONFIG)
        backup_conn.set_session(autocommit=False)
        log("Connected to backup database (WolfPack native)")

        # Temporarily disable read-only on backup
        set_readonly(backup_conn, readonly=False)

        # Sync memories
        memory_count = sync_memories(source_conn, backup_conn)

        # Sync embeddings (skip if source doesn't have embedding table)
        embedding_count = 0
        try:
            embedding_count = sync_embeddings(source_conn, backup_conn)
        except Exception as e:
            log(f"Skipping embeddings sync: {e}")

        # Commit all changes before re-enabling read-only
        backup_conn.commit()

        # Re-enable read-only on backup
        set_readonly(backup_conn, readonly=True)

        log(f"=== Sync complete: {memory_count} memories, {embedding_count} embeddings ===")

    except Exception as e:
        log(f"ERROR during sync: {e}")
        if backup_conn:
            try:
                backup_conn.rollback()
                set_readonly(backup_conn, readonly=True)
            except:
                pass

    finally:
        if source_conn:
            source_conn.close()
        if backup_conn:
            backup_conn.close()

def main():
    """Main loop - run sync every hour"""
    log("Backup sync script started (1-hour lag mode)")
    log(f"Source: Docker {SOURCE_CONFIG['host']}:{SOURCE_CONFIG['port']} (real-time)")
    log(f"Backup: WolfPack {BACKUP_CONFIG['host']}:{BACKUP_CONFIG['port']} (1-hour lag)")
    log(f"Lag window: {LAG_HOURS} hour(s)")

    while True:
        try:
            run_sync()
        except Exception as e:
            log(f"CRITICAL ERROR: {e}")

        # Wait 1 hour before next sync
        log(f"Sleeping for 1 hour until next sync...")
        time.sleep(3600)  # 3600 seconds = 1 hour

if __name__ == "__main__":
    main()
