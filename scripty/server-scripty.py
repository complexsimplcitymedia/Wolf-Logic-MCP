#!/usr/bin/env python3
"""
Server-Scripty - Verbatim Transcription
Runs on csmcloud-server (181) - Captures full exchanges, no processing.

Court reporter mode: VERBATIM ONLY. No summarization. No LLM calls.
Drops complete transcripts to client dump for swarm processing.

Union Way: Nobody rushes. Everybody has a job. Stay in your lane.
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path

# Client dump directory - swarm picks up from here
CLIENT_DUMP_DIR = Path("/mnt/Wolf-code/Wolf-Ai-Enterptises/Wolf-Logic-MCP/data/client-dumps")
CLIENT_DUMP_DIR.mkdir(parents=True, exist_ok=True)

# Log directory
LOG_DIR = Path("/mnt/Wolf-code/Wolf-Ai-Enterptises/Wolf-Logic-MCP/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "server-scripty.log"


def log(msg):
    """Simple file logging"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {msg}\n"

    print(log_line.strip())

    with open(LOG_FILE, 'a') as f:
        f.write(log_line)


def get_session_file():
    """Find the current Claude session file"""
    claude_dir = Path.home() / ".claude"
    projects_dir = claude_dir / "projects"

    if not projects_dir.exists():
        return None

    session_files = list(projects_dir.glob("**/*.jsonl"))
    session_files = [f for f in session_files if not f.name.startswith('agent-')]

    if session_files:
        return max(session_files, key=lambda p: p.stat().st_mtime)

    return None


def get_recent_exchanges(session_file, last_position=0):
    """Get new exchanges since last check - VERBATIM"""
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

                # Capture FULL content - verbatim
                full_content = []
                if isinstance(content_blocks, list):
                    for block in content_blocks:
                        if isinstance(block, dict):
                            block_type = block.get('type')
                            if block_type == 'text':
                                full_content.append(block.get('text', ''))
                            elif block_type == 'thinking':
                                # Include thinking - verbatim
                                full_content.append(f"[THINKING]\n{block.get('thinking', '')}")
                            elif block_type == 'tool_use':
                                # Include tool calls - verbatim
                                tool_name = block.get('name', 'unknown')
                                tool_input = json.dumps(block.get('input', {}), indent=2)
                                full_content.append(f"[TOOL: {tool_name}]\n{tool_input}")
                elif isinstance(content_blocks, str):
                    full_content.append(content_blocks)

                assistant_content = '\n\n'.join(full_content)

                exchanges.append({
                    'user': current_user,
                    'assistant': assistant_content,
                    'timestamp': datetime.now().isoformat()
                })
                current_user = None

        return len(entries), exchanges

    except Exception as e:
        log(f"Error reading exchanges: {e}")
        return last_position, []


def write_to_client_dump(exchange, exchange_num):
    """Write VERBATIM transcript to client dump - no processing"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = CLIENT_DUMP_DIR / f"transcript_{exchange_num:06d}_{timestamp}.json"

    try:
        # Full verbatim transcript
        transcript = {
            "exchange_num": exchange_num,
            "timestamp": exchange['timestamp'],
            "user": exchange['user'],
            "assistant": exchange['assistant'],
            "source": "server-scripty",
            "type": "verbatim_transcript"
        }

        with open(filename, 'w') as f:
            json.dump(transcript, f, indent=2)

        log(f"Transcript: {filename.name}")
        return True

    except Exception as e:
        log(f"Dump error: {e}")
        return False


def watch_session(check_interval=30):
    """Watch session - VERBATIM TRANSCRIPTION ONLY"""
    log("=" * 60)
    log("SERVER-SCRIPTY - Starting")
    log("MODE: Verbatim transcription (no processing)")
    log(f"Client dump: {CLIENT_DUMP_DIR}")
    log("=" * 60)

    last_position = 0
    exchange_count = 0

    while True:
        try:
            session_file = get_session_file()
            if not session_file:
                time.sleep(check_interval)
                continue

            last_position, exchanges = get_recent_exchanges(session_file, last_position)

            for exchange in exchanges:
                write_to_client_dump(exchange, exchange_count)
                log(f"Exchange #{exchange_count} → client dump")
                exchange_count += 1

            time.sleep(check_interval)

        except KeyboardInterrupt:
            log("Shutdown requested")
            log(f"Total exchanges transcribed: {exchange_count}")
            break
        except Exception as e:
            log(f"Error: {e}")
            time.sleep(60)


if __name__ == "__main__":
    watch_session()
