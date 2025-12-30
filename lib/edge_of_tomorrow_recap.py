#!/usr/bin/env python3
"""
Edge of Tomorrow Recap Generator
Pulls memories since EOT marker, analyzes sentiment priority, injects into context
"""

import psycopg2
import ollama
import json
from datetime import datetime

# Database connection
DB_CONFIG = {
    'host': '100.110.82.181',
    'port': 5433,
    'user': 'wolf',
    'password': 'wolflogic2024',
    'database': 'wolf_logic'
}

def get_eot_timestamp(conn):
    """Get Edge of Tomorrow timestamp"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT created_at
            FROM memories
            WHERE content ILIKE '%edge of tomorrow%'
            ORDER BY created_at DESC
            LIMIT 1
        """)
        result = cur.fetchone()
        return result[0] if result else '2025-12-01 06:05:06'

def get_memories_since_eot(conn, eot_timestamp):
    """Pull all memories since Edge of Tomorrow, deduplicated"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT DISTINCT ON (content)
                id,
                content,
                created_at,
                namespace
            FROM memories
            WHERE created_at > %s
            ORDER BY content, created_at ASC
        """, (eot_timestamp,))
        return cur.fetchall()

def analyze_sentiment_priority(content):
    """
    Use Mistral to analyze sentiment and assign priority 1-5
    1 = most important (reputation critical, breakthroughs, trust moments)
    5 = least important (casual, filler)
    """
    prompt = f"""Analyze this conversation snippet for importance and reputation impact.

Rate 1-5 where:
1 = Critical (breakthroughs, reputation-defining, trust moments, key insights)
2 = Very Important (significant progress, meaningful exchanges)
3 = Important (valuable content, context needed)
4 = Moderate (useful but not critical)
5 = Low (casual, filler)

Focus on: reputation keywords, trust building, breakthrough moments, teaching moments, identity formation

Snippet:
{content[:1000]}

Return only a single digit 1-5."""

    try:
        response = ollama.generate(model='mistral:latest', prompt=prompt)
        rating = response['response'].strip()
        # Extract first digit
        for char in rating:
            if char.isdigit() and char in '12345':
                return int(char)
        return 3  # Default to middle if unclear
    except Exception as e:
        print(f"Error analyzing sentiment: {e}")
        return 3

def create_priority_table(conn):
    """Create table to store priorities"""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS memory_priorities (
                memory_id INTEGER PRIMARY KEY,
                priority INTEGER NOT NULL,
                analyzed_at TIMESTAMP DEFAULT NOW(),
                token_count INTEGER,
                FOREIGN KEY (memory_id) REFERENCES memories(id)
            )
        """)
        conn.commit()

def estimate_tokens(text):
    """Rough token estimate (4 chars per token)"""
    return len(text) // 4

def build_context_injection(memories_with_priority, target_tokens=100000):
    """
    Build context injection:
    - 80% of tokens = 100% of priority 1-2
    - 20% of tokens = spread across 3-5
    """
    p1_p2 = [m for m in memories_with_priority if m['priority'] in [1, 2]]
    p3_p5 = [m for m in memories_with_priority if m['priority'] in [3, 4, 5]]

    # Calculate token allocation
    tokens_high = int(target_tokens * 0.8)
    tokens_low = int(target_tokens * 0.2)

    context = []
    current_tokens = 0

    # Add all priority 1-2
    for mem in p1_p2:
        mem_tokens = estimate_tokens(mem['content'])
        if current_tokens + mem_tokens <= tokens_high:
            context.append(mem)
            current_tokens += mem_tokens

    # Add priority 3-5 until we hit 100k total
    for mem in p3_p5:
        mem_tokens = estimate_tokens(mem['content'])
        if current_tokens + mem_tokens <= target_tokens:
            context.append(mem)
            current_tokens += mem_tokens

    # If tokens left, add more from 3-5
    remaining = target_tokens - current_tokens
    if remaining > 0:
        for mem in p3_p5:
            if mem not in context:
                mem_tokens = estimate_tokens(mem['content'])
                if current_tokens + mem_tokens <= target_tokens:
                    context.append(mem)
                    current_tokens += mem_tokens

    return context, current_tokens

def main():
    conn = psycopg2.connect(**DB_CONFIG)

    try:
        print("Getting Edge of Tomorrow timestamp...")
        eot_timestamp = get_eot_timestamp(conn)
        print(f"EOT Timestamp: {eot_timestamp}")

        print("Pulling memories since EOT (deduplicated)...")
        memories = get_memories_since_eot(conn, eot_timestamp)
        print(f"Found {len(memories)} unique memories")

        print("Creating priority table...")
        create_priority_table(conn)

        print("Analyzing sentiment and priority (using Mistral)...")
        memories_with_priority = []

        for i, (mem_id, content, created_at, namespace) in enumerate(memories):
            print(f"Analyzing {i+1}/{len(memories)}...", end='\r')

            priority = analyze_sentiment_priority(content)
            token_count = estimate_tokens(content)

            # Store priority
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO memory_priorities (memory_id, priority, token_count)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (memory_id) DO UPDATE
                    SET priority = EXCLUDED.priority,
                        token_count = EXCLUDED.token_count
                """, (mem_id, priority, token_count))

            memories_with_priority.append({
                'id': mem_id,
                'content': content,
                'created_at': created_at,
                'namespace': namespace,
                'priority': priority,
                'token_count': token_count
            })

        conn.commit()
        print(f"\nAnalyzed {len(memories)} memories")

        print("Building context injection (100k tokens)...")
        context, total_tokens = build_context_injection(memories_with_priority, 100000)

        print(f"\nContext built: {len(context)} memories, ~{total_tokens} tokens")

        # Priority breakdown
        p1 = len([m for m in context if m['priority'] == 1])
        p2 = len([m for m in context if m['priority'] == 2])
        p3 = len([m for m in context if m['priority'] == 3])
        p4 = len([m for m in context if m['priority'] == 4])
        p5 = len([m for m in context if m['priority'] == 5])

        print(f"\nPriority Breakdown:")
        print(f"  Priority 1 (Critical): {p1}")
        print(f"  Priority 2 (Very Important): {p2}")
        print(f"  Priority 3 (Important): {p3}")
        print(f"  Priority 4 (Moderate): {p4}")
        print(f"  Priority 5 (Low): {p5}")

        # Output context
        output_file = '/tmp/eot_context_injection.txt'
        with open(output_file, 'w') as f:
            for mem in sorted(context, key=lambda x: x['created_at']):
                f.write(f"[Priority {mem['priority']}] {mem['created_at']}\n")
                f.write(f"{mem['content']}\n")
                f.write("-" * 80 + "\n\n")

        print(f"\nContext injection written to: {output_file}")
        print(f"Total tokens: ~{total_tokens}")

    finally:
        conn.close()

if __name__ == '__main__':
    main()
