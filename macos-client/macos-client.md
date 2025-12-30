# macOS Client - Wolf Logic MCP

## Overview
macOS client setup for Wolf Logic MCP system. Local development environment with direct access to Messiah conda environment and MCP server integration.

## MANDATORY: Messiah Environment

### What is Messiah?
**Messiah** is the production Anaconda environment where all Wolf Logic processing happens:
- **Location:** `~/anaconda3/envs/messiah`
- **Python:** 3.12+
- **Purpose:** Unified environment for all AI/ML workflows
- **Models:** Local Ollama (llama3.2, mistral, qwen3-embedding, etc.)

### Activate on Entry - ALWAYS

**Every session, every script, every terminal - activate Messiah FIRST:**

```bash
source ~/anaconda3/bin/activate messiah
```

**Verification:**
```bash
which python
# Expected: /Users/youruser/anaconda3/envs/messiah/bin/python

python --version
# Expected: Python 3.12.x

conda env list | grep messiah
# Expected: messiah    * /Users/youruser/anaconda3/envs/messiah
```

### Why Messiah?

1. **Consistency:** Same environment across all nodes (181, 245, macOS)
2. **Dependencies:** All required packages pre-installed
3. **Isolation:** No conflicts with system Python or other projects
4. **Performance:** Optimized for AI/ML workloads

### Installed Libraries

```bash
# Core ML
- torch, torchvision, torchaudio
- sentence-transformers>=2.7.0
- transformers>=4.51.0

# Database
- psycopg2 (PostgreSQL)
- psycopg2-binary

# Document processing
- pypdf, pdfplumber
- python-docx
- pillow

# LLM/Embedding
- ollama (Python client)
- langchain
- chromadb

# API/Web
- fastapi, uvicorn
- requests, aiohttp
- pydantic

# Utilities
- python-dotenv
- rich (terminal formatting)
- click (CLI tools)
```

### Check Installed Packages

```bash
source ~/anaconda3/bin/activate messiah
pip list | grep -E "torch|transformers|psycopg2|fastapi"
```

## macOS Setup

### Prerequisites

1. **Anaconda/Miniconda installed**
   ```bash
   # If not installed:
   brew install --cask anaconda
   # or
   brew install miniconda
   ```

2. **Ollama installed** (for local LLM)
   ```bash
   brew install ollama
   ollama serve  # Start service
   ```

3. **Tailscale** (for server access)
   ```bash
   brew install --cask tailscale
   # Configure to access 100.110.82.181
   ```

### Create Messiah Environment

If Messiah doesn't exist on your macOS:

```bash
# Create environment
conda create -n messiah python=3.12 -y

# Activate
source ~/anaconda3/bin/activate messiah

# Install core packages
pip install \
  torch torchvision torchaudio \
  sentence-transformers transformers \
  psycopg2-binary \
  fastapi uvicorn \
  requests pydantic \
  pypdf pdfplumber \
  python-dotenv \
  rich click

# Install Ollama Python client
pip install ollama

# Verify
python -c "import torch; import transformers; import psycopg2; print('✓ Messiah ready')"
```

### Environment Variables

Create `~/.messiah_env`:

```bash
# Server connection
export POSTGRES_HOST=100.110.82.181
export POSTGRES_PORT=5433
export POSTGRES_USER=wolf
export POSTGRES_PASSWORD=wolflogic2024
export POSTGRES_DB=wolf_logic

# MCP Intake API
export MCP_INTAKE_URL=http://100.110.82.181:8002
export AUTHENTIK_URL=http://100.110.82.181:9001

# Ollama
export OLLAMA_HOST=http://localhost:11434

# Paths
export WOLF_CODE_ROOT=/Users/$(whoami)/Wolf-code/Wolf-Ai-Enterptises/Wolf-Logic-MCP
```

**Load on activation:**

Add to `~/.zshrc` or `~/.bash_profile`:

```bash
# Auto-activate Messiah for Wolf Logic work
function activate_messiah() {
    source ~/anaconda3/bin/activate messiah
    [ -f ~/.messiah_env ] && source ~/.messiah_env
    echo "✓ Messiah environment active"
    echo "  Python: $(which python)"
    echo "  Server: $POSTGRES_HOST:$POSTGRES_PORT"
}

# Alias for quick activation
alias messiah='activate_messiah'
```

