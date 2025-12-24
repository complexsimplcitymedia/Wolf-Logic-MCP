#!/usr/bin/env python3
"""
Scripty AI - Universal CLI-AI Monitor
Uses Grok (xAI) to watch ALL CLI-AI interactions on this workstation:
- Claude Code sessions
- Gemini CLI sessions
- Any AI terminal activity

Creates intelligent summaries instead of raw transcription.
Model: grok-beta (via xAI API)
"""

import os
import sys
import json
import time
import psycopg2
import requests
from datetime import datetime
from pathlib import Path

# Model configuration
SCRIPTY_MODEL = "grok-3"
XAI_API_KEY = os.environ.get("XAI_API_KEY")
if not XAI_API_KEY:
    raise ValueError("XAI_API_KEY environment variable not set")
XAI_API_URL = "https://api.x.ai/v1/chat/completions"
MODEL_CONTEXT_WINDOW = 131072  # 128K context for Grok
MAX_OUTPUT_TOKENS = 4096

# Database
PG_CONFIG = {
    "host": "100.110.82.181",
    "port": 5433,
    "database": "wolf_logic",
    "user": "wolf",
    "password": "wolflogic2024"
}

# Directories
LOG_DIR = Path("/mnt/Wolf-code/Wolf-Ai-Enterptises/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)


def get_session_files():
    """Find all active CLI-AI session files (Claude + Gemini)"""
    all_sessions = []

    # Claude Code sessions
    claude_dir = Path.home() / ".claude/projects"
    if claude_dir.exists():
        claude_sessions = list(claude_dir.glob("**/*.jsonl"))
        claude_sessions = [f for f in claude_sessions if not f.name.startswith('agent-')]
        all_sessions.extend([(f, 'claude') for f in claude_sessions])

    # Gemini CLI sessions
    gemini_dir = Path.home() / ".gemini/tmp"
    if gemini_dir.exists():
        gemini_sessions = list(gemini_dir.glob("*/chats/*.json"))
        all_sessions.extend([(f, 'gemini') for f in gemini_sessions])

    # Sort by modification time, return top 10 most recent
    all_sessions.sort(key=lambda x: x[0].stat().st_mtime, reverse=True)
    return all_sessions[:10]


def get_recent_exchanges_claude(session_file, last_position=0):
    """Get new exchanges from Claude Code JSONL session"""
    try:
        entries = []
        with open(session_file, 'r') as f:
            for line in f:
                if line.strip():
                    try:
                        entry = json.loads(line)
                        entries.append(entry)
                    except json.JSONDecodeError:
                        continue

        if len(entries) <= last_position:
            return last_position, []

        new_entries = entries[last_position:]
        exchanges = []
        current_user = None

        for entry in new_entries:
            entry_type = entry.get('type')

            if entry_type == 'user':
                msg = entry.get('message', {})
                content = msg.get('content', '')
                current_user = content

            elif entry_type == 'assistant' and current_user is not None:
                msg = entry.get('message', {})
                content_blocks = msg.get('content', [])

                full_content = []
                if isinstance(content_blocks, list):
                    for block in content_blocks:
                        if isinstance(block, dict):
                            if block.get('type') == 'text':
                                full_content.append(block.get('text', ''))
                            elif block.get('type') == 'tool_use':
                                tool_name = block.get('name', 'unknown')
                                full_content.append(f"[Used tool: {tool_name}]")
                elif isinstance(content_blocks, str):
                    full_content.append(content_blocks)

                assistant_content = '\n'.join(full_content)
                exchanges.append({
                    'user': current_user,
                    'assistant': assistant_content,
                    'source': 'claude'
                })
                current_user = None

        return len(entries), exchanges

    except Exception as e:
        print(f"[SCRIPTY] Error reading Claude session: {e}")
        return last_position, []


def get_recent_exchanges_gemini(session_file, last_position=0):
    """Get new exchanges from Gemini CLI JSON session"""
    try:
        with open(session_file, 'r') as f:
            data = json.load(f)

        messages = data.get('messages', [])
        if len(messages) <= last_position:
            return last_position, []

        new_messages = messages[last_position:]
        exchanges = []
        current_user = None

        for msg in new_messages:
            msg_type = msg.get('type')

            if msg_type == 'user':
                current_user = msg.get('content', '')

            elif msg_type == 'gemini' and current_user is not None:
                gemini_response = msg.get('content', '')
                exchanges.append({
                    'user': current_user,
                    'assistant': gemini_response,
                    'source': 'gemini',
                    'model': msg.get('model', 'unknown')
                })
                current_user = None

        return len(messages), exchanges

    except Exception as e:
        print(f"[SCRIPTY] Error reading Gemini session: {e}")
        return last_position, []


def get_recent_exchanges(session_file, session_type, last_position=0):
    """Route to appropriate parser based on session type"""
    if session_type == 'claude':
        return get_recent_exchanges_claude(session_file, last_position)
    elif session_type == 'gemini':
        return get_recent_exchanges_gemini(session_file, last_position)
    else:
        return last_position, []


def summarize_exchange(exchange, session_name):
    """Use Grok to create intelligent summary of exchange"""
    try:
        # Truncate exchange if too long (rough estimate: 4 chars = 1 token)
        max_chars = MODEL_CONTEXT_WINDOW * 3  # Leave room for prompt
        user_text = exchange['user'][:max_chars]
        assistant_text = exchange['assistant'][:max_chars]

        # Call xAI API (OpenAI-compatible format)
        response = requests.post(
            XAI_API_URL,
            headers={
                "Authorization": f"Bearer {XAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": SCRIPTY_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a concise summarizer. Summarize conversation exchanges in 2-3 sentences focusing on task requested and action taken."
                    },
                    {
                        "role": "user",
                        "content": f"USER: {user_text}\n\nASSISTANT: {assistant_text}\n\nSUMMARY:"
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 256
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            summary = result['choices'][0]['message']['content'].strip()
            return summary
        else:
            return f"[Summary unavailable: API error {response.status_code}]"

    except Exception as e:
        return f"[Summary unavailable: {str(e)}]"


def log_to_memory(summary, metadata=None):
    """Store summary in postgres memory system"""
    try:
        conn = psycopg2.connect(**PG_CONFIG)
        now = datetime.now()

        if metadata is None:
            metadata = {}

        metadata["timestamp"] = now.isoformat()
        metadata["type"] = "scripty_ai_summary"
        metadata["model"] = SCRIPTY_MODEL
        metadata["provider"] = "xai"

        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO memories (user_id, content, metadata, memory_type, namespace, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                "scripty_ai",
                summary,
                json.dumps(metadata),
                "session_summary",
                "scripty",
                now, now
            ))

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        print(f"[SCRIPTY] Storage error: {e}")
        return False


def watch_sessions(check_interval_seconds=30):
    """Watch multiple CLI-AI sessions and create intelligent summaries"""
    print("=" * 60)
    print("SCRIPTY AI - UNIVERSAL CLI-AI MONITOR (GROK EDITION)")
    print("=" * 60)
    print(f"Model: {SCRIPTY_MODEL} (xAI)")
    print(f"Context: {MODEL_CONTEXT_WINDOW} tokens (128K)")
    print(f"Watching: Claude Code + Gemini CLI + All AI terminals")
    print(f"Watching up to 10 active sessions")
    print("=" * 60)

    # Track positions for each session file
    session_positions = {}

    while True:
        try:
            # Get active session files (returns list of tuples: (file, type))
            session_files = get_session_files()

            if not session_files:
                print("[SCRIPTY] No active sessions found, waiting...")
                time.sleep(check_interval_seconds)
                continue

            # Process each session
            for session_file, session_type in session_files:
                session_name = session_file.stem
                session_key = str(session_file)

                # Initialize position tracking
                if session_key not in session_positions:
                    session_positions[session_key] = 0

                # Get new exchanges
                last_pos = session_positions[session_key]
                new_pos, exchanges = get_recent_exchanges(session_file, session_type, last_pos)
                session_positions[session_key] = new_pos

                # Summarize and log each exchange
                for exchange in exchanges:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    source = exchange.get('source', 'unknown')
                    print(f"\n[SCRIPTY] [{timestamp}] New {source} exchange in {session_name}")

                    # Generate AI summary
                    summary = summarize_exchange(exchange, session_name)

                    # Store in memory
                    log_to_memory(summary, {
                        "session": session_name,
                        "source": source,
                        "timestamp": timestamp
                    })

                    print(f"[SCRIPTY] Summary: {summary[:100]}...")

            time.sleep(check_interval_seconds)

        except KeyboardInterrupt:
            print("\n[SCRIPTY] Shutting down")
            break
        except Exception as e:
            print(f"[SCRIPTY] Error: {e}")
            time.sleep(60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Scripty AI - Intelligent session note-taker')
    parser.add_argument('--interval', type=int, default=30, help='Check interval in seconds')

    args = parser.parse_args()

    watch_sessions(args.interval)
