#!/usr/bin/env python3
import psycopg2

def check_librarian():
    conn = psycopg2.connect(
        host="100.110.82.181",
        port=5433,
        user="wolf",
        password="wolflogic2024",
        database="wolf_logic"
    )
    cur = conn.cursor()

    # Health check
    cur.execute("SELECT COUNT(*) FROM memories;")
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM memories_embedding_store;")
    vectorized = cur.fetchone()[0]

    try:
        cur.execute("SELECT * FROM ai.vectorizer_status WHERE target_table = 'memories_embedding_store' LIMIT 1;")
        vectorizer_status = cur.fetchone()
    except:
        vectorizer_status = None

    print(f"Total memories: {total}")
    print(f"Vectorized: {vectorized}")
    print(f"Vectorizer status: {'Active' if vectorizer_status else 'Unknown'}")

    # Pull recent memories (50K tokens ≈ 200K chars)
    cur.execute("""
        SELECT content FROM memories
        WHERE namespace = 'scripty'
        ORDER BY created_at DESC
        LIMIT 150;
    """)

    memories = []
    char_count = 0
    for row in cur.fetchall():
        if char_count >= 200000:
            break
        content = row[0] if row[0] else ""
        memories.append(content)
        char_count += len(content)

    print(f"\nRecent memories pulled: {len(memories)} entries, ~{char_count//4} tokens")
    print("\n=== RECENT CONTEXT ===")
    for i, mem in enumerate(memories[:5]):
        print(f"\n[{i+1}] {mem[:500]}..." if len(mem) > 500 else f"\n[{i+1}] {mem}")

    conn.close()
    return memories

if __name__ == "__main__":
    check_librarian()
