#!/usr/bin/env python3
"""
Verbatim Processor - Uses Llama 3.1 / Mistral to process raw stenographer captures
Extracts keywords, categories, importance scores from verbatim data

Runs periodically to process unprocessed stenographer captures
"""

import psycopg2
import json
import requests
import sys
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

OLLAMA_URL = "http://localhost:11434"
PROCESSING_MODEL = "llama3.1:latest"  # or mistral:latest

PG_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "wolf_logic",
    "user": "wolf",
    "password": "wolflogic2024"
}

ANALYSIS_PROMPT = """Analyze this verbatim conversation capture and extract:
1. Main keywords (5-10 key terms)
2. Primary category (infrastructure, protocol, sovereignty, development, technical, philosophical, operational)
3. Importance score (1-10, where 10 is critical)
4. Brief summary (one sentence)

Verbatim text:
{content}

Return ONLY valid JSON with this structure:
{{"keywords": ["keyword1", "keyword2"], "category": "category_name", "importance": 8, "summary": "brief summary"}}
"""

def process_verbatim(memory_id, content, model=PROCESSING_MODEL):
    """Process verbatim capture with LLM"""
    if not content or len(content.strip()) < 50:
        return None

    prompt = ANALYSIS_PROMPT.format(content=content[:2000])

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1, "num_predict": 200}
            },
            timeout=30
        )

        if response.status_code != 200:
            return None

        result = response.json().get("response", "").strip()

        # Extract JSON from response
        start = result.find("{")
        end = result.rfind("}") + 1
        if start >= 0 and end > start:
            analysis = json.loads(result[start:end])
            return {
                'memory_id': memory_id,
                'keywords': analysis.get('keywords', []),
                'category': analysis.get('category', 'general'),
                'importance': analysis.get('importance', 5),
                'summary': analysis.get('summary', '')
            }
    except Exception as e:
        print(f"Processing error for {memory_id}: {e}", file=sys.stderr)

    return None

def process_batch(batch, model):
    """Process batch of verbatim captures"""
    results = []
    for mem_id, content in batch:
        analysis = process_verbatim(mem_id, content, model)
        if analysis:
            results.append(analysis)
            print(f"[{analysis['category']}:{analysis['importance']}] {mem_id} - {analysis['summary'][:60]}...", file=sys.stderr)
    return results

def main():
    """Process unprocessed stenographer captures"""
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()

    # Get unprocessed stenographer captures (no keywords in metadata)
    cur.execute("""
        SELECT id, content
        FROM memories
        WHERE namespace = 'stenographer'
        AND content IS NOT NULL
        AND LENGTH(content) > 50
        AND (metadata IS NULL OR NOT (metadata ? 'keywords'))
        ORDER BY created_at DESC
        LIMIT 500
    """)

    captures = cur.fetchall()

    if not captures:
        print("No unprocessed captures", file=sys.stderr)
        return

    print(f"Processing {len(captures)} stenographer captures with {PROCESSING_MODEL}...", file=sys.stderr)

    # Process in parallel batches
    batch_size = 10
    batches = [captures[i:i+batch_size] for i in range(0, len(captures), batch_size)]

    all_results = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(process_batch, batch, PROCESSING_MODEL) for batch in batches]
        for future in as_completed(futures):
            all_results.extend(future.result())

    # Update memories with analysis
    print(f"\nUpdating {len(all_results)} memories with extracted metadata...", file=sys.stderr)

    for result in all_results:
        cur.execute("""
            UPDATE memories
            SET metadata = COALESCE(metadata, '{}'::jsonb) || %s::jsonb
            WHERE id = %s
        """, (json.dumps({
            'keywords': result['keywords'],
            'processed_category': result['category'],
            'processed_importance': result['importance'],
            'processed_summary': result['summary'],
            'processed_at': datetime.now().isoformat(),
            'processed_by': PROCESSING_MODEL
        }), result['memory_id']))

    conn.commit()

    # Show stats
    cur.execute("""
        SELECT
            metadata->>'processed_category' as category,
            COUNT(*) as count,
            AVG((metadata->>'processed_importance')::int) as avg_importance
        FROM memories
        WHERE namespace = 'stenographer'
        AND metadata ? 'keywords'
        GROUP BY category
        ORDER BY count DESC
    """)

    print("\n" + "="*80, file=sys.stderr)
    print("PROCESSED STENOGRAPHER DATA:", file=sys.stderr)
    print("="*80, file=sys.stderr)
    for category, count, avg_imp in cur.fetchall():
        print(f"{category}: {count} captures, avg importance: {avg_imp:.1f}", file=sys.stderr)

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
