#!/usr/bin/env python3
"""
The Librarian Fleet - Parallel Memory Processing
Uses all available Ollama models to process dumps concurrently

Architecture:
- Chunk dumps into segments
- Fan out to multiple LLM workers for extraction
- Parallel embedding generation
- Aggregate and store in pgai
"""

import os
import json
import time
import uuid
import requests
import psycopg2
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Configuration
DUMP_DIR = "/mnt/Wolf-code/Wolf-Ai-Enterptises/memory-dumps"
OLLAMA_URL = "http://localhost:11434"

# The Fleet
LLM_MODELS = ["qwen2.5:0.5b"]  # For extraction/summarization
EMBED_MODELS = [
    "nomic-embed-text:v1.5",
    "bge-large:latest",
    "mxbai-embed-large:latest",
    "snowflake-arctic-embed:137m",
]

# Postgres config
PG_CONFIG = {
    "host": "100.110.82.181",
    "port": 5433,
    "database": "wolf_logic",
    "user": "wolf",
    "password": "wolflogic2024"
}

# Thread-safe print
print_lock = threading.Lock()
def safe_print(msg):
    with print_lock:
        print(msg)

EXTRACT_PROMPT = """Extract key facts and memories from this conversation segment. Output a JSON array of objects with: memory, category, subcategory, tags, importance (1-10), summary.

Categories: infrastructure, preference, decision, configuration, workflow, context

SEGMENT:
{content}

JSON array (10-15 memories max):"""


def chunk_content(content: str, chunk_size: int = 4000, overlap: int = 200) -> list:
    """Split content into overlapping chunks"""
    chunks = []
    start = 0
    while start < len(content):
        end = start + chunk_size
        chunk = content[start:end]
        chunks.append(chunk)
        start = end - overlap
    return chunks


def extract_with_llm(chunk: str, model: str, chunk_id: int) -> list:
    """Extract memories from a chunk using specified LLM"""
    safe_print(f"  [Worker {chunk_id}] Extracting with {model}...")

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": model,
                "prompt": EXTRACT_PROMPT.format(content=chunk),
                "stream": False,
                "options": {"temperature": 0.1, "num_predict": 2000}
            },
            timeout=120
        )

        if response.status_code != 200:
            safe_print(f"  [Worker {chunk_id}] LLM error: {response.status_code}")
            return []

        result = response.json().get("response", "")

        # Parse JSON
        start = result.find("[")
        end = result.rfind("]") + 1
        if start >= 0 and end > start:
            memories = json.loads(result[start:end])
            safe_print(f"  [Worker {chunk_id}] Extracted {len(memories)} memories")
            return memories
    except Exception as e:
        safe_print(f"  [Worker {chunk_id}] Error: {e}")

    return []


def store_memories_batch(memories: list, source_file: str):
    """Store memories in pgai - embeddings handled by triggers"""
    if not memories:
        return 0

    try:
        conn = psycopg2.connect(**PG_CONFIG)
        stored = 0
        now = datetime.now()

        with conn.cursor() as cur:
            for mem in memories:
                try:
                    metadata = {
                        "source": "conversation_dump",
                        "source_file": source_file,
                        "extraction_model": "qwen2.5:0.5b",
                        "extracted_at": now.isoformat(),
                        "subcategory": mem.get("subcategory", ""),
                        "tags": mem.get("tags", []),
                        "importance": mem.get("importance", 5),
                        "summary": mem.get("summary", "")
                    }

                    cur.execute("""
                        INSERT INTO memories (user_id, content, metadata, memory_type, namespace, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        "claude_session",
                        mem.get("memory", ""),
                        json.dumps(metadata),
                        mem.get("category", "general"),
                        "wolf_logic",
                        now,
                        now
                    ))
                    stored += 1
                except Exception as e:
                    safe_print(f"  Insert error: {e}")
                    conn.rollback()
                    continue

            conn.commit()
        conn.close()
        return stored
    except Exception as e:
        safe_print(f"DB connection error: {e}")
        return 0


def deduplicate_memories(all_memories: list) -> list:
    """Remove duplicate memories based on content similarity"""
    seen = set()
    unique = []

    for mem in all_memories:
        # Simple dedup based on memory text
        content = mem.get("memory", "").lower().strip()
        content_hash = hash(content[:100])  # First 100 chars

        if content_hash not in seen and len(content) > 10:
            seen.add(content_hash)
            unique.append(mem)

    return unique


def process_dump_parallel(filepath: str):
    """Process dump using parallel workers"""
    print(f"\n{'='*60}")
    print(f"LIBRARIAN FLEET: Processing {os.path.basename(filepath)}")
    print(f"{'='*60}")

    # Read dump
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    print(f"Dump size: {len(content):,} chars")

    # Chunk it
    chunks = chunk_content(content, chunk_size=6000, overlap=300)
    print(f"Split into {len(chunks)} chunks")

    # Parallel extraction
    all_memories = []
    print(f"\nDeploying {len(chunks)} workers...")

    with ThreadPoolExecutor(max_workers=min(8, len(chunks))) as executor:
        futures = {
            executor.submit(extract_with_llm, chunk, LLM_MODELS[0], i): i
            for i, chunk in enumerate(chunks)
        }

        for future in as_completed(futures):
            chunk_id = futures[future]
            try:
                memories = future.result()
                all_memories.extend(memories)
            except Exception as e:
                safe_print(f"  [Worker {chunk_id}] Failed: {e}")

    print(f"\nTotal extracted: {len(all_memories)} memories")

    # Deduplicate
    unique_memories = deduplicate_memories(all_memories)
    print(f"After dedup: {len(unique_memories)} unique memories")

    # Store
    print("\nStoring in pgai...")
    stored = store_memories_batch(unique_memories, os.path.basename(filepath))
    print(f"Stored: {stored} memories")

    # Mark processed
    Path(filepath + ".processed").touch()
    print(f"\nDone! Marked as processed.")

    return stored


def main():
    print("="*60)
    print("THE LIBRARIAN FLEET")
    print("Parallel Memory Processing System")
    print("="*60)
    print(f"LLM Models: {LLM_MODELS}")
    print(f"Workers: ThreadPool")
    print(f"Target: pgai @ {PG_CONFIG['database']}")
    print("="*60)

    # Process existing dumps
    for f in sorted(os.listdir(DUMP_DIR)):
        filepath = os.path.join(DUMP_DIR, f)
        if os.path.isfile(filepath) and not f.endswith((".processed", ".log")):
            if not os.path.exists(filepath + ".processed"):
                process_dump_parallel(filepath)

    print("\nAll dumps processed. Exiting.")


if __name__ == "__main__":
    main()
