#!/usr/bin/env python3
"""
PGAI Queue Ingestor - PostgreSQL Memory Writer
Watches pgai-queue and ingests to PostgreSQL using pgai.

Pipeline: pgai-queue → PostgreSQL memories table
"""
import os
import json
import time
import psycopg2
from datetime import datetime
from pathlib import Path

# Directories
QUEUE_DIR = Path("/mnt/Wolf-code/Wolf-Ai-Enterptises/Wolf-Logic-MCP/data/pgai-queue")
PROCESSED_DIR = Path("/mnt/Wolf-code/Wolf-Ai-Enterptises/Wolf-Logic-MCP/data/pgai-processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Database connection
DB_CONFIG = {
    "host": os.getenv("PGHOST", "100.110.82.181"),
    "port": os.getenv("PGPORT", "5433"),
    "database": os.getenv("PGDATABASE", "wolf_logic"),
    "user": os.getenv("PGUSER", "wolf"),
    "password": os.getenv("PGPASSWORD", "wolflogic2024")
}

def get_db_connection(max_retries=3, retry_delay=2):
    """Get PostgreSQL connection with retry logic"""
    last_error = None
    for attempt in range(max_retries):
        try:
            return psycopg2.connect(**DB_CONFIG)
        except psycopg2.OperationalError as e:
            last_error = e
            if attempt < max_retries - 1:
                print(f"[{datetime.now()}] DB connection failed (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
            else:
                print(f"[{datetime.now()}] DB connection failed after {max_retries} attempts: {e}")
                raise
        except psycopg2.Error as e:
            print(f"[{datetime.now()}] Database error: {type(e).__name__}: {e}")
            raise

def ingest_to_pgai(data):
    """Ingest data to PostgreSQL memories table"""
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Validate required data
        content = data.get('text', data.get('content', ''))
        if not content:
            print(f"[{datetime.now()}] Skipping empty content")
            return False

        # Insert into memories table
        cur.execute("""
            INSERT INTO memories (user_id, content, namespace, metadata, created_at)
            VALUES (%s, %s, %s, %s, NOW())
        """, (
            data.get('username', 'wolf'),
            content,
            data.get('namespace', 'scripty'),
            json.dumps({
                "session": data.get('session'),
                "timestamp": data.get('timestamp'),
                "keywords": data.get('keywords', []),
                "sentiment": data.get('sentiment', {}),
                "source": data.get('source', 'unknown')
            })
        ))

        conn.commit()
        return True

    except psycopg2.IntegrityError as e:
        print(f"[{datetime.now()}] Duplicate or constraint violation: {e}")
        if conn:
            conn.rollback()
        return False
    except psycopg2.OperationalError as e:
        print(f"[{datetime.now()}] DB connection error during ingest: {e}")
        if conn:
            conn.rollback()
        return False
    except psycopg2.Error as e:
        print(f"[{datetime.now()}] Database error ({type(e).__name__}): {e}")
        if conn:
            conn.rollback()
        return False
    except json.JSONDecodeError as e:
        print(f"[{datetime.now()}] JSON encoding error in metadata: {e}")
        return False
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def watch_queue():
    """Watch pgai-queue and ingest files"""
    print(f"[{datetime.now()}] Starting pgai-queue ingestor...")

    while True:
        try:
            # Get all JSON files in queue
            queue_files = sorted(QUEUE_DIR.glob("*.json"))

            for queue_file in queue_files:
                try:
                    # Read data
                    with open(queue_file, 'r') as f:
                        data = json.load(f)

                    # Ingest to database
                    if ingest_to_pgai(data):
                        # Move to processed
                        processed_file = PROCESSED_DIR / queue_file.name
                        queue_file.rename(processed_file)
                        print(f"[{datetime.now()}] Ingested: {queue_file.name}")
                    else:
                        print(f"[{datetime.now()}] Failed: {queue_file.name}")
                        time.sleep(1)

                except json.JSONDecodeError as e:
                    print(f"[{datetime.now()}] Invalid JSON in {queue_file.name}: {e}")
                except PermissionError as e:
                    print(f"[{datetime.now()}] Permission denied for {queue_file.name}: {e}")
                except FileNotFoundError:
                    print(f"[{datetime.now()}] File disappeared: {queue_file.name}")
                except OSError as e:
                    print(f"[{datetime.now()}] OS error processing {queue_file.name}: {e}")

            time.sleep(10)

        except KeyboardInterrupt:
            print(f"\n[{datetime.now()}] Stopping pgai-queue ingestor")
            break
        except Exception as e:
            print(f"[{datetime.now()}] Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    watch_queue()
