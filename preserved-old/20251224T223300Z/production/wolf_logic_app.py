"""
Wolf Logic AI - Flask Backend
Control surface + script runner with MemZero environment integration

Runs on port 4500
Frontend connects from http://localhost:2500
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import subprocess
import sys
import json
from pathlib import Path
import tempfile
import time
import threading
import os

app = Flask(__name__, static_folder='control_center', template_folder='control_center')
CORS(app)

# Load script registry
SCRIPT_REGISTRY_PATH = Path(__file__).parent / "script_registry.json"
SCRIPT_REGISTRY = {}
if SCRIPT_REGISTRY_PATH.exists():
    with open(SCRIPT_REGISTRY_PATH, 'r') as f:
        registry_data = json.load(f)
        SCRIPT_REGISTRY = registry_data.get('scripts', {})
        BASE_PATH = registry_data.get('base_path', str(Path(__file__).parent))
else:
    BASE_PATH = str(Path(__file__).parent)

# Directory to store scripts
SCRIPTS_DIR = Path(__file__).parent / "wolf_scripts"
SCRIPTS_DIR.mkdir(exist_ok=True)

# Track slot -> script name mapping - Reorganized for actual available scripts
slots_map = {
    0: "InitOllama",         # Button 1: Initialize Ollama Connection
    1: "StartMistral",       # Button 2: Start Mistral Model
    2: "StartEmbedder",      # Button 3: Start Embedder Service
    3: "StartRetriever",     # Button 4: Start Retriever Service
    4: "MemoryInit",         # Button 5: Initialize Memory System
    5: "AddMemory",          # Button 6: Add New Memory
    6: "MemorySearch",       # Button 7: Search Memories
    7: "ChatBegin",          # Button 8: Start Chat Session
    8: "ContextLoad",        # Button 9: Load Context
    9: "AgentStatus",        # Button 10: Check Agent Status
    10: "ExportMemory",      # Button 11: Export Memory Data
    11: "ImportMemory",      # Button 12: Import Memory Data
    12: "ModelSwitch",       # Button 13: Switch Mistral Model
    13: "TuneParams",        # Button 14: Tune Model Parameters
    14: "BenchmarkRun",      # Button 15: Run Performance Benchmark
    15: "vector_categorize", # Button 16: Vector Memory Agent - Categorize
    16: "neo4j_stats",       # Button 17: Neo4j Statistics
    17: "find_similar",      # Button 18: Find Similar Memories
    18: "find_by_category",  # Button 19: Find by Category
    19: "export_graph",      # Button 20: Export Graph Snapshot
    20: "relationship_recall" # Button 21: Relationship Recall
}
slots_lock = threading.Lock()

# Pre-populate script names for immediate use - Ollama/Mistral Workflow
PREDEFINED_SCRIPTS = {
    "InitOllama": "🔥 Init Ollama",
    "StartMistral": "🧠 Start Mistral",
    "StartEmbedder": "🚀 Start Embedder",
    "StartRetriever": "🔍 Start Retriever",
    "MemoryInit": "💾 Memory Init",
    "AddMemory": "➕ Add Memory",
    "MemorySearch": "🔎 Memory Search",
    "ChatBegin": "💬 Chat Begin",
    "ContextLoad": "📚 Context Load",
    "AgentStatus": "📊 Agent Status",
    "ExportMemory": "📤 Export Memory",
    "ImportMemory": "📥 Import Memory",
    "ModelSwitch": "🔄 Model Switch",
    "TuneParams": "⚙️ Tune Params",
    "BenchmarkRun": "⏱️ Benchmark Run",
    "vector_categorize": "🧠 Vector Categorize",
    "neo4j_stats": "📊 Neo4j Stats",
    "find_similar": "🔎 Find Similar",
    "find_by_category": "🔍 Find by Category",
    "export_graph": "📤 Export Graph",
    "relationship_recall": "🔗 Relationship Recall"
}


@app.route("/scripts/state", methods=["GET"])
def get_scripts_state():
    """Return current state of all 32 slots"""
    with slots_lock:
        slots = []
        for i in range(32):
            script_name = slots_map.get(i, None)
            if script_name and script_name in PREDEFINED_SCRIPTS:
                # Use friendly display name for predefined scripts
                display_name = PREDEFINED_SCRIPTS[script_name]
            else:
                display_name = script_name
            slots.append({"name": display_name})
    return jsonify({"slots": slots})


@app.route("/api/scripts", methods=["GET"])
def get_api_scripts():
    """Get all available scripts for control center UI"""
    scripts = []
    for slot_id, script_name in slots_map.items():
        if script_name in PREDEFINED_SCRIPTS:
            scripts.append({
                'id': script_name,
                'name': PREDEFINED_SCRIPTS[script_name],
                'slot': slot_id,
                'category': 'workflow'
            })
    return jsonify({'scripts': scripts})


@app.route("/api/config", methods=["GET"])
def get_config():
    """Get configuration for control center"""
    return jsonify({
        'layout': list(slots_map.values()),
        'total_slots': 32,
        'active_slots': len(slots_map)
    })


@app.route("/api/execute/<script_id>", methods=["POST"])
def execute_script_by_id(script_id):
    """Execute a script by ID from control center"""
    # Find the slot for this script
    slot = None
    for slot_num, script_name in slots_map.items():
        if script_name == script_id:
            slot = slot_num
            break
    
    if slot is None:
        return jsonify({'error': 'Script not found', 'ok': False}), 404
    
    # Create request data with the slot
    script_name = script_id
    
    try:
        # Run with MemZero environment using script name
        script_path = f"wolf_scripts/{script_name}.py"
        result = run_script_in_memzero(script_path)
        
        return jsonify({
            "ok": result["returncode"] == 0,
            "output": result["stdout"] if result["stdout"] else result["stderr"],
            "name": script_name,
            "returncode": result["returncode"]
        })
    
    except Exception as e:
        return jsonify({
            "ok": False,
            "output": f"Error: {str(e)}",
            "name": script_name
        }), 500


@app.route("/api/status/<script_id>", methods=["GET"])
def get_script_status(script_id):
    """Get status of a script"""
    return jsonify({
        'id': script_id,
        'status': 'ready',
        'running': False
    })


@app.route("/scripts/create", methods=["POST"])
def create_script():
    """Create a new script slot and open Kate"""
    data = request.json or {}
    slot = data.get("slot")
    
    if slot is None or not (0 <= slot < 32):
        return jsonify({"ok": False, "error": "Invalid slot"}), 400
    
    try:
        # Create temp file in wolf_scripts directory
        temp_file = SCRIPTS_DIR / f"slot_{slot}_temp.py"
        temp_file.write_text(
            "# Your script here\n"
            "# This runs with MemZero environment activated\n\n"
            "def run():\n"
            "    pass\n"
        )
        
        # Launch Kate and wait for it to close
        subprocess.run(["kate", str(temp_file)])
        
        # Read the saved file
        script_content = temp_file.read_text()
        
        # Extract script name - use a sanitized version based on slot
        # For now, use the first comment or default name
        script_name = f"slot_{slot}_script"
        lines = script_content.split('\n')
        for line in lines:
            if line.strip().startswith('# ') and 'Your script' not in line:
                # Extract name from first meaningful comment
                potential_name = line.replace('#', '').strip()[:30]
                if potential_name and len(potential_name) > 2:
                    script_name = potential_name.replace(' ', '_')
                    break
        
        # Store permanently
        final_file = SCRIPTS_DIR / f"{script_name}.py"
        final_file.write_text(script_content)
        
        # Clean up temp
        temp_file.unlink(missing_ok=True)
        
        # Update mapping
        with slots_lock:
            slots_map[slot] = script_name
        
        return jsonify({"ok": True, "name": script_name})
    
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/scripts/run", methods=["POST"])
def run_script():
    """Execute a script for a given slot with MemZero environment"""
    data = request.json or {}
    slot = data.get("slot")
    script_id = data.get("script_id")  # Optional: directly specify script by ID
    
    if slot is None and script_id is None:
        return jsonify({"ok": False, "error": "Must provide slot or script_id"}), 400
    
    # Determine which script to run
    if script_id and script_id in SCRIPT_REGISTRY:
        # Use script registry
        script_info = SCRIPT_REGISTRY[script_id]
        script_path = script_info['path']
        script_name = script_info['name']
    elif slot is not None and (0 <= slot < 32):
        # Use slot mapping
        with slots_lock:
            script_name = slots_map.get(slot)
        
        if not script_name:
            return jsonify({"ok": False, "error": "No script assigned"}), 404
        
        script_path = f"wolf_scripts/{script_name}.py"
    else:
        return jsonify({"ok": False, "error": "Invalid slot or script_id"}), 400
    
    try:
        # Run with MemZero environment using absolute path
        result = run_script_in_memzero(script_path)
        
        return jsonify({
            "ok": result["returncode"] == 0,
            "output": result["stdout"] if result["stdout"] else result["stderr"],
            "name": script_name,
            "returncode": result["returncode"]
        })
    
    except Exception as e:
        return jsonify({
            "ok": False,
            "output": f"Error: {str(e)}",
            "name": script_name if 'script_name' in locals() else "unknown"
        }), 500


@app.route("/scripts/delete", methods=["POST"])
def delete_script():
    """Delete a script assignment"""
    data = request.json or {}
    slot = data.get("slot")
    
    if slot is None or not (0 <= slot < 32):
        return jsonify({"ok": False, "error": "Invalid slot"}), 400
    
    with slots_lock:
        if slot in slots_map:
            script_name = slots_map.pop(slot)
            script_path = SCRIPTS_DIR / f"{script_name}.py"
            if script_path.exists():
                script_path.unlink()
            return jsonify({"ok": True, "deleted": script_name})
        else:
            return jsonify({"ok": False, "error": "No script assigned"}), 404


@app.route("/scripts/edit", methods=["POST"])
def edit_script():
    """Open existing script in Kate for editing"""
    data = request.json or {}
    slot = data.get("slot")
    
    if slot is None or not (0 <= slot < 32):
        return jsonify({"ok": False, "error": "Invalid slot"}), 400
    
    with slots_lock:
        script_name = slots_map.get(slot)
    
    if not script_name:
        return jsonify({"ok": False, "error": "No script assigned"}), 404
    
    script_path = SCRIPTS_DIR / f"{script_name}.py"
    
    if not script_path.exists():
        return jsonify({"ok": False, "error": "Script file not found"}), 404
    
    try:
        subprocess.run(["kate", str(script_path)])
        return jsonify({"ok": True, "name": script_name})
    
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/memory/count", methods=["GET"])
def get_memory_count():
    """Get memory count from postgres"""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="100.110.82.181",
            port=5433,
            database="wolf_logic",
            user="wolf",
            password="wolflogic2024"
        )
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM memories")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return jsonify({"total": count})
    except Exception as e:
        return jsonify({"error": str(e), "total": 0}), 500


@app.route("/api/gpu/stats", methods=["GET"])
def get_gpu_stats():
    """Get AMD GPU statistics from LACT daemon"""
    try:
        result = subprocess.run(
            ["flatpak", "run", "io.github.ilya_zlobintsev.LACT", "cli", "stats"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            return jsonify({"error": "LACT command failed", "success": False}), 500

        # Parse LACT output
        output = result.stdout
        gpu_data = {}

        for line in output.split('\n'):
            line = line.strip()

            if line.startswith("GPU Clockspeed:"):
                gpu_data["gpu_clock_mhz"] = int(line.split(":")[1].strip().replace(" MHz", ""))

            elif line.startswith("VRAM Usage:"):
                vram_str = line.split(":")[1].strip()
                used, total = vram_str.replace(" MiB", "").split("/")
                vram_used_mib = int(used)
                vram_total_mib = int(total)

                gpu_data["vram_used_gb"] = round(vram_used_mib / 1024, 2)
                gpu_data["vram_total_gb"] = round(vram_total_mib / 1024, 2)
                gpu_data["vram_free_gb"] = round((vram_total_mib - vram_used_mib) / 1024, 2)
                gpu_data["vram_usage_percent"] = round((vram_used_mib / vram_total_mib) * 100, 1)

            elif line.startswith("Temperatures:"):
                temps_str = line.split(":", 1)[1].strip()
                for temp_pair in temps_str.split(", "):
                    name, value = temp_pair.split(": ")
                    temp_c = float(value.replace("°C", ""))
                    if name == "edge":
                        gpu_data["temp_edge_c"] = temp_c
                    elif name == "junction":
                        gpu_data["temp_junction_c"] = temp_c
                    elif name == "mem":
                        gpu_data["temp_memory_c"] = temp_c

            elif line.startswith("GPU Voltage:"):
                voltage_mv = int(line.split(":")[1].strip().replace(" mV", ""))
                gpu_data["gpu_voltage_mv"] = voltage_mv

            elif line.startswith("Fan Speed:"):
                fan_str = line.split(":")[1].strip()
                percent = int(fan_str.split("%")[0])
                rpm = int(fan_str.split("(")[1].split(" RPM")[0])
                gpu_data["fan_speed_percent"] = percent
                gpu_data["fan_speed_rpm"] = rpm

        # Calculate GPU usage from clock speed
        max_clock = 2500
        current_clock = gpu_data.get("gpu_clock_mhz", 0)
        gpu_data["gpu_usage_percent"] = round((current_clock / max_clock) * 100, 1)
        gpu_data["power_draw_watts"] = round((current_clock / max_clock) * 315, 1)

        return jsonify({
            "success": True,
            "gpu": "AMD Radeon RX 7900 XT",
            "data": gpu_data,
            "timestamp": time.time()
        })

    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "service": "Wolf Logic API",
        "scripts_dir": str(SCRIPTS_DIR),
        "active_slots": len(slots_map)
    })


def run_script_in_memzero(script_path: str) -> dict:
    """
    Run a script on the host machine via FastAPI executor service.
    Calls the wolf_executor_api.py running on host:5500
    
    Returns:
        dict with stdout, stderr, returncode
    """
    
    try:
        import requests
        
        # Ensure we always send an absolute path so the remote executor
        # invokes the exact project script regardless of its CWD.
        base_dir = Path(BASE_PATH).resolve()
        script_path_obj = Path(script_path)
        if not script_path_obj.is_absolute():
            script_path_obj = (base_dir / script_path_obj).resolve()
        else:
            script_path_obj = script_path_obj.resolve()
        
        # Extract script name from the absolute path for logging
        script_name = script_path_obj.stem
        
        # Call FastAPI executor on host
        response = requests.post(
            "http://host.docker.internal:5500/execute",
            json={
                "script_name": script_name,
                "script_path": str(script_path_obj)
            },
            timeout=65
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "stdout": data.get("output", ""),
                "stderr": "",
                "returncode": data.get("returncode", 0)
            }
        else:
            error_detail = response.json().get("detail", response.text)
            return {
                "stdout": "",
                "stderr": f"Executor API error ({response.status_code}): {error_detail}",
                "returncode": 1
            }
    
    except requests.exceptions.ConnectionError:
        return {
            "stdout": "",
            "stderr": "Cannot connect to executor API on host:5500. Is wolf_executor_api.py running?",
            "returncode": 1
        }
    except Exception as e:
        return {
            "stdout": "",
            "stderr": f"Execution error: {str(e)}",
            "returncode": 1
        }
    except Exception as e:
        return {
            "stdout": "",
            "stderr": f"Execution error: {str(e)}",
            "returncode": 1
        }


@app.route("/")
def index():
    """Serve the control center UI"""
    return send_from_directory('control_center', 'index.html')


@app.route("/wolf_logo.png")
def serve_logo():
    """Serve Wolf Logic logo"""
    return send_from_directory('control_center', 'wolf_logo.png')


@app.route("/<path:path>")
def serve_static(path):
    """Serve static files from control_center"""
    return send_from_directory('control_center', path)


if __name__ == "__main__":
    port = int(os.environ.get('WOLF_LOGIC_PORT', 4500))
    print(f"Wolf Logic Control Center starting on http://0.0.0.0:{port}")
    print(f"Scripts directory: {SCRIPTS_DIR}")
    print(f"MemZero environment will be auto-activated for all scripts")
    print(f"Serving control center UI from: control_center/")

    app.run(debug=True, port=port, host="0.0.0.0")
