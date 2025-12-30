import psycopg2
import psycopg2.extras
import os

DB_CONFIG = {
    'host': '100.110.82.181',
    'port': 5433,
    'database': 'wolf_logic',
    'user': 'wolf',
    'password': 'wolflogic2024'
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def fetch_memories_for_injection(max_tokens=40000):
    conn = None
    memories_text = []
    current_chars = 0
    max_chars = max_tokens * 4 # Rough estimate: 4 characters per token

    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # 1. Fetch from 'core_identity' namespace first
        cur.execute("SELECT content FROM memories WHERE namespace = 'core_identity' ORDER BY created_at ASC")
        core_identity_memories = cur.fetchall()
        for record in core_identity_memories:
            content = record['content']
            if content:
                content_chars = len(content)
                if current_chars + content_chars < max_chars:
                    memories_text.append(content)
                    current_chars += content_chars
                else:
                    # Truncate if adding the full content exceeds the limit
                    remaining_chars = max_chars - current_chars
                    if remaining_chars > 0:
                        memories_text.append(content[:remaining_chars])
                    break
        
        # 2. Fetch other recent memories until max_chars is reached
        if current_chars < max_chars:
            # Estimate how many more characters are needed and fetch a bit more to be safe
            remaining_chars_needed = max_chars - current_chars
            # Fetch content that is not from 'core_identity'
            cur.execute(f"""
                SELECT content FROM memories 
                WHERE namespace != 'core_identity' 
                ORDER BY created_at DESC 
                LIMIT {int(remaining_chars_needed / 100) + 10} 
                -- Rough estimate for limit, assuming average memory length
            """)
            other_memories = cur.fetchall()
            for record in other_memories:
                content = record['content']
                if content:
                    content_chars = len(content)
                    if current_chars + content_chars < max_chars:
                        memories_text.append(content)
                        current_chars += content_chars
                    else:
                        remaining_chars = max_chars - current_chars
                        if remaining_chars > 0:
                            memories_text.append(content[:remaining_chars])
                        break

        cur.close()
    except Exception as e:
        print(f"Error fetching memories: {e}")
        # Optionally, log the full traceback for debugging
        # import traceback
        # print(traceback.format_exc())
    finally:
        if conn:
            conn.close()
    
    return "\n---\n".join(memories_text) # Join with a separator to distinguish individual memories

if __name__ == '__main__':
    injected_memories = fetch_memories_for_injection()
    print(injected_memories)
