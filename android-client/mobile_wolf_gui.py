import termuxgui as tg
import requests
import json
import time
import os
import subprocess

# Wolf Logic Mobile Controller - Termux-GUI Edition
# Target: Localhost FastAPI on S24 Ultra

API_BASE = "http://127.0.0.1:8000/api"

def on_click(event):
    btn_id = event['id']
    if btn_id == "refresh":
        update_stats()
    elif btn_id == "ingest":
        filepath = tg.get_value(path_input)
        if filepath:
            execute_cmd("ingest_file", {"filepath": filepath})
    elif btn_id == "start_stack":
        start_local_stack()
    else:
        execute_cmd(btn_id)

def start_local_stack():
    """Wake up Postgres and FastAPI locally"""
    tg.set_text(status_view, "Starting Postgres & FastAPI...")
    try:
        # This assumes standard Termux start scripts are in place
        subprocess.Popen(["pg_ctl", "-D", "$PREFIX/var/lib/postgresql", "start"])
        time.sleep(3)
        subprocess.Popen(["python", "api/fastapi_server.py"])
        time.sleep(3)
        update_stats()
    except Exception as e:
        tg.set_text(status_view, f"Boot Error: {e}")

def execute_cmd(cmd, params={}):
    try:
        tg.set_text(status_view, f"Executing {cmd}...")
        r = requests.post(f"{API_BASE}/execute", json={"command": cmd, "params": params}, timeout=15)
        res = r.json()
        tg.set_text(status_view, f"RES: {json.dumps(res.get('data', res), indent=2)}")
    except Exception as e:
        tg.set_text(status_view, f"ERROR: {str(e)}")

def update_stats():
    try:
        r = requests.get(f"{API_BASE}/memory-stats", timeout=5)
        stats = r.json()
        tg.set_text(counter_view, f"Memories: {stats['total_memories']:,}")
        tg.set_text(status_view, "Connected to Wolf Brain.")
    except:
        tg.set_text(counter_view, "OFFLINE")
        tg.set_text(status_view, "OFFLINE. Tap 'START STACK' to wake up.")

# Initialize Termux-GUI Connection
with tg.Connection() as conn:
    activity = tg.Activity(conn)
    layout = tg.LinearLayout(activity)
    
    # Header
    tg.TextView(layout, "WOLF AI MOBILE CONTROL", size=24, color="#ff0000", gravity="center")
    
    # Stats
    counter_view = tg.TextView(layout, "Initializing...", size=30, color="#00ff88", gravity="center")
    
    # Ingest Area
    tg.TextView(layout, "INGEST PATH:", margin_top=15)
    path_input = tg.EditText(layout, hint="/sdcard/Documents/patent.pdf")
    
    # Buttons
    grid = tg.GridLayout(layout, columns=2)
    tg.Button(grid, "REFRESH STATS", id="refresh")
    tg.Button(grid, "INGEST FILE", id="ingest")
    tg.Button(grid, "START STACK", id="start_stack")
    tg.Button(grid, "STOP SCRIPTY", id="scripty_stop")
    tg.Button(grid, "DB HEALTH", id="db_stats")
    tg.Button(grid, "RANK MEMORIES", id="rank_memories")
    
    # Console
    tg.TextView(layout, "SYSTEM FEED:", margin_top=15, color="#ff00ff")
    status_view = tg.TextView(layout, "Checking Database...", size=12, color="#cccccc")
    
    activity.set_on_click_listener(on_click)
    
    # Startup Check
    update_stats()
    
    activity.show()
    conn.wait_for_close()
