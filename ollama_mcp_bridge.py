#!/usr/bin/env python3
"""
Ollama MCP Bridge - Connects Messiah to the Librarian via MCP
Lightweight Python implementation for Termux/Android compatibility
"""

import json
import requests
import psycopg2
from typing import Optional

# Configuration
OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = "messiah_awakening:latest"

# Local DB (when on the server)
DB_CONFIG_LOCAL = {
    "host": "127.0.0.1",
    "port": 5433,
    "user": "wolf",
    "password": "wolflogic2024",
    "dbname": "wolf_logic"
}

# Docker mirror (via Tailscale - for remote/mobile access)
DB_CONFIG_DOCKER = {
    "host": "100.110.82.250",
    "port": 5433,
    "user": "wolf",
    "password": "wolflogic2024",
    "dbname": "wolf_logic"
}

# Default - try local first, fall back to Docker
DB_CONFIG = DB_CONFIG_LOCAL

class LibrarianMCP:
    """MCP-style interface to the Librarian (PostgreSQL)"""

    def __init__(self, prefer_docker: bool = False):
        self.conn = None
        self.active_config = None
        self.prefer_docker = prefer_docker
        self.connect()

    def connect(self):
        """Connect to the Librarian - tries local first, then Docker mirror"""
        configs = [
            ("Docker", DB_CONFIG_DOCKER),
            ("Local", DB_CONFIG_LOCAL)
        ] if self.prefer_docker else [
            ("Local", DB_CONFIG_LOCAL),
            ("Docker", DB_CONFIG_DOCKER)
        ]

        for name, config in configs:
            try:
                self.conn = psycopg2.connect(**config, connect_timeout=5)
                self.active_config = name
                print(f"Connected to the Librarian ({name}: {config['host']}:{config['port']})")
                return
            except Exception as e:
                print(f"Librarian {name} connection failed: {e}")

        print("WARNING: Could not connect to any Librarian instance")
        self.conn = None

    def query(self, sql: str, limit: int = 20) -> list:
        """Execute a query against the Librarian"""
        if not self.conn:
            self.connect()
        if not self.conn:
            return [{"error": "Cannot connect to Librarian"}]

        try:
            cur = self.conn.cursor()
            cur.execute(sql)
            columns = [desc[0] for desc in cur.description] if cur.description else []
            rows = cur.fetchmany(limit)
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            self.conn.rollback()
            return [{"error": str(e)}]

    def semantic_search(self, query: str, namespace: str = None, limit: int = 10) -> list:
        """Semantic search using qwen3-embedding:4b"""
        ns_filter = f"WHERE namespace = '{namespace}'" if namespace else ""
        sql = f"""
            SELECT content, namespace, created_at
            FROM memories_embedding
            {ns_filter}
            ORDER BY embedding <=> ai.ollama_embed('qwen3-embedding:4b', '{query}')
            LIMIT {limit};
        """
        return self.query(sql, limit)

    def recent_context(self, hours: int = 1, namespace: str = "scripty") -> list:
        """Get recent memories"""
        sql = f"""
            SELECT content, created_at
            FROM memories
            WHERE namespace = '{namespace}'
              AND created_at >= NOW() - INTERVAL '{hours} hours'
            ORDER BY created_at DESC
            LIMIT 20;
        """
        return self.query(sql)

    def text_search(self, term: str, namespace: str = None) -> list:
        """Text search for exact matches"""
        ns_filter = f"AND namespace = '{namespace}'" if namespace else ""
        sql = f"""
            SELECT content, namespace, created_at
            FROM memories
            WHERE content ILIKE '%{term}%' {ns_filter}
            ORDER BY created_at DESC
            LIMIT 15;
        """
        return self.query(sql)