## Core Logic Template

### Session Startup Protocol

**Every macOS session working with Wolf Logic MCP:**

```bash
# 1. Activate Messiah
source ~/anaconda3/bin/activate messiah
source ~/.messiah_env

# 2. Verify Librarian access
PGPASSWORD=wolflogic2024 psql \
  -h 100.110.82.181 \
  -p 5433 \
  -U wolf \
  -d wolf_logic \
  -c "SELECT COUNT(*) FROM memories;"
# Expected: 97,000+ rows

# 3. Check Ollama models
ollama list | grep -E "llama|mistral|qwen"

# 4. Verify MCP Intake API
curl http://100.110.82.181:8002/health
# Expected: {"status":"healthy",...}

# 5. Pull recent context (optional)
PGPASSWORD=wolflogic2024 psql \
  -h 100.110.82.181 \
  -p 5433 \
  -U wolf \
  -d wolf_logic \
  -c "SELECT content, namespace, created_at FROM memories
      WHERE namespace IN ('scripty', 'core_identity')
      ORDER BY created_at DESC LIMIT 20;"
```

### Script Template

Every Python script that works with Wolf Logic:

```python
#!/usr/bin/env python3
"""
Script: example_script.py
Purpose: [Describe what this does]

REQUIRES: Messiah environment
  source ~/anaconda3/bin/activate messiah
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import psycopg2
import requests

# Verify Messiah environment
REQUIRED_PACKAGES = ['psycopg2', 'requests', 'transformers']
for pkg in REQUIRED_PACKAGES:
    try:
        __import__(pkg)
    except ImportError:
        print(f"ERROR: {pkg} not found. Activate Messiah environment:")
        print("  source ~/anaconda3/bin/activate messiah")
        sys.exit(1)

# Load environment
from dotenv import load_dotenv
load_dotenv(Path.home() / '.messiah_env')

# Configuration
POSTGRES_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', '100.110.82.181'),
    'port': int(os.getenv('POSTGRES_PORT', '5433')),
    'user': os.getenv('POSTGRES_USER', 'wolf'),
    'password': os.getenv('POSTGRES_PASSWORD', 'wolflogic2024'),
    'database': os.getenv('POSTGRES_DB', 'wolf_logic')
}

MCP_INTAKE_URL = os.getenv('MCP_INTAKE_URL', 'http://100.110.82.181:8002')
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')


def query_librarian(query: str, namespace: str = None, limit: int = 10) -> list:
    """
    Query the Librarian (PostgreSQL + pgai)

    Args:
        query: Semantic search query
        namespace: Filter by namespace (optional)
        limit: Max results

    Returns:
        List of memory dicts
    """
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cursor = conn.cursor()

        if namespace:
            sql = """
                SELECT content, namespace, created_at
                FROM memories_embedding
                WHERE namespace = %s
                ORDER BY embedding <=> ai.ollama_embed('qwen3-embedding:4b', %s)
                LIMIT %s;
            """
            cursor.execute(sql, (namespace, query, limit))
        else:
            sql = """
                SELECT content, namespace, created_at
                FROM memories_embedding
                ORDER BY embedding <=> ai.ollama_embed('qwen3-embedding:4b', %s)
                LIMIT %s;
            """
            cursor.execute(sql, (query, limit))

        results = cursor.fetchall()
        cursor.close()
        conn.close()

        return [
            {
                'content': row[0],
                'namespace': row[1],
                'created_at': row[2]
            }
            for row in results
        ]

    except Exception as e:
        print(f"Librarian query failed: {e}")
        return []


def submit_to_mcp(text: str, metadata: dict = None, oauth_token: str = None):
    """
    Submit text to MCP Intake Stream

    Args:
        text: Text content
        metadata: Optional metadata dict
        oauth_token: OAuth token (if required)

    Returns:
        Response dict or None
    """
    try:
        headers = {'Content-Type': 'application/json'}
        if oauth_token:
            headers['Authorization'] = f'Bearer {oauth_token}'

        payload = {
            'text': text,
            'metadata': metadata or {}
        }

        response = requests.post(
            f'{MCP_INTAKE_URL}/intake/stream',
            json=payload,
            headers=headers,
            timeout=10
        )
        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"MCP submission failed: {e}")
        return None


def query_ollama(prompt: str, model: str = 'llama3.2:1b'):
    """
    Query local Ollama model

    Args:
        prompt: Prompt text
        model: Model name

    Returns:
        Response text or None
    """
    try:
        response = requests.post(
            f'{OLLAMA_HOST}/api/generate',
            json={
                'model': model,
                'prompt': prompt,
                'stream': False
            },
            timeout=30
        )
        response.raise_for_status()

        result = response.json()
        return result.get('response', '')

    except requests.exceptions.RequestException as e:
        print(f"Ollama query failed: {e}")
        return None


def main():
    """Main entry point"""
    print("=" * 60)
    print("Script: example_script.py")
    print("Environment: Messiah")
    print("=" * 60)

    # Example: Query Librarian
    print("\n1. Querying Librarian...")
    results = query_librarian("AI model deployment", namespace="scripty", limit=5)
    for i, result in enumerate(results, 1):
        print(f"  [{i}] {result['namespace']}: {result['content'][:100]}...")

    # Example: Submit to MCP
    print("\n2. Submitting to MCP...")
    response = submit_to_mcp(
        text="Test submission from macOS client",
        metadata={'source': 'macos_script', 'timestamp': datetime.now().isoformat()}
    )
    if response:
        print(f"  ✓ Submitted: {response.get('data', {}).get('file_id')}")

    # Example: Query Ollama
    print("\n3. Querying Ollama...")
    answer = query_ollama("What is 2+2? Answer in one word.", model="llama3.2:1b")
    if answer:
        print(f"  Response: {answer.strip()}")

    print("\n" + "=" * 60)
    print("✓ Script complete")


if __name__ == "__main__":
    main()
```

