#!/usr/bin/env python3
"""
Optimized Verbatim Processor - Delegates to embed models fleet
Uses qwen2.5:0.5b for fast extraction, embed models handle semantic processing
pgai vectorizer handles embeddings automatically
"""

import psycopg2
import json
import requests
import sys
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

OLLAMA_URL = "http://localhost:11434"
EXTRACTION_MODEL = "qwen2.5:0.5b"  # Fast extraction model

PG_CONFIG = {
    "host": "100.110.82.181",
    "port": 5433,
    "database": "wolf_logic",
    "user": "wolf",
    "password": "wolflogic2024"
}

# Simple extraction prompt for fast model
EXTRACT_PROMPT = """Extract from this text:
Keywords: (5-10 key terms)
Category: (infrastructure/protocol/sovereignty/development/technical/philosophical/operational)
Importance: (1-10)
Summary: (one sentence)

Text: {content}

Output format:
keywords: word1, word2, word3
category: category_name
importance: 7
summary: brief summary"""

def extract_metadata(content):
    """Fast extraction with qwen2.5:0.5b"""
    if not content or len(content.strip()) < 50:
        return None

    prompt = EXTRACT_PROMPT.format(content=content[:1000])

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": EXTRACTION_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1, "num_predict": 100}
            },
            timeout=15
        )

        if response.status_code != 200:
            return None

        result = response.json().get("response", "").strip()

        # Parse simple format
        metadata = {
            'keywords': [],
            'category': 'general',
            'importance': 5,
            'summary': ''
        }

        for line in result.split('\n'):
            line = line.strip()
            if line.startswith('keywords:'):
                keywords = line.replace('keywords:', '').strip()
                metadata['keywords'] = [k.strip() for k in keywords.split(',') if k.strip()]
            elif line.startswith('category:'):
                metadata['category'] = line.replace('category:', '').strip()
            elif line.startswith('importance:'):
                try:
                    metadata['importance'] = int(line.replace('importance:', '').strip())
                except:
                    pass
            elif line.startswith('summary:'):
                metadata['summary'] = line.replace('summary:', '').strip()

        return metadata

    except Exception as e:
        print(f"Extraction error: {e}", file=sys.stderr)
        return None

def process_batch(batch):
    """Process batch quickly with extraction model"""
    results = []
    for mem_id, content in batch:
        metadata = extract_metadata(content)
        if metadata:
            results.append((mem_id, metadata))
            print(f"[{metadata['category']}:{metadata['importance']}] {mem_id}", file=sys.stderr)
    return results

def main():
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()

    # Get unprocessed captures
    cur.execute("""
        SELECT id, content
        FROM memories
        WHERE namespace = 'stenographer'
        AND content IS NOT NULL
        AND LENGTH(content) > 50
        AND (metadata IS NULL OR NOT (metadata ? 'keywords'))
        ORDER BY created_at DESC
        LIMIT 200
    """)

    captures = cur.fetchall()

    if not captures:
        print("No unprocessed captures", file=sys.stderr)
        return

    print(f"Processing {len(captures)} captures with {EXTRACTION_MODEL}...", file=sys.stderr)

    # Fast parallel processing with small model
    batch_size = 20
    batches = [captures[i:i+batch_size] for i in range(0, len(captures), batch_size)]

    all_results = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(process_batch, batch) for batch in batches]
        for future in as_completed(futures):
            all_results.extend(future.result())

    # Bulk update - let pgai vectorizer handle embeddings automatically
    print(f"\nUpdating {len(all_results)} memories...", file=sys.stderr)

    for mem_id, metadata in all_results:
        cur.execute("""
            UPDATE memories
            SET metadata = COALESCE(metadata, '{}'::jsonb) || %s::jsonb
            WHERE id = %s
        """, (json.dumps({
            'keywords': metadata['keywords'],
            'processed_category': metadata['category'],
            'processed_importance': metadata['importance'],
            'processed_summary': metadata['summary'],
            'processed_at': datetime.now().isoformat()
        }), mem_id))

    conn.commit()

    # Stats
    cur.execute("""
        SELECT
            metadata->>'processed_category' as category,
            COUNT(*) as count
        FROM memories
        WHERE namespace = 'stenographer'
        AND metadata ? 'keywords'
        GROUP BY category
        ORDER BY count DESC
    """)

    print("\n" + "="*80, file=sys.stderr)
    print("PROCESSED CAPTURES:", file=sys.stderr)
    for category, count in cur.fetchall():
        print(f"  {category}: {count}", file=sys.stderr)

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
