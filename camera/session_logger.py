#!/usr/bin/env python3
"""
Session Logger - Complete Transcript Capture
Monitors Claude Code session and maintains in-depth logs of everything.
Every message, every tool call, every response - logged in full.

Union Way: The stenographer records for memory, the logger records for audit.
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path
import shutil

# Paths
CLAUDE_DIR = Path.home() / ".claude"
DAILYS_DIR = Path("/mnt/Wolf-code/Wolf-Ai-Enterptises/camera/dailys")

# Ensure directories exist
DAILYS_DIR.mkdir(parents=True, exist_ok=True)

def get_session_file():
    """Find the current Claude session file"""
    session_files = list(CLAUDE_DIR.glob("**/session*.json"))
    if session_files:
        return max(session_files, key=lambda p: p.stat().st_mtime)
    return None

def get_session_id(session_file):
    """Extract session ID from filename"""
    try:
        return session_file.stem.replace("session_", "")
    except:
        return datetime.now().strftime("%Y%m%d_%H%M%S")

def log_session_snapshot(session_file, session_id):
    """Create timestamped snapshot of session"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = DAILYS_DIR / f"session_{session_id}_{timestamp}.json"

    try:
        # Copy full session
        shutil.copy2(session_file, log_file)

        # Also create human-readable version
        with open(session_file, 'r') as f:
            session_data = json.load(f)

        readable_file = DAILYS_DIR / f"session_{session_id}_{timestamp}_readable.txt"
        with open(readable_file, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write(f"Claude Code Session Log - {datetime.now().isoformat()}\n")
            f.write(f"Session ID: {session_id}\n")
            f.write("=" * 80 + "\n\n")

            # Write formatted session data
            if 'messages' in session_data:
                for i, msg in enumerate(session_data['messages']):
                    f.write(f"\n[Message {i+1}] Role: {msg.get('role', 'unknown')}\n")
                    f.write(f"Timestamp: {msg.get('timestamp', 'N/A')}\n")
                    f.write("-" * 80 + "\n")
                    f.write(msg.get('content', '') + "\n")
                    f.write("-" * 80 + "\n")
            else:
                f.write(json.dumps(session_data, indent=2))

        return True

    except Exception as e:
        print(f"[SESSION_LOGGER] Error logging snapshot: {e}")
        return False

def monitor_sessions(interval_seconds=60):
    """Monitor and log sessions continuously"""
    print("=" * 80)
    print("SESSION LOGGER - Complete Transcript Capture")
    print("=" * 80)
    print(f"Log directory: {DAILYS_DIR}")
    print(f"Snapshot interval: {interval_seconds}s")
    print("Logging mode: IN-DEPTH - Everything captured")
    print("=" * 80)

    last_session_id = None
    snapshot_count = 0

    while True:
        try:
            session_file = get_session_file()

            if session_file and session_file.exists():
                session_id = get_session_id(session_file)

                # New session detected
                if session_id != last_session_id:
                    print(f"\n[SESSION_LOGGER] New session detected: {session_id}")
                    last_session_id = session_id
                    snapshot_count = 0

                # Log snapshot
                if log_session_snapshot(session_file, session_id):
                    snapshot_count += 1
                    file_size = session_file.stat().st_size
                    print(f"[SESSION_LOGGER] Snapshot #{snapshot_count} - Size: {file_size:,} bytes")

            time.sleep(interval_seconds)

        except KeyboardInterrupt:
            print("\n[SESSION_LOGGER] Stopped by user")
            break
        except Exception as e:
            print(f"[SESSION_LOGGER] Error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Session Logger - In-depth transcript capture')
    parser.add_argument('--interval', type=int, default=60, help='Snapshot interval in seconds')

    args = parser.parse_args()

    monitor_sessions(args.interval)
