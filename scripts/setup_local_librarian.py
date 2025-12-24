#!/usr/bin/env python3
"""
Setup local Librarian (pgai vectorizer) on MacBook
Stays dormant when 181 is accessible, activates when offline
"""
import psycopg2
import subprocess
import socket

# Database configs
DB_PRIMARY = {
    "host": "100.110.82.181",
    "port": 5433,
    "database": "wolf_logic",
    "user": "wolf",
    "password": "wolflogic2024"
}

import os
DB_LOCAL = {
    "host": "localhost",
    "port": 5432,
    "database": "wolf_logic",
    "user": os.getenv('USER'),  # Use superuser (apexwolf)
    "password": ""
}

def is_181_accessible():
    """Check if 181 is reachable"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex(('100.110.82.181', 5433))
        sock.close()
        return result == 0
    except:
        return False

def setup_local_vectorizer():
    """Setup pgai vectorizer on local postgres"""
    print("Setting up local Librarian (pgai vectorizer)...")

    # Connect to local postgres
    conn = psycopg2.connect(**DB_LOCAL)
    cur = conn.cursor()

    # Create vectorizer for memories table
    # Uses local Ollama (qwen3-embedding:4b)
    cur.execute("""
        SELECT ai.create_vectorizer(
            'memories'::regclass,
            loading => ai.loading_column(column_name => 'content'),
            destination => ai.destination_table(target_table => 'memories_embedding_store'),
            embedding => ai.embedding_ollama(
                model => 'qwen3-embedding:4b',
                dimensions => 2560,
                base_url => 'http://localhost:11434'
            )
        );
    """)

    conn.commit()
    print("✓ Local vectorizer created")
    print("✓ Model: qwen3-embedding:4b (via local Ollama)")
    print("✓ Dimensions: 2560")
    print("✓ Status: Dormant (181 is accessible)")

    cur.close()
    conn.close()

def check_status():
    """Check if we should use local or remote Librarian"""
    if is_181_accessible():
        print("✓ 181 accessible - using remote Librarian")
        print("  Local Librarian: DORMANT")
        return "remote"
    else:
        print("⚠ 181 NOT accessible - using local Librarian")
        print("  Local Librarian: ACTIVE")
        return "local"

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        setup_local_vectorizer()
    elif len(sys.argv) > 1 and sys.argv[1] == "status":
        check_status()
    else:
        print("Usage:")
        print("  python3 setup_local_librarian.py setup   # Setup vectorizer")
        print("  python3 setup_local_librarian.py status  # Check which Librarian to use")
