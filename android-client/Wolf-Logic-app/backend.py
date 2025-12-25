#!/usr/bin/env python3
"""
Complex Logic App - Backend API Server
Port: 2500
Provides API endpoints for script execution, GPU metrics, and system status
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import subprocess
import os
import json
import psutil
import glob
from datetime import datetime
from pathlib import Path
import socket
import psycopg2

app = Flask(__name__, static_folder='wolf-ui/build', static_url_path='')
CORS(app)

# Base directory for scripts (inside container)
BASE_DIR = Path(__file__).parent.resolve()
SCRIPTS_ROOT = BASE_DIR / "writers"

# Process tracking
running_processes = {}

# ==================== SCRIPT REGISTRY (dynamic) ====================

def discover_scripts(limit: int = 32):
    """
    Scan writers/ for runnable scripts (.py/.sh) and register them.
    Category comes from immediate parent directory.
    """
    scripts = []
    if not SCRIPTS_ROOT.exists():
        return scripts

    candidates = sorted(
        [p for p in SCRIPTS_ROOT.rglob("*") if p.suffix in {".py", ".sh"}],
        key=lambda p: str(p.relative_to(SCRIPTS_ROOT)).lower()
    )

    for script_path in candidates:
        # Skip cache/init files
        if script_path.name.startswith("__init__") or "__pycache__" in script_path.parts:
            continue

        rel = script_path.relative_to(BASE_DIR)
        rel_id = str(rel.with_suffix("")).replace(os.sep, "__")
        scripts.append({
            'id': rel_id,
            'name': script_path.stem.replace('_', ' ').title(),
            'script': str(rel),
            'category': script_path.parent.name
        })
        if len(scripts) >= limit:
            break
    return scripts

WOLF_SCRIPTS = discover_scripts()

# ==================== GPU METRICS ====================

def read_file_int(filepath):
    try:
        with open(filepath, 'r') as f:
            return int(f.read().strip())
    except:
        return 0

def get_gpu_metrics():
    """Get GPU metrics from sysfs or fallback"""
    try:
        device_path = '/sys/class/drm/card1/device'
        hwmon_paths = glob.glob(f'{device_path}/hwmon/hwmon*')
        
        if hwmon_paths:
            hwmon = hwmon_paths[0]
            temp = read_file_int(f"{hwmon}/temp1_input") / 1000
            power = read_file_int(f"{hwmon}/power1_average") / 1000000
            gpu_busy = read_file_int(f"{device_path}/gpu_busy_percent")
            vram_used = read_file_int(f"{device_path}/mem_info_vram_used") // (1024 * 1024)
            vram_total = read_file_int(f"{device_path}/mem_info_vram_total") // (1024 * 1024)
            fan_rpm = read_file_int(f"{hwmon}/fan1_input")
            
            return {
                'source': 'sysfs', 'load': gpu_busy, 'temperature': int(temp),
                'vram_used': vram_used, 'vram_total': vram_total or 8192,
                'power_draw': int(power), 'fan_speed': fan_rpm
            }
    except:
        pass
    
    # Fallback mock data
    import random
    cpu = psutil.cpu_percent(interval=0.1)
    load = min(100, max(0, cpu + random.randint(-10, 20)))
    return {
        'source': 'simulated', 'load': int(load), 'temperature': int(45 + load * 0.4),
        'vram_used': int(1500 + random.random() * 2000), 'vram_total': 8192,
        'power_draw': int(80 + load * 1.5), 'fan_speed': int(800 + load * 10)
    }

def get_system_metrics():
    cpu = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    return {
        'cpu': {'percent': cpu, 'cores': psutil.cpu_count()},
        'memory': {'total_gb': mem.total // (1024**3), 'used_gb': mem.used // (1024**3), 'percent': mem.percent},
        'disk': {'total_gb': disk.total // (1024**3), 'used_gb': disk.used // (1024**3), 'percent': disk.percent}
    }

def get_service_status():
    services = {
        'neo4j': 7687, 'qdrant': 6333, 'postgres': 5432,
        'ollama': 11434, 'openmemory': 8765, 'graphql': 25000
    }
    results = {}
    for name, port in services.items():
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.3)
        status = 'online' if sock.connect_ex(('127.0.0.1', port)) == 0 else 'offline'
        sock.close()
        results[name] = {'port': port, 'status': status}
    return results

# ==================== API ENDPOINTS ====================

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'Complex Logic App', 'ports': {'frontend': 3333, 'backend': 2500}})

@app.route('/api/gpu-stats')
def gpu_stats():
    return jsonify({'success': True, 'data': get_gpu_metrics()})

@app.route('/api/system-stats')
def system_stats():
    return jsonify({'success': True, 'data': get_system_metrics()})

@app.route('/api/services')
def services():
    return jsonify({'success': True, 'data': get_service_status()})

def get_memory_count():
    """Get memory count from PostgreSQL"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('WOLF_PG_HOST', '127.0.0.1'),
            port=int(os.getenv('WOLF_PG_PORT', '5433')),
            database=os.getenv('WOLF_PG_DB', 'wolf_logic'),
            user=os.getenv('WOLF_PG_USER', 'wolf'),
            password=os.getenv('WOLF_PG_PASSWORD', 'wolflogic2024')
        )
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM memories;")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return count
    except Exception as e:
        return 0

