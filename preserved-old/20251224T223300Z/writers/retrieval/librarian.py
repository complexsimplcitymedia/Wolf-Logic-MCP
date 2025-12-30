#!/usr/bin/env python3
"""
The Librarian - pgai's faithful servant
Watches for conversation dumps, extracts memories, feeds them to pgai

Workflow:
1. Watch memory-dumps directory for new files
2. Process dump with qwen2.5:0.5b to extract key facts/memories
3. Generate embeddings with nomic-embed-text
4. Store in wolf_logic database following the memory schema
"""

import os
import sys
import json
import time
import uuid
import hashlib
import requests
import psycopg2
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configuration
DUMP_DIR = "/mnt/Wolf-code/Wolf-Ai-Enterptises/memory-dumps"
OLLAMA_URL = "http://localhost:11434"
LLM_MODEL = "qwen2.5:0.5b"
EMBED_MODEL = "nomic-embed-text:v1.5"

# Postgres config
PG_CONFIG = {
    "host": "localhost",
    "port": 5434,
    "database": "wolf_logic",
    "user": "wolf",
    "password": "wolflogic2024"
}

# Extraction prompt
EXTRACT_PROMPT = """You are a memory extraction agent. Analyze this conversation dump and extract key facts, decisions, configurations, and important information that should be remembered for future sessions.

For each memory, output a JSON object with:
- memory: the fact/knowledge (concise, self-contained)
- category: one of [infrastructure, preference, decision, configuration, workflow, context]
- subcategory: more specific classification
- tags: relevant keywords
- importance: 1-10 scale
- summary: one-line summary

Output ONLY a JSON array of memory objects. No other text.

CONVERSATION DUMP:
{dump_content}

Extract the most important 10-20 memories from this conversation:"""


# pgai handles embeddings automatically via triggers
# Just insert text into memories table and pgai does the rest


def extract_memories(dump_content: str) -> list:
    """Use LLM to extract memories from dump"""
    # Truncate if too long (qwen2.5:0.5b has limited context)
    max_chars = 8000
    if len(dump_content) > max_chars:
        # Take start and end
        dump_content = dump_content[:max_chars//2] + "\n...[truncated]...\n" + dump_content[-max_chars//2:]

    prompt = EXTRACT_PROMPT.format(dump_content=dump_content)

    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": LLM_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.1}
        }
    )

    if response.status_code != 200:
        print(f"LLM error: {response.status_code}")
        return []

    result = response.json().get("response", "")

    # Parse JSON from response
    try:
        # Find JSON array in response
        start = result.find("[")
        end = result.rfind("]") + 1
        if start >= 0 and end > start:
            return json.loads(result[start:end])
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")

    return []


def store_memory(conn, memory: dict, source_file: str):
    """Store a memory in pgai - embeddings generated automatically by triggers"""
    now = datetime.now()

    metadata = {
        "source": "conversation_dump",
        "source_file": source_file,
        "extraction_model": LLM_MODEL,
        "extracted_at": now.isoformat(),
        "subcategory": memory.get("subcategory", ""),
        "tags": memory.get("tags", []),
        "importance": memory.get("importance", 5),
        "summary": memory.get("summary", "")
    }

    try:
        with conn.cursor() as cur:
            # Just insert - pgai triggers handle embedding automatically
            cur.execute("""
                INSERT INTO memories (user_id, content, metadata, memory_type, namespace, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                "claude_session",
                memory.get("memory", ""),
                json.dumps(metadata),
                memory.get("category", "general"),
                "wolf_logic",
                now,
                now
            ))
        conn.commit()
        return True
    except Exception as e:
        print(f"DB error: {e}")
        conn.rollback()
        return False


def process_dump(filepath: str):
    """Process a conversation dump file"""
    print(f"\n{'='*60}")
    print(f"LIBRARIAN: Processing {filepath}")
    print(f"{'='*60}")

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    print(f"Dump size: {len(content)} chars")

    # Extract memories
    print("Extracting memories with LLM...")
    memories = extract_memories(content)
    print(f"Extracted {len(memories)} memories")

    if not memories:
        print("No memories extracted")
        return

    # Connect to database
    try:
        conn = psycopg2.connect(**PG_CONFIG)
    except Exception as e:
        print(f"Database connection failed: {e}")
        return

    # Store each memory
    stored = 0
    for mem in memories:
        if store_memory(conn, mem, os.path.basename(filepath)):
            stored += 1
            print(f"  Stored: {mem.get('memory', '')[:60]}...")

    conn.close()

    print(f"\nStored {stored}/{len(memories)} memories")

    # Mark file as processed
    processed_marker = filepath + ".processed"
    Path(processed_marker).touch()
    print(f"Marked as processed: {processed_marker}")


class DumpHandler(FileSystemEventHandler):
    """Watch for new dump files"""

    def on_created(self, event):
        if event.is_directory:
            return

        filepath = event.src_path

        # Skip processed files and markers
        if filepath.endswith(".processed") or filepath.endswith(".log"):
            return

        # Wait for file to be fully written
        time.sleep(1)

        # Check if already processed
        if os.path.exists(filepath + ".processed"):
            return

        process_dump(filepath)


def main():
    """Main entry point"""
    print("="*60)
    print("THE LIBRARIAN - pgai's Memory Keeper")
    print("="*60)
    print(f"Watching: {DUMP_DIR}")
    print(f"LLM: {LLM_MODEL}")
    print(f"Embedder: {EMBED_MODEL}")
    print(f"Database: {PG_CONFIG['database']}@{PG_CONFIG['host']}:{PG_CONFIG['port']}")
    print("="*60)

    # Process any existing unprocessed dumps
    for f in os.listdir(DUMP_DIR):
        filepath = os.path.join(DUMP_DIR, f)
        if os.path.isfile(filepath) and not f.endswith(".processed") and not f.endswith(".log"):
            if not os.path.exists(filepath + ".processed"):
                process_dump(filepath)

    # Start watching
    observer = Observer()
    observer.schedule(DumpHandler(), DUMP_DIR, recursive=False)
    observer.start()

    print("\nWatching for new dumps... (Ctrl+C to stop)")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()


if __name__ == "__main__":
    main()
