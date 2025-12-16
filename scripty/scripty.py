#!/usr/bin/env python3
"""
Scripty - Production Transcriber for Claude Sessions
Full session transcription + continuity logging + memory counter.

Court reporter mode: Captures EVERYTHING.
Every exchange, every token, every tool call - full verbatim.

Union Way: Nobody rushes. Everybody has a job. Stay in your lane.
"""

import os
import sys
import json
import time
import psycopg2
from datetime import datetime
from pathlib import Path
import subprocess

# Embedding fleet - fan out, don't bottleneck
EMBED_FLEET = [
    "nomic-embed-text:v1.5",
    "mxbai-embed-large:latest",
    "snowflake-arctic-embed:137m",
    "jina/jina-embeddings-v2-base-en:latest",
    "embeddinggemma:latest",
]

# Database
PG_CONFIG = {
    "host": "100.110.82.181",
    "port": 5433,
    "database": "wolf_logic",
    "user": "wolf",
    "password": "wolflogic2024"
}

# Context thresholds
DUMP_THRESHOLD = 0.90  # 90% context usage triggers full dump (buffer for dump size)
DUMP_DIR = Path("/mnt/Wolf-code/Wolf-Ai-Enterptises/data/memory-dumps")
LOG_DIR = Path("/mnt/Wolf-code/Wolf-Ai-Enterptises/logs")
INGEST_SCRIPT = Path("/mnt/Wolf-code/Wolf-Ai-Enterptises/writers/ingest_agent.py")

# Ensure directories exist
DUMP_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)


def get_session_file():
    """Find the current Claude session file - project-based JSONL"""
    # Claude Code stores full conversations in ~/.claude/projects/{project-dir}/{sessionId}.jsonl
    # These are the actual transcripts with user + assistant messages

    claude_dir = Path.home() / ".claude"
    projects_dir = claude_dir / "projects"

    if not projects_dir.exists():
        return None

    # Find the most recently modified session file across all projects
    session_files = list(projects_dir.glob("**/*.jsonl"))
    # Filter out agent files - we want main session files only
    session_files = [f for f in session_files if not f.name.startswith('agent-')]

    if session_files:
        # Return most recently modified session file
        return max(session_files, key=lambda p: p.stat().st_mtime)

    return None


def get_memory_count():
    """Get total memory count from postgres - live counter"""
    try:
        conn = psycopg2.connect(**PG_CONFIG)
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM memories")
            count = cur.fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        print(f"[SCRIPTY] Counter error: {e}")
        return 0


def get_recent_exchanges(session_file, last_position=0):
    """Get new exchanges since last check - FULL TRANSCRIPTION MODE"""
    try:
        # Claude Code project sessions: one JSON per line
        # Format: {type: "user"|"assistant"|"file-history-snapshot", message: {...}, ...}
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

        # Get new entries since last check
        new_entries = entries[last_position:]

        # Build exchanges from user/assistant pairs - FULL VERBATIM
        exchanges = []
        current_user = None

        for entry in new_entries:
            entry_type = entry.get('type')

            if entry_type == 'user':
                # User message
                msg = entry.get('message', {})
                content = msg.get('content', '')
                current_user = content

            elif entry_type == 'assistant' and current_user is not None:
                # Assistant response
                msg = entry.get('message', {})
                content_blocks = msg.get('content', [])

                # Extract full content from all blocks
                full_content = []
                if isinstance(content_blocks, list):
                    for block in content_blocks:
                        if isinstance(block, dict):
                            block_type = block.get('type')
                            if block_type == 'text':
                                full_content.append(block.get('text', ''))
                            elif block_type == 'thinking':
                                # Include thinking blocks - FULL VERBATIM
                                full_content.append(f"[THINKING]\n{block.get('thinking', '')}")
                            elif block_type == 'tool_use':
                                # Include tool calls - FULL VERBATIM
                                tool_name = block.get('name', 'unknown')
                                tool_input = json.dumps(block.get('input', {}), indent=2)
                                full_content.append(f"[TOOL: {tool_name}]\n{tool_input}")
                elif isinstance(content_blocks, str):
                    full_content.append(content_blocks)

                assistant_content = '\n\n'.join(full_content)

                # Create exchange pair
                exchanges.append({
                    'user': current_user,
                    'assistant': assistant_content
                })
                current_user = None  # Reset for next exchange

        return len(entries), exchanges

    except Exception as e:
        print(f"[SCRIPTY] Error reading exchanges: {e}")
        import traceback
        traceback.print_exc()
        return last_position, []


def transcribe_exchange(exchange, exchange_num):
    """Full transcription - court reporter mode"""
    timestamp = datetime.now().isoformat()

    # Build full transcript entry
    transcript = {
        "exchange_number": exchange_num,
        "timestamp": timestamp,
        "user_input": exchange['user'],
        "assistant_response": exchange['assistant'],
        "type": "full_transcript"
    }

    return json.dumps(transcript, indent=2)


def get_token_usage(session_data):
    """Extract token usage from session data"""
    try:
        if 'usage' in session_data:
            used = session_data['usage'].get('tokens_used', 0)
            total = session_data['usage'].get('tokens_total', 200000)
            return used / total if total > 0 else 0
    except:
        pass
    return None