**Run:**
```bash
source ~/anaconda3/bin/activate messiah
python example_script.py
```

## MCP Client Integration

### Python Client

```python
import requests
from typing import Dict, Any, Optional

class WolfMCPClient:
    """macOS client for Wolf Logic MCP"""

    def __init__(
        self,
        base_url: str = "http://100.110.82.181:8002",
        oauth_token: Optional[str] = None
    ):
        self.base_url = base_url
        self.oauth_token = oauth_token
        self.session = requests.Session()

        if oauth_token:
            self.session.headers.update({
                'Authorization': f'Bearer {oauth_token}'
            })

    def submit_text(self, text: str, metadata: Dict[str, Any] = None) -> Dict:
        """Submit text to intake stream"""
        response = self.session.post(
            f'{self.base_url}/intake/stream',
            json={
                'text': text,
                'metadata': metadata or {}
            },
            timeout=10
        )
        response.raise_for_status()
        return response.json()

    def get_stats(self) -> Dict:
        """Get intake queue statistics"""
        response = self.session.get(
            f'{self.base_url}/intake/stats',
            timeout=10
        )
        response.raise_for_status()
        return response.json()

    def health_check(self) -> Dict:
        """Check API health"""
        response = self.session.get(
            f'{self.base_url}/health',
            timeout=5
        )
        response.raise_for_status()
        return response.json()


# Usage
client = WolfMCPClient()

# Submit text
result = client.submit_text(
    text="Important note from macOS",
    metadata={'source': 'macos_client', 'priority': 'high'}
)
print(f"Submitted: {result['data']['file_id']}")

# Check stats
stats = client.get_stats()
print(f"Queue: {stats['data']['total_files']} files")
```

### Swift Client (macOS Native)

For native macOS apps:

```swift
import Foundation

class WolfMCPClient {
    let baseURL = "http://100.110.82.181:8002"
    let oauthToken: String?

    init(oauthToken: String? = nil) {
        self.oauthToken = oauthToken
    }

    func submitText(text: String, metadata: [String: Any] = [:]) async throws -> [String: Any] {
        var request = URLRequest(url: URL(string: "\(baseURL)/intake/stream")!)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        if let token = oauthToken {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        let payload: [String: Any] = [
            "text": text,
            "metadata": metadata
        ]

        request.httpBody = try JSONSerialization.data(withJSONObject: payload)

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw URLError(.badServerResponse)
        }

        return try JSONSerialization.jsonObject(with: data) as! [String: Any]
    }

    func getStats() async throws -> [String: Any] {
        var request = URLRequest(url: URL(string: "\(baseURL)/intake/stats")!)

        if let token = oauthToken {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        let (data, _) = try await URLSession.shared.data(for: request)
        return try JSONSerialization.jsonObject(with: data) as! [String: Any]
    }
}

// Usage
Task {
    let client = WolfMCPClient()

    do {
        let result = try await client.submitText(
            text: "Test from macOS Swift",
            metadata: ["source": "swift_app", "version": "1.0"]
        )
        print("Submitted: \(result)")
    } catch {
        print("Error: \(error)")
    }
}
```

