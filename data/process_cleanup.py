#!/usr/bin/env python3
"""
Process Cleanup Script - System Integrity Maintenance
Kills orphaned Python processes running backup_sync.py
Keeps system clean, no ghost processes
"""

import psutil
import time
import sys
from datetime import datetime

SCRIPT_NAME = "backup_sync.py"
CHECK_INTERVAL = 300  # Check every 5 minutes

def log(message):
    """Log with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")
    sys.stdout.flush()

def find_backup_sync_processes():
    """Find all Python processes running backup_sync.py"""
    backup_processes = []

    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
        try:
            # Check if it's a Python process running backup_sync.py
            if proc.info['name'] and 'python' in proc.info['name'].lower():
                cmdline = proc.info['cmdline']
                if cmdline and any(SCRIPT_NAME in arg for arg in cmdline):
                    backup_processes.append({
                        'pid': proc.info['pid'],
                        'cmdline': ' '.join(cmdline),
                        'created': datetime.fromtimestamp(proc.info['create_time']),
                        'process': proc
                    })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return backup_processes

def cleanup_old_processes(processes):
    """Keep only the newest process, kill the rest"""
    if len(processes) <= 1:
        log(f"Found {len(processes)} backup_sync process(es) - no cleanup needed")
        return 0

    # Sort by creation time, newest first
    processes.sort(key=lambda p: p['created'], reverse=True)

    # Keep the newest one
    newest = processes[0]
    log(f"Keeping newest process: PID {newest['pid']} (started {newest['created']})")

    # Kill the rest
    killed_count = 0
    for proc_info in processes[1:]:
        try:
            proc_info['process'].terminate()
            proc_info['process'].wait(timeout=5)
            log(f"Killed orphan process: PID {proc_info['pid']} (started {proc_info['created']})")
            killed_count += 1
        except psutil.TimeoutExpired:
            # Force kill if graceful termination fails
            proc_info['process'].kill()
            log(f"Force-killed stubborn process: PID {proc_info['pid']}")
            killed_count += 1
        except Exception as e:
            log(f"Error killing PID {proc_info['pid']}: {e}")

    return killed_count

def main():
    """Main cleanup loop"""
    log("Process cleanup script started")
    log(f"Monitoring for orphaned {SCRIPT_NAME} processes")
    log(f"Check interval: {CHECK_INTERVAL} seconds")

    while True:
        try:
            processes = find_backup_sync_processes()

            if processes:
                killed = cleanup_old_processes(processes)
                if killed > 0:
                    log(f"Cleanup complete: {killed} orphan(s) terminated")
            else:
                log("No backup_sync processes found")

        except Exception as e:
            log(f"ERROR during cleanup cycle: {e}")

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
