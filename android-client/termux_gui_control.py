import termuxgui as tg
import requests
import json
import time

# Points to this server's Tailscale IP
API_BASE = "http://100.110.82.181:8000/api"

def on_click(event):
    btn_id = event['id']
    if btn_id == "refresh":
        update_stats()
    elif btn_id == "ingest":
        path = tg.get_value(path_input)
        if path:
            execute_cmd("ingest_file", {"filepath": path})
    else:
        execute_cmd(btn_id)

def execute_cmd(cmd, params={}):
    try:
        tg.set_text(status_text, f"Executing {cmd}...")
        r = requests.post(f"{API_BASE}/execute", json={"command": cmd, "params": params}, timeout=30)
        result = r.json()
        tg.set_text(status_text, f"SUCCESS: {cmd}\n{json.dumps(result.get('data', {}), indent=2)}")
    except Exception as e:
        tg.set_text(status_text, f"ERROR: {str(e)}")

def update_stats():
    try:
        r = requests.get(f"{API_BASE}/memory-stats", timeout=5)
        stats = r.json()
        tg.set_text(counter_label, f"MEMORIES: {stats['total_memories']:,}")
        tg.set_text(status_text, f"Librarian Check: {time.strftime('%H:%M:%S')}")
    except:
        tg.set_text(counter_label, "MEMORIES: OFFLINE")

# Layout Definition
with tg.Connection() as conn:
    activity = tg.Activity(conn)
    layout = tg.LinearLayout(activity)
    
    tg.TextView(layout, "WOLF ENTERPRISES MOBILE", size=22, color="#ff0000")
    counter_label = tg.TextView(layout, "MEMORIES: --", size=28, color="#00ff88")
    
    tg.TextView(layout, "INGEST PATH (No Auto-Correct):", margin_top=10)
    path_input = tg.EditText(layout, hint="/sdcard/Documents/patent.pdf")
    
    grid = tg.GridLayout(layout, columns=2)
    tg.Button(grid, "REFRESH STATS", id="refresh")
    tg.Button(grid, "INGEST FILE", id="ingest")
    tg.Button(grid, "START SCRIPTY", id="scripty_start")
    tg.Button(grid, "STOP SCRIPTY", id="scripty_stop")
    tg.Button(grid, "DB STATS", id="db_stats")
    tg.Button(grid, "RANK MEMS", id="rank_memories")
    
    tg.TextView(layout, "PRODUCTION LOG:", margin_top=15)
    status_text = tg.TextView(layout, "System Standby.", color="#888", size=12)
    
    activity.set_on_click_listener(on_click)
    update_stats()
    activity.show()
    conn.wait_for_close()
