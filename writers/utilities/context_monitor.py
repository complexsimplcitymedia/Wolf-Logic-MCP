#!/usr/bin/env python3
"""
Context Monitor - Watches Claude Code token usage, dumps at 95%
Monitors Claude session files and triggers full dump when context hits 95%.
"""

import os
import time
import json
import subprocess
from pathlib import Path
from datetime import datetime

# Thresholds
DUMP_THRESHOLD = 0.95  # 95% context usage
CHECK_INTERVAL = 30  # Check every 30 seconds

# Paths
CLAUDE_DIR = Path.home() / ".claude"
DUMP_DIR = Path("/mnt/Wolf-code/Wolf-Ai-Enterptises/data/memory-dumps")
INGEST_SCRIPT = Path("/mnt/Wolf-code/Wolf-Ai-Enterptises/writers/ingest_agent.py")
MESSIAH_ENV = Path.home() / "anaconda3/envs/messiah/bin/python"

def get_session_file():
    """Find the current Claude session file"""
    session_files = list(CLAUDE_DIR.glob("**/session*.json"))
    if session_files:
        return max(session_files, key=lambda p: p.stat().st_mtime)
    return None

def get_token_usage():
    """Extract token usage from session file"""
    session_file = get_session_file()
    if not session_file or not session_file.exists():
        return None

    try:
        with open(session_file, 'r') as f:
            data = json.load(f)

        # Look for token usage in session data
        # This structure may vary - adjust based on actual session file format
        if 'usage' in data:
            used = data['usage'].get('tokens_used', 0)
            total = data['usage'].get('tokens_total', 200000)
            return used / total if total > 0 else 0

        return None
    except Exception as e:
        print(f"[CONTEXT_MONITOR] Error reading session: {e}")
        return None

def dump_session():
    """Dump current session to file and ingest it"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dump_file = DUMP_DIR / f"context_dump_{timestamp}.jsonl"

    print(f"[CONTEXT_MONITOR] 95% threshold reached! Dumping session...")

    # Copy session file to dump directory
    session_file = get_session_file()
    if session_file and session_file.exists():
        try:
            with open(session_file, 'r') as src:
                session_data = src.read()

            with open(dump_file, 'w') as dst:
                dst.write(session_data)

            print(f"[CONTEXT_MONITOR] Dumped to: {dump_file}")

            # Trigger ingestion
            print(f"[CONTEXT_MONITOR] Starting ingestion...")
            subprocess.run([
                str(MESSIAH_ENV),
                str(INGEST_SCRIPT),
                str(dump_file)
            ], check=True)

            print(f"[CONTEXT_MONITOR] Ingestion complete!")
            return True

        except Exception as e:
            print(f"[CONTEXT_MONITOR] Dump failed: {e}")
            return False

    return False

def monitor_loop():
    """Main monitoring loop"""
    print("=" * 60)
    print("CONTEXT MONITOR - Watching for 95% threshold")
    print("=" * 60)
    print(f"Check interval: {CHECK_INTERVAL}s")
    print(f"Dump threshold: {DUMP_THRESHOLD * 100}%")
    print("=" * 60)

    last_usage = 0
    dump_triggered = False

    while True:
        try:
            usage = get_token_usage()

            if usage is not None:
                # Reset dump flag if usage dropped (new session)
                if usage < 0.5 and dump_triggered:
                    dump_triggered = False
                    print(f"[CONTEXT_MONITOR] New session detected, reset dump flag")

                # Show progress every 10% increase
                if int(usage * 10) > int(last_usage * 10):
                    print(f"[CONTEXT_MONITOR] Context usage: {usage * 100:.1f}%")
                    last_usage = usage

                # Trigger dump at 95%
                if usage >= DUMP_THRESHOLD and not dump_triggered:
                    if dump_session():
                        dump_triggered = True

            time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            print("\n[CONTEXT_MONITOR] Stopped by user")
            break
        except Exception as e:
            print(f"[CONTEXT_MONITOR] Error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    # Ensure dump directory exists
    DUMP_DIR.mkdir(parents=True, exist_ok=True)

    # Run monitor loop
    monitor_loop()