class OllamaMCPBridge:
    """Bridge between Ollama and MCP tools"""

    def __init__(self, model: str = OLLAMA_MODEL):
        self.model = model
        self.librarian = LibrarianMCP()
        self.tools = self._define_tools()

    def _define_tools(self) -> list:
        """Define available MCP tools"""
        return [
            {
                "name": "librarian_semantic_search",
                "description": "Search the Librarian using semantic similarity. Use for finding related concepts, topics, or context.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The semantic search query"},
                        "namespace": {"type": "string", "description": "Optional namespace filter (scripty, core_identity, wolf_hunt, ingested)"},
                        "limit": {"type": "integer", "description": "Max results (default 10)"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "librarian_recent",
                "description": "Get recent memories from the Librarian. Use for recent conversation context.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "hours": {"type": "integer", "description": "Hours to look back (default 1)"},
                        "namespace": {"type": "string", "description": "Namespace to search (default: scripty)"}
                    }
                }
            },
            {
                "name": "librarian_text_search",
                "description": "Search for exact text matches in the Librarian.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "term": {"type": "string", "description": "Text to search for"},
                        "namespace": {"type": "string", "description": "Optional namespace filter"}
                    },
                    "required": ["term"]
                }
            },
            {
                "name": "librarian_sql",
                "description": "Execute raw SQL against the Librarian. Use for complex queries.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sql": {"type": "string", "description": "SQL query to execute"}
                    },
                    "required": ["sql"]
                }
            }
        ]

    def execute_tool(self, tool_name: str, params: dict) -> str:
        """Execute an MCP tool"""
        if tool_name == "librarian_semantic_search":
            results = self.librarian.semantic_search(
                params.get("query", ""),
                params.get("namespace"),
                params.get("limit", 10)
            )
        elif tool_name == "librarian_recent":
            results = self.librarian.recent_context(
                params.get("hours", 1),
                params.get("namespace", "scripty")
            )
        elif tool_name == "librarian_text_search":
            results = self.librarian.text_search(
                params.get("term", ""),
                params.get("namespace")
            )
        elif tool_name == "librarian_sql":
            results = self.librarian.query(params.get("sql", ""))
        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})

        return json.dumps(results, default=str, indent=2)

    def chat(self, message: str, auto_context: bool = True) -> str:
        """Send a message to Ollama with Librarian context injection"""

        # Auto-inject recent context from Librarian
        context_block = ""
        if auto_context:
            recent = self.librarian.recent_context(hours=1)
            if recent and len(recent) > 0:
                if not (isinstance(recent[0], dict) and "error" in recent[0]):
                    context_block = "\n\n[LIBRARIAN CONTEXT - Last Hour]:\n"
                    for mem in recent[:5]:
                        if isinstance(mem, dict) and "content" in mem:
                            context_block += f"- {mem['content'][:200]}...\n"

        # Check if user is asking to search/query
        search_results = ""
        search_triggers = ["search", "find", "query", "look up", "what did", "librarian"]
        if any(trigger in message.lower() for trigger in search_triggers):
            results = self.librarian.semantic_search(message, limit=5)
            if results and len(results) > 0:
                if not (isinstance(results[0], dict) and "error" in results[0]):
                    search_results = "\n\n[LIBRARIAN SEARCH RESULTS]:\n"
                    for r in results:
                        if isinstance(r, dict) and "content" in r:
                            search_results += f"- {r['content'][:300]}...\n"

        # Build the full message
        full_message = message
        if search_results:
            full_message += search_results
        if context_block:
            full_message += context_block

        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": full_message}
            ],
            "stream": False
        }

        try:
            response = requests.post(f"{OLLAMA_URL}/api/chat", json=payload)
            result = response.json()
            return result.get("message", {}).get("content", "No response")

        except Exception as e:
            return f"Error: {e}"


def main():
    """Interactive CLI for the bridge"""
    print("=" * 50)
    print("OLLAMA MCP BRIDGE - Messiah + Librarian")
    print("=" * 50)
    print("Type 'quit' to exit")
    print()

    bridge = OllamaMCPBridge()

    while True:
        try:
            user_input = input("\nYou: ").strip()
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
            if not user_input:
                continue

            print("\nMessiah: ", end="", flush=True)
            response = bridge.chat(user_input)
            print(response)

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
