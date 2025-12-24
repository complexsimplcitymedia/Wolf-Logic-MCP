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
SENTIMENT_MODEL = "mistral:latest"  # For sentiment ranking
EMBED_MODELS = [
    "nomic-embed-text:v1.5",
    "bge-large:latest",
    "mxbai-embed-large:latest",
    "snowflake-arctic-embed:137m",
]
KEYWORD_MODELS = EMBED_MODELS  # Use embed models for keyword extraction

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


def store_memories_batch(memories: list, source_file: str, keywords: list = None, sentiment: int = 3):
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
                        "summary": mem.get("summary", ""),
                        "swarm_keywords": keywords or [],
                        "sentiment": sentiment,
                        "sentiment_model": "mistral:latest"
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


def extract_keywords_parallel(content: str) -> list:
    """Extract keywords using multiple models in parallel"""
    safe_print("  [Keywords] Extracting with model swarm...")

    keyword_prompt = f"""Extract the 10-15 most important keywords/phrases from this text. Output ONLY a JSON array of strings.

TEXT:
{content[:3000]}

JSON array of keywords:"""

    all_keywords = []

    with ThreadPoolExecutor(max_workers=len(KEYWORD_MODELS)) as executor:
        futures = {
            executor.submit(
                lambda m: requests.post(
                    f"{OLLAMA_URL}/api/generate",
                    json={"model": m, "prompt": keyword_prompt, "stream": False, "options": {"temperature": 0.1}},
                    timeout=60
                ).json().get("response", ""),
                model
            ): model
            for model in KEYWORD_MODELS
        }

        for future in as_completed(futures):
            model = futures[future]
            try:
                result = future.result()
                start = result.find("[")
                end = result.rfind("]") + 1
                if start >= 0 and end > start:
                    keywords = json.loads(result[start:end])
                    all_keywords.extend(keywords)
            except Exception as e:
                safe_print(f"  [Keywords] {model} failed: {e}")

    # Deduplicate and return top keywords
    unique_keywords = list(set(all_keywords))
    safe_print(f"  [Keywords] Extracted {len(unique_keywords)} unique keywords")
    return unique_keywords[:20]


def get_sentiment(content: str) -> int:
    """Get sentiment ranking 1-5 from Mistral"""
    safe_print("  [Sentiment] Analyzing with Mistral...")

    sentiment_prompt = f"""Analyze the sentiment and emotional tone of this conversation. Rate from 1-5:
1 = Very Negative (conflict, frustration, errors)
2 = Somewhat Negative (challenges, issues)
3 = Neutral (informational, factual)
4 = Somewhat Positive (progress, solutions)
5 = Very Positive (breakthroughs, success)

Output ONLY the number (1-5).

CONVERSATION:
{content[:4000]}

Rating:"""

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": SENTIMENT_MODEL,
                "prompt": sentiment_prompt,
                "stream": False,
                "options": {"temperature": 0.1}
            },
            timeout=90
        )

        if response.status_code == 200:
            result = response.json().get("response", "3").strip()
            # Extract first digit
            for char in result:
                if char.isdigit():
                    rating = int(char)
                    if 1 <= rating <= 5:
                        safe_print(f"  [Sentiment] Rating: {rating}/5")
                        return rating
    except Exception as e:
        safe_print(f"  [Sentiment] Error: {e}")

    safe_print("  [Sentiment] Defaulting to 3/5 (neutral)")
    return 3


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

    # === PHASE 1: Model Swarm Analysis ===
    print(f"\n{'='*60}")
    print("PHASE 1: Model Swarm Analysis")
    print(f"{'='*60}")

    # Extract keywords using multiple models in parallel
    keywords = extract_keywords_parallel(content)

    # Get sentiment from Mistral
    sentiment = get_sentiment(content)

    print(f"\nSwarm Analysis Complete:")
    print(f"  Keywords: {len(keywords)}")
    print(f"  Sentiment: {sentiment}/5")

    # === PHASE 2: Memory Extraction ===
    print(f"\n{'='*60}")
    print("PHASE 2: Memory Extraction")
    print(f"{'='*60}")

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

    # === PHASE 3: Store to pgai ===
    print(f"\n{'='*60}")
    print("PHASE 3: Handoff to pgai")
    print(f"{'='*60}")
    print("Storing memories with swarm metadata...")
    stored = store_memories_batch(unique_memories, os.path.basename(filepath), keywords, sentiment)
    print(f"Stored: {stored} memories")
    print("pgai will handle vectorization via triggers")

    # Mark processed
    Path(filepath + ".processed").touch()
    print(f"\nDone! Marked as processed.")

    return stored


def main():
    print("="*60)
    print("THE LIBRARIAN FLEET - UNION WAY")
    print("Parallel Memory Processing System")
    print("="*60)
    print(f"Extraction: {LLM_MODELS}")
    print(f"Keywords: {len(KEYWORD_MODELS)} models in swarm")
    print(f"Sentiment: {SENTIMENT_MODEL}")
    print(f"Storage: pgai @ {PG_CONFIG['database']}")
    print(f"Vectorization: pgai auto-triggers")
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