def trigger_full_dump(session_file):
    """Trigger full session dump and ingestion at 95% threshold"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dump_file = DUMP_DIR / f"context_dump_95pct_{timestamp}.jsonl"

    print(f"[SCRIPTY] 🚨 90% THRESHOLD REACHED! Dumping full session...")

    try:
        # Copy full session to dump directory
        with open(session_file, 'r') as src:
            session_data = src.read()

        with open(dump_file, 'w') as dst:
            dst.write(session_data)

        print(f"[SCRIPTY] ✓ Dumped to: {dump_file}")

        # Trigger ingestion via ingest_agent
        messiah_python = Path.home() / "anaconda3/envs/messiah/bin/python"
        subprocess.run([
            str(messiah_python),
            str(INGEST_SCRIPT),
            str(dump_file)
        ], check=True)

        print(f"[SCRIPTY] ✓ Ingestion complete!")
        return True

    except Exception as e:
        print(f"[SCRIPTY] ✗ Dump failed: {e}")
        return False


def check_context_threshold():
    """Check if we hit 90% context - trigger full dump if so"""
    session_file = get_session_file()

    if not session_file or not session_file.exists():
        return None

    try:
        # For JSONL files, read last line which may contain usage info
        # For now, skip threshold check for JSONL - rely on manual dumps
        if str(session_file).endswith('.jsonl'):
            return 0.0  # Can't easily get usage from JSONL format

        with open(session_file, 'r') as f:
            session_data = json.load(f)

        usage = get_token_usage(session_data)
        if usage is not None and usage >= DUMP_THRESHOLD:
            print(f"[SCRIPTY] 90% threshold hit - triggering full dump")
            trigger_full_dump(session_file)
            return usage

        return usage
    except Exception as e:
        print(f"[SCRIPTY] Error checking threshold: {e}")
        return None


def log_observation(observation: str, metadata: dict = None):
    """Log a single timestamped observation - one line, that's it"""
    try:
        conn = psycopg2.connect(**PG_CONFIG)
        now = datetime.now()

        if metadata is None:
            metadata = {}

        metadata["timestamp"] = now.isoformat()
        metadata["type"] = "scripty_note"

        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO memories (user_id, content, metadata, memory_type, namespace, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                "scripty",
                observation,
                json.dumps(metadata),
                "continuity_note",
                "scripty",
                now, now
            ))

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        print(f"[SCRIPTY] Storage error: {e}")
        return False


def watch_session(check_interval_seconds: int = 30):
    """Watch session - FULL TRANSCRIPTION MODE"""
    # Initial memory count
    memory_count = get_memory_count()

    print("=" * 60)
    print("SCRIPTY - PRODUCTION TRANSCRIBER")
    print("=" * 60)
    print("TRANSCRIPTION MODE: FULL VERBATIM")
    print("Checking 90% context threshold")
    print(f"MEMORIES SERVED: {memory_count:,}")
    print("=" * 60)
    print("Union Way: Stay in your lane")
    print("=" * 60)

    session_file = get_session_file()
    if not session_file:
        print("[SCRIPTY] No session file found - waiting...")
        time.sleep(check_interval_seconds)
        return

    last_position = 0
    exchange_count = 0
    last_memory_count = memory_count

    while True:
        try:
            # Update memory counter
            memory_count = get_memory_count()
            if memory_count != last_memory_count:
                print(f"\n{'='*60}")
                print(f"📊 MEMORIES SERVED: {memory_count:,} (+{memory_count - last_memory_count})")
                print(f"{'='*60}\n")
                last_memory_count = memory_count

            # Check for 90% threshold
            usage = check_context_threshold()
            if usage and usage >= DUMP_THRESHOLD:
                print(f"[SCRIPTY] 🚨 Context dumped at {usage*100:.1f}% - clean slate")

            # Get new exchanges since last check
            last_position, exchanges = get_recent_exchanges(session_file, last_position)

            # Full transcription on new exchanges
            for exchange in exchanges:
                transcript = transcribe_exchange(exchange, exchange_count)
                timestamp = datetime.now().strftime("%H:%M:%S")

                # Log full transcript to database
                log_observation(transcript, {
                    "exchange_num": exchange_count,
                    "transcript_mode": "full_verbatim",
                    "timestamp": timestamp
                })

                print(f"[SCRIPTY] [{timestamp}] Exchange #{exchange_count} transcribed")
                exchange_count += 1

            time.sleep(check_interval_seconds)

        except KeyboardInterrupt:
            print("\n[SCRIPTY] Wrapping for the day")
            print(f"Final count: {exchange_count} exchanges transcribed")
            print(f"Memories served: {memory_count:,}")
            break
        except Exception as e:
            print(f"[SCRIPTY] Error: {e}")
            time.sleep(60)


def log_note_once(note: str = None):
    """Log a single note - for manual observations"""
    if note is None:
        note = "Manual timecode mark"

    print(f"[SCRIPTY] {note}")

    if log_observation(note):
        print(f"[SCRIPTY] Logged")
        return True
    return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Scripty - Production Transcriber (Full verbatim + memory counter)')
    parser.add_argument('--interval', type=int, default=30, help='Check interval in seconds')
    parser.add_argument('--note', type=str, help='Log a single note and exit')

    args = parser.parse_args()

    if args.note:
        log_note_once(args.note)
    else:
        watch_session(args.interval)
