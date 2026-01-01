#!/usr/bin/env python3
"""
Scripty - Session Transcriber
Uses llama3.2 on 181 to transcribe CLI-AI sessions verbatim
Writes to files for swarm processing
"""

import os
import json
import time
import requests
from datetime import datetime
from pathlib import Path

# Ollama on 181
OLLAMA_URL = "http://100.110.82.181:11434/api/chat"
OLLAMA_MODEL = "llama3.2:1b"

# Output directory
OUTPUT_DIR = Path("/mnt/Wolf-code/Wolf-Ai-Enterptises/camera/dailys")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_session_files():
    """Find active Claude Code session files"""
    claude_dir = Path.home() / ".claude/projects"
    if not claude_dir.exists():
        return []

    sessions = list(claude_dir.glob("**/*.jsonl"))
    sessions = [f for f in sessions if not f.name.startswith('agent-')]
    sessions.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return sessions[:10]


def get_recent_exchanges(session_file, last_position=0):
    """Get new exchanges from Claude JSONL session"""
    try:
        entries = []
        with open(session_file, 'r') as f:
            for line in f:
                if line.strip():
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        print(f"[SCRIPTY] Skipping malformed JSON line: {str(e)[:50]}")
                        continue

        if len(entries) <= last_position:
            return last_position, []

        new_entries = entries[last_position:]
        exchanges = []
        current_user = None

        for entry in new_entries:
            if entry.get('type') == 'user':
                current_user = entry.get('message', {}).get('content', '')
            elif entry.get('type') == 'assistant' and current_user:
                content_blocks = entry.get('message', {}).get('content', [])
                assistant_text = []

                if isinstance(content_blocks, list):
                    for block in content_blocks:
                        if isinstance(block, dict) and block.get('type') == 'text':
                            assistant_text.append(block.get('text', ''))

                exchanges.append({
                    'user': current_user,
                    'assistant': '\n'.join(assistant_text)
                })
                current_user = None

        return len(entries), exchanges

    except FileNotFoundError:
        print(f"[SCRIPTY] Session file not found: {session_file}")
        return last_position, []
    except PermissionError as e:
        print(f"[SCRIPTY] Permission denied reading session file: {e}")
        return last_position, []
    except IOError as e:
        print(f"[SCRIPTY] I/O error reading session: {e}")
        return last_position, []


def transcribe_exchange(exchange):
    """Use llama3.2 on 181 to transcribe exchange verbatim"""
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": "Transcribe the following conversation exchange verbatim. Do not summarize."
                    },
                    {
                        "role": "user",
                        "content": f"USER: {exchange['user']}\n\nASSISTANT: {exchange['assistant']}"
                    }
                ],
                "stream": False
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            return result['message']['content']
        else:
            return f"USER: {exchange['user']}\n\nASSISTANT: {exchange['assistant']}"

    except requests.exceptions.Timeout:
        print("[SCRIPTY] Ollama request timed out, using raw exchange")
        return f"USER: {exchange['user']}\n\nASSISTANT: {exchange['assistant']}"
    except requests.exceptions.ConnectionError as e:
        print(f"[SCRIPTY] Cannot connect to Ollama at {OLLAMA_URL}: {e}")
        return f"USER: {exchange['user']}\n\nASSISTANT: {exchange['assistant']}"
    except requests.exceptions.RequestException as e:
        print(f"[SCRIPTY] Request error during transcription: {e}")
        return f"USER: {exchange['user']}\n\nASSISTANT: {exchange['assistant']}"


def write_to_file(transcript, session_name):
    """Write transcript to daily file"""
    try:
        today = datetime.now().strftime("%Y%m%d")
        output_file = OUTPUT_DIR / f"scripty_{today}.jsonl"

        entry = {
            "timestamp": datetime.now().isoformat(),
            "session": session_name,
            "transcript": transcript
        }

        with open(output_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')

        return True
    except PermissionError as e:
        print(f"[SCRIPTY] Permission denied writing to {output_file}: {e}")
        return False
    except OSError as e:
        print(f"[SCRIPTY] OS error writing transcript (disk full?): {e}")
        return False
    except IOError as e:
        print(f"[SCRIPTY] I/O error writing transcript: {e}")
        return False


def watch_sessions(check_interval=30):
    """Watch Claude sessions and transcribe to files"""
    print("=" * 60)
    print("SCRIPTY - SESSION TRANSCRIBER")
    print("=" * 60)
    print(f"Model: {OLLAMA_MODEL} @ 181")
    print(f"Output: {OUTPUT_DIR}")
    print("=" * 60)

    session_positions = {}

    while True:
        try:
            sessions = get_session_files()

            if not sessions:
                time.sleep(check_interval)
                continue

            for session_file in sessions:
                session_name = session_file.stem
                session_key = str(session_file)

                if session_key not in session_positions:
                    session_positions[session_key] = 0

                last_pos = session_positions[session_key]
                new_pos, exchanges = get_recent_exchanges(session_file, last_pos)
                session_positions[session_key] = new_pos

                for exchange in exchanges:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"\n[SCRIPTY] [{timestamp}] New exchange in {session_name}")

                    transcript = transcribe_exchange(exchange)
                    write_to_file(transcript, session_name)

                    print(f"[SCRIPTY] Transcribed to {OUTPUT_DIR}")

            time.sleep(check_interval)

        except KeyboardInterrupt:
            print("\n[SCRIPTY] Shutting down")
            break
        except Exception as e:
            print(f"[SCRIPTY] Error: {e}")
            time.sleep(60)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--interval', type=int, default=30)
    args = parser.parse_args()
    watch_sessions(args.interval)
