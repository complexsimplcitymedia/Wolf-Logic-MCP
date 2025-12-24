#!/usr/bin/env python3
"""
Session Manager - Proactive memory and state management
Runs in background, monitors token usage, manages context, stores state

Not reactive. PROACTIVE.
"""

import os
import sys
import json
import time
import psycopg2
import requests
from datetime import datetime
from pathlib import Path

# Paths
SESSION_STATE_FILE = "/tmp/claude_session_state.json"
MEMORY_DUMPS_DIR = "/mnt/Wolf-code/Wolf-Ai-Enterptises/memory-dumps"
DAILYS_DIR = "/mnt/Wolf-code/Wolf-Ai-Enterptises/camera/dailys"

# Postgres
PG_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "wolf_logic",
    "user": "wolf",
    "password": "wolflogic2024"
}

# Ollama
OLLAMA_URL = "http://localhost:11434"

class SessionManager:
    def __init__(self):
        self.state = self.load_state()
        self.conn = psycopg2.connect(**PG_CONFIG)

    def load_state(self):
        """Load session state from disk"""
        if os.path.exists(SESSION_STATE_FILE):
            with open(SESSION_STATE_FILE, 'r') as f:
                return json.load(f)
        return {
            "session_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "token_count": 0,
            "context_loaded": [],
            "last_memory_query": None,
            "critical_memories_loaded": False,
            "started_at": datetime.now().isoformat()
        }

    def save_state(self):
        """Persist state to disk"""
        with open(SESSION_STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def load_critical_context(self):
        """Load constitution, protocols, key memories at session start"""
        if self.state["critical_memories_loaded"]:
            return

        print("Loading critical context...", file=sys.stderr)

        # Priority namespaces
        priorities = [
            ('core_identity', 10),
            ('ingested', 50),
            ('logical-wolf', 20),
            ('session_recovery', 100),
        ]

        cur = self.conn.cursor()
        loaded = []

        for namespace, limit in priorities:
            cur.execute("""
                SELECT id, content
                FROM memories
                WHERE namespace = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (namespace, limit))

            results = cur.fetchall()
            loaded.extend([r[0] for r in results])

        self.state["context_loaded"] = loaded
        self.state["critical_memories_loaded"] = True
        self.save_state()

        print(f"Loaded {len(loaded)} critical memories", file=sys.stderr)

    def query_relevant_memories(self, topic=None):
        """Query for memories relevant to current topic"""
        # Semantic search based on recent conversation topics
        # For now, just track that we can do this
        self.state["last_memory_query"] = datetime.now().isoformat()
        self.save_state()

    def capture_state_snapshot(self):
        """Capture current session state to memory"""
        snapshot = {
            "session_id": self.state["session_id"],
            "timestamp": datetime.now().isoformat(),
            "token_count": self.state["token_count"],
            "memories_loaded": len(self.state["context_loaded"]),
            "uptime_seconds": (datetime.now() - datetime.fromisoformat(self.state["started_at"])).total_seconds()
        }

        # Store in pgai
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO memories (user_id, content, metadata, memory_type, namespace, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            "claude_session",
            json.dumps(snapshot),
            json.dumps({"type": "session_state"}),
            "system",
            "wolf_logic",
            datetime.now(),
            datetime.now()
        ))
        self.conn.commit()

    def monitor_session(self):
        """Main monitoring loop"""
        print("Session Manager Active", file=sys.stderr)
        print(f"Session ID: {self.state['session_id']}", file=sys.stderr)

        # Load critical context immediately
        self.load_critical_context()

        # Periodic tasks
        snapshot_interval = 300  # 5 minutes
        last_snapshot = time.time()

        while True:
            time.sleep(10)

            # Periodic state snapshot
            if time.time() - last_snapshot > snapshot_interval:
                self.capture_state_snapshot()
                last_snapshot = time.time()

    def cleanup(self):
        """Clean shutdown"""
        self.capture_state_snapshot()
        self.save_state()
        self.conn.close()


def main():
    manager = SessionManager()
    try:
        manager.monitor_session()
    except KeyboardInterrupt:
        manager.cleanup()
        print("\nSession Manager stopped", file=sys.stderr)


if __name__ == "__main__":
    main()
