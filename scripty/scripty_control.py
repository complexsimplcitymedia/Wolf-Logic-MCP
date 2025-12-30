#!/usr/bin/env python3
"""
Scripty Control - Daemon management for button integration
Start, stop, status, restart commands with PID file management
"""

import os
import sys
import json
import signal
import subprocess
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent
PID_FILE = SCRIPT_DIR / "scripty.pid"
LOG_FILE = Path("/tmp/scripty.log")
SCRIPTY_SCRIPT = SCRIPT_DIR / "scripty.py"


def is_running():
    """Check if scripty is currently running"""
    if not PID_FILE.exists():
        return False, None

    try:
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())

        # Check if process is actually running
        os.kill(pid, 0)  # Doesn't kill, just checks if process exists
        return True, pid
    except (OSError, ValueError, ProcessLookupError):
        # PID file exists but process is dead
        PID_FILE.unlink(missing_ok=True)
        return False, None


def start():
    """Start scripty daemon"""
    running, pid = is_running()

    if running:
        return {
            "success": False,
            "message": f"Scripty already running (PID: {pid})",
            "pid": pid,
            "status": "already_running"
        }

    # Start the daemon
    try:
        # Activate messiah env and run scripty
        messiah_python = Path.home() / "anaconda3/envs/messiah/bin/python"

        process = subprocess.Popen(
            [str(messiah_python), str(SCRIPTY_SCRIPT)],
            stdout=open(LOG_FILE, 'w'),
            stderr=subprocess.STDOUT,
            start_new_session=True  # Detach from parent
        )

        # Write PID file
        with open(PID_FILE, 'w') as f:
            f.write(str(process.pid))

        return {
            "success": True,
            "message": "Scripty started successfully",
            "pid": process.pid,
            "log_file": str(LOG_FILE),
            "status": "started"
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to start scripty: {e}",
            "status": "error"
        }


def stop():
    """Stop scripty daemon"""
    running, pid = is_running()

    if not running:
        return {
            "success": False,
            "message": "Scripty is not running",
            "status": "not_running"
        }

    try:
        # Send SIGTERM for graceful shutdown
        os.kill(pid, signal.SIGTERM)

        # Clean up PID file
        PID_FILE.unlink(missing_ok=True)

        return {
            "success": True,
            "message": f"Scripty stopped (PID: {pid})",
            "pid": pid,
            "status": "stopped"
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to stop scripty: {e}",
            "status": "error"
        }


def status():
    """Get scripty status"""
    running, pid = is_running()

    if running:
        # Get uptime from PID file mtime
        uptime_seconds = datetime.now().timestamp() - PID_FILE.stat().st_mtime
        uptime_minutes = int(uptime_seconds / 60)

        return {
            "success": True,
            "running": True,
            "pid": pid,
            "uptime_minutes": uptime_minutes,
            "log_file": str(LOG_FILE),
            "message": f"Scripty running (PID: {pid}, uptime: {uptime_minutes}m)",
            "status": "running"
        }
    else:
        return {
            "success": True,
            "running": False,
            "message": "Scripty is not running",
            "status": "stopped"
        }


def restart():
    """Restart scripty daemon"""
    stop_result = stop()

    # Wait a moment
    import time
    time.sleep(1)

    start_result = start()

    return {
        "success": start_result["success"],
        "message": f"Restart: {stop_result['message']} → {start_result['message']}",
        "pid": start_result.get("pid"),
        "status": "restarted" if start_result["success"] else "error"
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "success": False,
            "message": "Usage: scripty_control.py {start|stop|status|restart}"
        }))
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "start":
        result = start()
    elif command == "stop":
        result = stop()
    elif command == "status":
        result = status()
    elif command == "restart":
        result = restart()
    else:
        result = {
            "success": False,
            "message": f"Unknown command: {command}. Use: start, stop, status, or restart"
        }

    # Output JSON for API consumption
    print(json.dumps(result, indent=2))

    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
