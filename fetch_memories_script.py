
import psycopg2
import json
import os
import time

def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="wolf_logic",
        user="wolf",
        password="wolflogic2024",
        port="5433"
    )

def fetch_memories(limit_tokens=75000, chunk_size_tokens=19000):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Updated query based on api/memory_api.py schema
        cur.execute("""
            SELECT content, created_at
            FROM memories
            ORDER BY created_at DESC
            LIMIT 5000;
        """)
        
        memories = []
        current_token_count = 0
        
        for row in cur.fetchall():
            content = row[0]
            if content:
                # Simple approximation: 1 token ~ 4 characters
                content_tokens = len(content) / 4 
                
                if current_token_count + content_tokens <= limit_tokens:
                    memories.append(content)
                    current_token_count += content_tokens
                else:
                    break # Reached token limit
        
        print(f"Fetched approximately {int(current_token_count)} tokens of memories.")
        return memories
    except Exception as e:
        print(f"Error fetching memories: {e}")
        return []
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    memory_contents = fetch_memories()
    
    # Save to a temporary file
    temp_dir = os.environ.get('GEMINI_TEMP_DIR', '/tmp') # Use provided temp dir or default
    temp_file_path = os.path.join(temp_dir, 'injected_memories.json')
    
    with open(temp_file_path, 'w') as f:
        json.dump(memory_contents, f, indent=2)
    
    print(f"Memories saved to {temp_file_path}")

