#!/usr/bin/env python3
"""
Scripty Grok - Universal CLI-AI Monitor (xAI Grok Edition)
Uses Grok API to watch ALL CLI-AI interactions on this workstation:
- Claude Code sessions
- Gemini CLI sessions
- Any AI terminal activity

Creates intelligent summaries instead of raw transcription.
Model: grok-3-mini-fast (via xAI API)
"""

import os
import sys
import json
import time
import psycopg2
import requests
from datetime import datetime
from pathlib import Path

# xAI Grok API Configuration
XAI_API_KEY = os.environ.get("XAI_API_KEY", "xai-HOFGrAn4OU8xaixrGUBMX8cgHzHePizLgSCTahhmF5oQre0MqFn7ZJXobcChWrLkx5sOlasPWUTmGW4G")
XAI_API_URL = "https://api.x.ai/v1/chat/completions"
GROK_MODEL = os.environ.get("GROK_MODEL", "grok-3-mini-fast")  # Model from env

# Database - Mac connects to main server with localhost fallback
PG_CONFIG_PRIMARY = {
    "host": "100.110.82.181",
    "port": 5433,
    "database": "wolf_logic",
    "user": "wolf",
    "password": "wolflogic2024"
}

PG_CONFIG_FALLBACK = {
    "host": "localhost",
    "port": 5432,
    "database": "wolf_logic",
    "user": "wolf",
    "password": "wolflogic2024"
}

def get_db_connection():
    """Try primary (181), fall back to localhost if offline"""
    try:
        conn = psycopg2.connect(**PG_CONFIG_PRIMARY, connect_timeout=3)
        return conn, "primary"
    except (psycopg2.OperationalError, Exception):
        try:
            conn = psycopg2.connect(**PG_CONFIG_FALLBACK, connect_timeout=3)
            return conn, "fallback"
        except Exception as e:
            raise Exception(f"Both primary and fallback DB failed: {e}")

# Directories - Mac paths
LOG_DIR = Path.home() / "Wolf-Logic-MCP/logs"
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
        print(f"[SCRIPTY-GROK] Error reading Claude session: {e}")
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
        print(f"[SCRIPTY-GROK] Error reading Gemini session: {e}")
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
    """Use Grok API to create intelligent summary of exchange"""
    try:
        # Truncate exchange if too long
        max_chars = 12000  # Leave room for response
        user_text = exchange['user'][:max_chars]
        assistant_text = exchange['assistant'][:max_chars]

        prompt = f"""Summarize this conversation exchange in 2-3 concise sentences. Focus on what task was requested and what action was taken.

USER: {user_text}

ASSISTANT: {assistant_text}

SUMMARY:"""

        headers = {
            "Authorization": f"Bearer {XAI_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": GROK_MODEL,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 256,
            "temperature": 0.3
        }

        response = requests.post(
            XAI_API_URL,
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            summary = result.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
            return summary
        else:
            return f"[Summary unavailable: API error {response.status_code}]"

    except Exception as e:
        return f"[Summary unavailable: {str(e)}]"


def log_to_memory(summary, metadata=None):
    """Store summary in postgres memory system"""
    try:
        conn, db_type = get_db_connection()
        now = datetime.now()

        if metadata is None:
            metadata = {}

        metadata["timestamp"] = now.isoformat()
        metadata["type"] = "scripty_summary"
        metadata["machine"] = "apexwolf-mac"
        metadata["db_target"] = db_type

        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO memories (user_id, content, metadata, memory_type, namespace, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                "scripty_grok",
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
        print(f"[SCRIPTY-GROK] Storage error: {e}")
        return False


def watch_sessions(check_interval_seconds=30):
    """Watch multiple CLI-AI sessions and create intelligent summaries"""
    print("=" * 60)
    print("SCRIPTY - CLI-AI MONITOR")
    print("=" * 60)
    print(f"Watching: Claude Code + Gemini CLI")
    print(f"Interval: {check_interval_seconds}s")
    print("=" * 60)

    # Track positions for each session file
    session_positions = {}

    while True:
        try:
            # Get active session files
            session_files = get_session_files()

            if not session_files:
                print("[SCRIPTY-GROK] No active sessions found, waiting...")
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
                    print(f"\n[SCRIPTY-GROK] [{timestamp}] New {source} exchange in {session_name}")

                    # Generate Grok summary
                    summary = summarize_exchange(exchange, session_name)

                    # Store in memory
                    log_to_memory(summary, {
                        "session": session_name,
                        "source": source,
                        "timestamp": timestamp
                    })

                    print(f"[SCRIPTY-GROK] Summary: {summary[:100]}...")

            time.sleep(check_interval_seconds)

        except KeyboardInterrupt:
            print("\n[SCRIPTY-GROK] Shutting down")
            break
        except Exception as e:
            print(f"[SCRIPTY-GROK] Error: {e}")
            time.sleep(60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Scripty Grok - Intelligent session note-taker using xAI')
    parser.add_argument('--interval', type=int, default=30, help='Check interval in seconds')

    args = parser.parse_args()

    watch_sessions(args.interval)