## CLI Tools

### Quick Submit Tool

```bash
#!/bin/bash
# wolf-submit.sh - Quick CLI submission to MCP

source ~/anaconda3/bin/activate messiah
source ~/.messiah_env

TEXT="${1:-}"
if [ -z "$TEXT" ]; then
    echo "Usage: wolf-submit.sh \"Your text here\""
    exit 1
fi

curl -X POST "$MCP_INTAKE_URL/intake/stream" \
    -H "Content-Type: application/json" \
    -d "{
        \"text\": \"$TEXT\",
        \"metadata\": {
            \"source\": \"cli\",
            \"user\": \"$(whoami)\",
            \"host\": \"$(hostname)\"
        }
    }"
```

**Make executable:**
```bash
chmod +x wolf-submit.sh
./wolf-submit.sh "Important note to remember"
```

### Clipboard Monitor

```python
#!/usr/bin/env python3
"""
clipboard_monitor.py - Auto-submit clipboard to MCP
"""

import time
import pyperclip
import requests
from datetime import datetime

MCP_URL = "http://100.110.82.181:8002/intake/stream"
LAST_CLIPBOARD = ""

def submit_to_mcp(text):
    try:
        response = requests.post(
            MCP_URL,
            json={
                'text': text,
                'metadata': {
                    'source': 'clipboard_monitor',
                    'timestamp': datetime.now().isoformat()
                }
            },
            timeout=5
        )
        if response.status_code == 200:
            print(f"✓ Submitted: {text[:50]}...")
    except Exception as e:
        print(f"✗ Failed: {e}")

while True:
    try:
        current = pyperclip.paste()
        if current and current != LAST_CLIPBOARD:
            submit_to_mcp(current)
            LAST_CLIPBOARD = current
        time.sleep(2)
    except KeyboardInterrupt:
        print("\nStopping clipboard monitor")
        break
```

## Troubleshooting

### Messiah not activating
```bash
# Verify Anaconda installation
conda --version

# List environments
conda env list

# If Messiah missing, create it
conda create -n messiah python=3.12 -y
```

### Can't connect to server
```bash
# Check Tailscale
ping 100.110.82.181

# Test PostgreSQL
PGPASSWORD=wolflogic2024 psql -h 100.110.82.181 -p 5433 -U wolf -d wolf_logic -c "SELECT 1;"

# Test MCP API
curl http://100.110.82.181:8002/health
```

### Ollama not running
```bash
# Start Ollama
ollama serve

# Pull models
ollama pull llama3.2:1b
ollama pull mistral:latest
ollama pull qwen3-embedding:4b
```

## Automation

### LaunchAgent (Auto-start on login)

Create `~/Library/LaunchAgents/com.wolflogic.messiah.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.wolflogic.messiah</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>source ~/anaconda3/bin/activate messiah && python /path/to/your/script.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

**Load:**
```bash
launchctl load ~/Library/LaunchAgents/com.wolflogic.messiah.plist
```

## Best Practices

1. **Always activate Messiah first**
2. **Use environment variables** (never hardcode credentials)
3. **Query Librarian before making decisions**
4. **Submit important notes to MCP** (they get processed + embedded)
5. **Test locally with Ollama** before deploying
6. **Use the script template** for consistency
7. **Monitor logs** with rich/logging
8. **Handle errors gracefully** (network, DB, LLM can fail)

## Resources

- **Server:** 100.110.82.181
- **MCP Docs:** `/server-configuration/README-INTAKE-PIPELINE.md`
- **Android Docs:** `/android-client.md`
- **GEMINI Instructions:** `/GEMINI.md`
- **CLAUDE Instructions:** `/CLAUDE.md`
