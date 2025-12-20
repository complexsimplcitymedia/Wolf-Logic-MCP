#!/usr/bin/env python3
"""
Scripty Supervisor - Dynamic Instance Manager
Monitors active Claude sessions and spawns one llama3.2:1b instance per session.

Automatically scales:
- New session detected → spawn new llama3.2:1b
- Session closed → kill its llama3.2:1b
- Always maintains 1:1 mapping of sessions to AI instances
"""

import os
import sys
import time
import subprocess
import signal
from pathlib import Path
from datetime import datetime

# Configuration
SCRIPTY_SCRIPT = Path("/mnt/Wolf-code/Wolf-Ai-Enterptises/scripty/scripty_ai.py")
PYTHON_BIN = Path.home() / "anaconda3/envs/messiah/bin/python"
CHECK_INTERVAL = 10  # Check for new/closed sessions every 10 seconds
STALE_THRESHOLD = 300  # Consider session inactive after 5 minutes of no updates

# Track running instances: {session_file_path: subprocess.Popen}
running_instances = {}


def get_active_sessions():
    """Find all active Claude session files"""
    claude_dir = Path.home() / ".claude"
    projects_dir = claude_dir / "projects"

    if not projects_dir.exists():
        return []

    # Get all session files, exclude agent files
    session_files = list(projects_dir.glob("**/*.jsonl"))
    session_files = [f for f in session_files if not f.name.startswith('agent-')]

    # Filter to recently modified sessions (active within STALE_THRESHOLD)
    active_sessions = []
    now = time.time()
    for session_file in session_files:
        try:
            mtime = session_file.stat().st_mtime
            age = now - mtime
            if age < STALE_THRESHOLD:
                active_sessions.append(session_file)
        except:
            continue

    return active_sessions


def spawn_instance(session_file):
    """Spawn a llama3.2:1b instance for a specific session"""
    try:
        print(f"[SUPERVISOR] Spawning instance for {session_file.name}")

        # Launch scripty_ai.py with session-specific logging
        log_file = f"/var/log/scripty-ai-{session_file.stem}.log"

        process = subprocess.Popen(
            [str(PYTHON_BIN), str(SCRIPTY_SCRIPT), "--interval", "30"],
            stdout=open(log_file, 'a'),
            stderr=subprocess.STDOUT,
            start_new_session=True
        )

        running_instances[str(session_file)] = process
        print(f"[SUPERVISOR] Instance spawned (PID {process.pid}) for {session_file.name}")
        return True

    except Exception as e:
        print(f"[SUPERVISOR] Failed to spawn instance: {e}")
        return False


def kill_instance(session_file_path):
    """Kill the llama3.2:1b instance for a closed session"""
    try:
        process = running_instances[session_file_path]
        session_name = Path(session_file_path).name

        print(f"[SUPERVISOR] Killing instance (PID {process.pid}) for {session_name}")

        # Send SIGTERM, wait, then SIGKILL if needed
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

        del running_instances[session_file_path]
        print(f"[SUPERVISOR] Instance killed for {session_name}")
        return True

    except Exception as e:
        print(f"[SUPERVISOR] Failed to kill instance: {e}")
        return False


def cleanup_stale_instances():
    """Kill instances whose sessions are no longer active"""
    active_sessions = get_active_sessions()
    active_paths = {str(s) for s in active_sessions}

    # Find instances that no longer have active sessions
    stale_paths = set(running_instances.keys()) - active_paths

    for stale_path in stale_paths:
        kill_instance(stale_path)


def manage_instances():
    """Main supervisor loop - manage instance lifecycle"""
    print("=" * 60)
    print("SCRIPTY SUPERVISOR - DYNAMIC INSTANCE MANAGER")
    print("=" * 60)
    print(f"Model: llama3.2:1b per session")
    print(f"Check interval: {CHECK_INTERVAL}s")
    print(f"Stale threshold: {STALE_THRESHOLD}s")
    print("=" * 60)

    while True:
        try:
            # Get currently active sessions
            active_sessions = get_active_sessions()
            active_paths = {str(s) for s in active_sessions}
            running_paths = set(running_instances.keys())

            # Spawn instances for new sessions
            new_sessions = active_paths - running_paths
            for session_path in new_sessions:
                spawn_instance(Path(session_path))

            # Clean up instances for closed/stale sessions
            cleanup_stale_instances()

            # Status report
            if running_instances:
                print(f"\n[SUPERVISOR] [{datetime.now().strftime('%H:%M:%S')}] "
                      f"Managing {len(running_instances)} active instances")

            time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            print("\n[SUPERVISOR] Shutting down...")
            # Kill all running instances
            for session_path in list(running_instances.keys()):
                kill_instance(session_path)
            break

        except Exception as e:
            print(f"[SUPERVISOR] Error: {e}")
            time.sleep(30)


if __name__ == "__main__":
    manage_instances()
