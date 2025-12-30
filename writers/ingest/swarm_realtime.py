#!/usr/bin/env python3
"""
Swarm Real-Time Ingestion - The Processing Department
Watches scripty output every 5 minutes, vectorizes with embed fleet, stores in pgai.

Architecture:
- Monitors scripty namespace in memories table
- Fetches new unvectorized entries
- Fans out to embedding fleet (exclude nomic - reserved for librarian)
- Updates with vector embeddings in real-time

Union Way: Don't wait for the dump. Process as it comes.
"""

import sys
import os
import time
import json
import psycopg2
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Ollama for embeddings
import ollama

# Config
PG_CONFIG = {
    "host": "100.110.82.181",
    "port": 5433,
    "database": "wolf_logic",
    "user": "wolf",
    "password": "wolflogic2024"
}

# Embedding fleet - exclude nomic (reserved for librarian)
EMBED_FLEET = [
    "bge-large:latest",
    "mxbai-embed-large:latest",
    "snowflake-arctic-embed:137m",
    "jina/jina-embeddings-v2-base-en:latest",
]

# Swarm config
CHECK_INTERVAL = 300  # 5 minutes in seconds
MAX_WORKERS = 4  # Parallel embedding workers

# Thread-safe printing
print_lock = threading.Lock()
def safe_print(msg):
    with print_lock:
        print(msg)


def get_unvectorized_entries(limit=100):
    """Get scripty entries that need vectorization"""
    try:
        conn = psycopg2.connect(**PG_CONFIG)
        with conn.cursor() as cur:
            # Get recent scripty entries without embeddings
            cur.execute("""
                SELECT id, content, created_at
                FROM memories
                WHERE namespace = 'scripty'
                  AND embedding IS NULL
                  AND created_at > NOW() - INTERVAL '1 hour'
                ORDER BY created_at ASC
                LIMIT %s
            """, (limit,))

            entries = []
            for row in cur.fetchall():
                entries.append({
                    "id": row[0],
                    "content": row[1],
                    "created_at": row[2]
                })

        conn.close()
        return entries

    except Exception as e:
        safe_print(f"[SWARM] Error fetching entries: {e}")
        return []


def generate_embedding(content, model):
    """Generate embedding for content using specified model"""
    try:
        response = ollama.embeddings(
            model=model,
            prompt=content
        )
        return response['embedding']
    except Exception as e:
        safe_print(f"[SWARM] Embedding error [{model}]: {e}")
        return None


def vectorize_entry(entry, model):
    """Vectorize a single entry and update in database"""
    entry_id = entry['id']
    content = entry['content']

    try:
        # Generate embedding
        embedding = generate_embedding(content, model)

        if embedding is None:
            return {"id": entry_id, "status": "failed", "model": model}

        # Update database with embedding
        conn = psycopg2.connect(**PG_CONFIG)
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE memories
                SET embedding = %s,
                    updated_at = %s
                WHERE id = %s
            """, (embedding, datetime.now(), entry_id))

        conn.commit()
        conn.close()

        return {"id": entry_id, "status": "success", "model": model}

    except Exception as e:
        safe_print(f"[SWARM] Vectorization error [ID {entry_id}]: {e}")
        return {"id": entry_id, "status": "error", "model": model, "error": str(e)}


def process_batch(entries):
    """Process a batch of entries with parallel embedding fleet"""
    if not entries:
        return []

    safe_print(f"[SWARM] Processing {len(entries)} entries...")

    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {}

        # Distribute entries across embed fleet
        for i, entry in enumerate(entries):
            model = EMBED_FLEET[i % len(EMBED_FLEET)]
            future = executor.submit(vectorize_entry, entry, model)
            futures[future] = entry['id']

        # Collect results
        for future in as_completed(futures):
            result = future.result()
            results.append(result)

            if result['status'] == 'success':
                safe_print(f"  [SWARM] ✓ Entry {result['id']} vectorized [{result['model']}]")
            else:
                safe_print(f"  [SWARM] ✗ Entry {result['id']} failed")

    success_count = sum(1 for r in results if r['status'] == 'success')
    safe_print(f"[SWARM] Batch complete: {success_count}/{len(entries)} vectorized")

    return results


def watch_and_swarm(check_interval=CHECK_INTERVAL):
    """Main loop - watch for new entries and swarm them"""
    safe_print("=" * 60)
    safe_print("SWARM REAL-TIME INGESTION")
    safe_print("=" * 60)
    safe_print(f"Embed Fleet: {len(EMBED_FLEET)} models")
    safe_print(f"Check Interval: {check_interval}s ({check_interval/60:.1f} min)")
    safe_print(f"Max Workers: {MAX_WORKERS}")
    safe_print("=" * 60)
    safe_print("Union Way: Process as it comes, don't wait for the dump")
    safe_print("=" * 60)

    iteration = 0

    while True:
        try:
            iteration += 1
            timestamp = datetime.now().strftime("%H:%M:%S")

            safe_print(f"\n[SWARM] [{timestamp}] Iteration #{iteration} - Checking for new entries...")

            # Get unvectorized entries
            entries = get_unvectorized_entries()

            if entries:
                safe_print(f"[SWARM] Found {len(entries)} entries needing vectorization")
                process_batch(entries)
            else:
                safe_print(f"[SWARM] No new entries - swarm idle")

            # Wait for next check
            time.sleep(check_interval)

        except KeyboardInterrupt:
            safe_print("\n[SWARM] Shutting down swarm")
            safe_print(f"Total iterations: {iteration}")
            break
        except Exception as e:
            safe_print(f"[SWARM] Error: {e}")
            time.sleep(60)  # Wait a minute before retrying on error


def main():
    """Entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Swarm Real-Time Ingestion')
    parser.add_argument('--interval', type=int, default=CHECK_INTERVAL,
                       help=f'Check interval in seconds (default: {CHECK_INTERVAL})')
    parser.add_argument('--once', action='store_true',
                       help='Run once and exit (no continuous loop)')

    args = parser.parse_args()

    if args.once:
        # Single run mode
        entries = get_unvectorized_entries()
        if entries:
            process_batch(entries)
        else:
            safe_print("[SWARM] No entries to process")
    else:
        # Continuous watch mode
        watch_and_swarm(check_interval=args.interval)


if __name__ == "__main__":
    main()
