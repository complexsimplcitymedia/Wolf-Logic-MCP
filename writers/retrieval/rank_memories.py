#!/usr/bin/env python3
"""
Memory Ranking Agent - Uses Llama 3.1 or Mistral to rank existing memories
Adds sentiment_level (1-5) to metadata for priority loading
"""

import psycopg2
import json
import requests
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

OLLAMA_URL = "http://localhost:11434"
RANKING_MODEL = "llama3.1:latest"  # or mistral:latest

PG_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "wolf_logic",
    "user": "wolf",
    "password": "wolflogic2024"
}

RANK_PROMPT = """Analyze this memory and rate its importance/emotional weight on a 1-5 scale:

1 = CRITICAL (constitution, core values, sovereignty, breakthrough moments, key decisions)
2 = IMPORTANT (technical achievements, relationship dynamics, infrastructure wins)  
3 = MODERATE (useful context, preferences, workflow notes)
4 = LOW (routine operations, minor details)
5 = MINIMAL (metadata, timestamps, trivial info)

Memory: {content}

Respond with ONLY a single digit 1-5. No explanation."""

def rank_memory(content, model=RANKING_MODEL):
    """Use Llama/Mistral to rank a memory"""
    if not content or len(content.strip()) < 10:
        return 5  # Trivial
    
    prompt = RANK_PROMPT.format(content=content[:1000])
    
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1, "num_predict": 5}
            },
            timeout=30
        )
        
        if response.status_code != 200:
            return 3  # Default moderate
        
        result = response.json().get("response", "").strip()
        
        # Extract first digit
        for char in result:
            if char.isdigit() and char in '12345':
                return int(char)
        
        return 3
    except Exception as e:
        print(f"Ranking error: {e}", file=sys.stderr)
        return 3

def process_batch(batch, model):
    """Process batch of memories"""
    results = []
    for mem_id, content, metadata in batch:
        sentiment = rank_memory(content, model)
        
        # Update metadata
        meta = metadata if isinstance(metadata, dict) else (json.loads(metadata) if metadata else {})
        meta['sentiment_level'] = sentiment
        
        results.append((sentiment, json.dumps(meta), mem_id))
        
        # Show progress
        preview = content[:50] if content else "empty"
        print(f"[{sentiment}] {preview}...", file=sys.stderr)
    
    return results

def main():
    # Connect
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()
    
    # Get unranked memories
    cur.execute("""
        SELECT id, content, metadata
        FROM memories
        WHERE content IS NOT NULL
        AND (metadata->>'sentiment_level') IS NULL
        ORDER BY created_at DESC
        LIMIT 500
    """)
    
    memories = cur.fetchall()
    print(f"Ranking {len(memories)} memories with {RANKING_MODEL}...", file=sys.stderr)
    
    if not memories:
        print("No unranked memories found", file=sys.stderr)
        return
    
    # Process in batches with 4 parallel workers
    batch_size = 10
    batches = [memories[i:i+batch_size] for i in range(0, len(memories), batch_size)]
    
    updates = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(process_batch, batch, RANKING_MODEL) for batch in batches]
        for future in as_completed(futures):
            updates.extend(future.result())
    
    # Bulk update
    print(f"\nUpdating {len(updates)} memories...", file=sys.stderr)
    for sentiment, meta, mem_id in updates:
        cur.execute("""
            UPDATE memories 
            SET metadata = %s
            WHERE id = %s
        """, (meta, mem_id))
    
    conn.commit()
    
    # Show distribution
    cur.execute("""
        SELECT metadata->>'sentiment_level' as level, COUNT(*) 
        FROM memories 
        WHERE (metadata->>'sentiment_level') IS NOT NULL
        GROUP BY level
        ORDER BY level
    """)
    
    print("\n" + "="*60, file=sys.stderr)
    print("SENTIMENT DISTRIBUTION:", file=sys.stderr)
    print("="*60, file=sys.stderr)
    for level, count in cur.fetchall():
        print(f"Level {level}: {count} memories", file=sys.stderr)
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