def get_recent_memories(limit=50):
    """Get recent memories from PostgreSQL"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('WOLF_PG_HOST', '127.0.0.1'),
            port=int(os.getenv('WOLF_PG_PORT', '5433')),
            database=os.getenv('WOLF_PG_DB', 'wolf_logic'),
            user=os.getenv('WOLF_PG_USER', 'wolf'),
            password=os.getenv('WOLF_PG_PASSWORD', 'wolflogic2024')
        )
        cur = conn.cursor()
        cur.execute("""
            SELECT id, content, created_at
            FROM memories
            ORDER BY created_at DESC
            LIMIT %s;
        """, (limit,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [{
            'id': r[0],
            'content': r[1],
            'created_at': r[2].isoformat() if hasattr(r[2], "isoformat") else str(r[2])
        } for r in rows]
    except Exception:
        return []

@app.route('/api/lcd-data')
def lcd_data():
    return jsonify({
        'success': True,
        'data': {
            'gpu': get_gpu_metrics(),
            'system': get_system_metrics(),
            'services': get_service_status(),
            'timestamp': datetime.now().isoformat()
        }
    })

@app.route('/api/metrics')
def metrics():
    return jsonify({
        'gpu': get_gpu_metrics(),
        'system': get_system_metrics(),
        'memory_count': get_memory_count()
    })

@app.route('/api/memories/stats')
def memory_stats():
    count = get_memory_count()
    return jsonify({
        'total': count,
        'success': True
    })

@app.route('/api/memories/recent')
def memory_recent():
    limit = int(request.args.get('limit', 50))
    return jsonify({
        'success': True,
        'memories': get_recent_memories(limit)
    })

@app.route('/api/scripts')
def get_scripts():
    return jsonify({'scripts': WOLF_SCRIPTS})

@app.route('/scripts/state')
def script_state():
    slots = []
    for script in WOLF_SCRIPTS:
        slots.append({
            'name': script['name'], 'id': script['id'], 'category': script['category'],
            'isRunning': script['id'] in running_processes
        })
    while len(slots) < 32:
        slots.append({'name': None})
    return jsonify({'slots': slots})

@app.route('/scripts/models')
def get_models():
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')[1:]
            models = [l.split()[0] for l in lines if l.strip()]
            return jsonify({'models': models})
    except:
        pass
    return jsonify({'models': ['mistral:latest', 'llama3:latest', 'codellama:latest', 'qwen2.5:latest']})

@app.route('/scripts/run', methods=['POST'])
def run_script_by_slot():
    """Execute script by slot number - used by WolfLogicGrid"""
    data = request.get_json()
    slot = data.get('slot', 0)
    params = data.get('params', {})
    
    if slot >= len(WOLF_SCRIPTS):
        return jsonify({'ok': False, 'error': 'Invalid slot'})
    
    script = WOLF_SCRIPTS[slot]
    script_path = BASE_DIR / script['script']
    
    if not script_path.exists():
        return jsonify({'ok': False, 'error': f"Script not found: {script['script']}"})
    
    if script_path.suffix == '.py':
        cmd = ['python3', str(script_path)]
    elif script_path.suffix == '.sh':
        cmd = ['bash', str(script_path)]
    else:
        cmd = [str(script_path)]

    if params.get('model'):
        cmd.extend(['--model', params['model']])
    
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=str(script_path.parent))
        running_processes[script['id']] = {'process': process, 'started': datetime.now().isoformat(), 'name': script['name']}
        
        try:
            stdout, stderr = process.communicate(timeout=3)
            output = stdout or stderr or 'Script executed'
        except subprocess.TimeoutExpired:
            output = 'Running in background...'
        
        return jsonify({'ok': True, 'name': script['name'], 'output': output[:500]})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)})

@app.route('/api/execute', methods=['POST'])
def execute_script():
    """Execute script by ID - alternative endpoint"""
    data = request.get_json()
    script_id = data.get('script_id')
    args = data.get('args', [])
    
    script = next((s for s in WOLF_SCRIPTS if s['id'] == script_id), None)
    if not script:
        return jsonify({'success': False, 'error': 'Script not found'})
    
    script_path = BASE_DIR / script['script']
    if not script_path.exists():
        return jsonify({'success': False, 'error': f"File not found: {script_path}"})
    
    if script_path.suffix == '.py':
        cmd = ['python3', str(script_path)] + args
    elif script_path.suffix == '.sh':
        cmd = ['bash', str(script_path)] + args
    else:
        cmd = [str(script_path)] + args

    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=str(script_path.parent))
        running_processes[script_id] = {'process': process, 'started': datetime.now().isoformat(), 'name': script['name']}
        return jsonify({'success': True, 'message': f"{script['name']} started", 'script_id': script_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/stop/<script_id>', methods=['POST'])
def stop_script(script_id):
    if script_id not in running_processes:
        return jsonify({'success': False, 'error': 'Not running'})
    try:
        running_processes[script_id]['process'].terminate()
        del running_processes[script_id]
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/status/<script_id>')
def script_status(script_id):
    if script_id in running_processes:
        p = running_processes[script_id]['process']
        return jsonify({'status': 'running' if p.poll() is None else 'completed'})
    return jsonify({'status': 'idle'})

@app.route('/android-setup')
@app.route('/android-setup.html')
def android_setup():
    return send_from_directory(os.path.join(BASE_DIR, 'wolf-ui/public'), 'android-setup.html')

@app.route('/<path:path>')
def serve_static(path):
    if os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    host_port = os.environ.get('WOLF_HOST_PORT', '8084')
    frontend_host_port = os.environ.get('WOLF_FRONTEND_HOST_PORT', '8083')
    container_port = int(os.environ.get('WOLF_LOGIC_PORT', 2500))

    print("╔═══════════════════════════════════════════════════════════╗")
    print("║              🧠 COMPLEX LOGIC APP - Backend                  ║")
    print("╠═══════════════════════════════════════════════════════════╣")
    print(f"║  API Server:    http://localhost:{host_port} (container :{container_port})".ljust(61) + "║")
    print(f"║  Frontend:      http://localhost:{frontend_host_port}".ljust(61) + "║")
    print("╠═══════════════════════════════════════════════════════════╣")
    print("║  Endpoints:                                               ║")
    print("║    /api/gpu-stats     - GPU metrics                       ║")
    print("║    /api/system-stats  - CPU/RAM/Disk                      ║")
    print("║    /api/services      - Service status                    ║")
    print("║    /api/lcd-data      - All dashboard data                ║")
    print("║    /api/scripts       - Available scripts                 ║")
    print("║    /scripts/run       - Execute script by slot            ║")
    print("║    /api/execute       - Execute script by ID              ║")
    print("╚═══════════════════════════════════════════════════════════╝")

    app.run(host='0.0.0.0', port=container_port, debug=False, threaded=True)
