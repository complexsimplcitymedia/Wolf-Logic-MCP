"""
Complex Logic Control Center - GPU Metrics + Live Memory Dashboard
Backend: Port 4500
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_sock import Sock
import json
import time
import threading
import os
import psutil
import logging
from pathlib import Path
import glob as globlib

# PostgreSQL for memory count
import psycopg2

# Try to import LACT client for AMD GPU
try:
    from lact_client import LACTClient
    LACT_AVAILABLE = True
    lact_client = LACTClient()
except:
    LACT_AVAILABLE = False
    lact_client = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='control_center', template_folder='control_center')
CORS(app)
sock = Sock(app)

# PostgreSQL Librarian connection
PG_CONFIG = {
    'host': os.environ.get('PG_HOST', 'localhost'),
    'port': int(os.environ.get('PG_PORT', 5433)),
    'dbname': os.environ.get('PG_DB', 'wolf_logic'),
    'user': os.environ.get('PG_USER', 'wolf'),
    'password': os.environ.get('PG_PASS', 'wolflogic2024')
}


def get_memory_count():
    """Get live memory count from PostgreSQL librarian"""
    try:
        conn = psycopg2.connect(**PG_CONFIG)
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM memories")
            count = cur.fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        logger.error(f"PostgreSQL memory count error: {e}")
        return None


def get_memory_stats():
    """Get detailed memory statistics by namespace"""
    try:
        conn = psycopg2.connect(**PG_CONFIG)
        stats = {'total': 0, 'namespaces': {}}

        with conn.cursor() as cur:
            # Total count
            cur.execute("SELECT COUNT(*) FROM memories")
            stats['total'] = cur.fetchone()[0]

            # Count by namespace
            cur.execute("""
                SELECT namespace, COUNT(*)
                FROM memories
                GROUP BY namespace
                ORDER BY COUNT(*) DESC
            """)
            for row in cur.fetchall():
                stats['namespaces'][row[0] or 'default'] = row[1]

        conn.close()
        return stats
    except Exception as e:
        logger.error(f"PostgreSQL memory stats error: {e}")
        return {'total': 0, 'namespaces': {}, 'error': str(e)}


class MetricsCollector:
    def __init__(self):
        self.metrics_history = []
        self.max_history = 60
        self.running = False
        self.thread = None
        self.memory_count = 0

    def get_gpu_metrics(self):
        """Get AMD GPU metrics via LACT"""
        gpu_data = {}

        if LACT_AVAILABLE and lact_client:
            try:
                # Get device list first
                devices = lact_client.list_devices()
                if devices and len(devices) > 0:
                    device_id = devices[0]['id']
                    device_name = devices[0].get('name', 'AMD GPU')

                    # Get stats for device
                    stats = lact_client.get_device_stats(device_id)

                    if stats:
                        # VRAM (bytes to GB)
                        vram = stats.get('vram', {})
                        vram_used = vram.get('used', 0) / (1024**3)
                        vram_total = vram.get('total', 0) / (1024**3)

                        # Temps
                        temps = stats.get('temps', {})
                        temp_edge = temps.get('edge', {}).get('current', 0)
                        temp_junction = temps.get('junction', {}).get('current', 0)
                        temp_mem = temps.get('mem', {}).get('current', 0)

                        # Clocks
                        clocks = stats.get('clockspeed', {})
                        gpu_clock = clocks.get('gpu_clockspeed', 0)
                        mem_clock = clocks.get('vram_clockspeed', 0)

                        # Fan
                        fan = stats.get('fan', {})
                        fan_rpm = fan.get('speed_current', 0)
                        fan_max = fan.get('speed_max', 3000)
                        fan_percent = round((fan_rpm / fan_max * 100), 1) if fan_max > 0 else 0

                        # Power
                        power = stats.get('power', {})
                        power_watts = power.get('average', 0)

                        # Voltage
                        voltage = stats.get('voltage', {})
                        gpu_voltage = voltage.get('gpu', 0)

                        gpu_data = {
                            "name": device_name,
                            "vram_used_gb": round(vram_used, 2),
                            "vram_total_gb": round(vram_total, 2),
                            "vram_percent": round((vram_used / vram_total * 100), 1) if vram_total > 0 else 0,
                            "gpu_clock_mhz": gpu_clock,
                            "mem_clock_mhz": mem_clock,
                            "temp_edge": temp_edge,
                            "temp_junction": temp_junction,
                            "temp_memory": temp_mem,
                            "fan_percent": fan_percent,
                            "fan_rpm": fan_rpm,
                            "power_watts": power_watts,
                            "voltage_mv": gpu_voltage,
                            "gpu_usage": stats.get('busy_percent', 0),
                            "throttling": "Yes" if stats.get('throttle_info', {}) else "No"
                        }
            except Exception as e:
                logger.error(f"AMD LACT metrics error: {e}")
                gpu_data = {"error": str(e)}
        else:
            gpu_data = {"error": "LACT not available"}

        return gpu_data

    def get_system_metrics(self):
        """Get comprehensive system metrics"""
        cpu_freq = psutil.cpu_freq()

        # Get memory count
        mem_count = get_memory_count()
        if mem_count is not None:
            self.memory_count = mem_count

        metrics = {
            "timestamp": time.time(),
            "memories": self.memory_count,
            "cpu": {
                "percent": psutil.cpu_percent(interval=0.1),
                "cores": psutil.cpu_count(),
                "frequency_mhz": round(cpu_freq.current, 0) if cpu_freq else 0
            },
            "ram": {
                "total_gb": round(psutil.virtual_memory().total / 1024**3, 2),
                "used_gb": round(psutil.virtual_memory().used / 1024**3, 2),
                "percent": psutil.virtual_memory().percent
            },
            "gpu": self.get_gpu_metrics()
        }

        return metrics

    def collect_loop(self):
        """Background metrics collection"""
        while self.running:
            try:
                metrics = self.get_system_metrics()
                self.metrics_history.append(metrics)

                if len(self.metrics_history) > self.max_history:
                    self.metrics_history = self.metrics_history[-self.max_history:]

            except Exception as e:
                logger.error(f"Metrics collection error: {e}")

            time.sleep(2)

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.collect_loop, daemon=True)
            self.thread.start()
            logger.info("Metrics collection started")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)


metrics_collector = MetricsCollector()


# ============= API ROUTES =============

@app.route("/api/metrics", methods=["GET"])
def get_metrics():
    """Get current system metrics"""
    return jsonify(metrics_collector.get_system_metrics())


@app.route("/api/metrics/gpu", methods=["GET"])
def get_gpu_metrics():
    """Get GPU metrics only"""
    return jsonify(metrics_collector.get_gpu_metrics())


@app.route("/api/memories", methods=["GET"])
def get_memories():
    """Get memory count"""
    count = get_memory_count()
    return jsonify({"count": count})


@app.route("/api/memories/stats", methods=["GET"])
def get_memories_stats():
    """Get detailed memory statistics"""
    return jsonify(get_memory_stats())


@sock.route('/ws/metrics')
def metrics_websocket(ws):
    """WebSocket for real-time metrics streaming"""
    try:
        while True:
            metrics = metrics_collector.get_system_metrics()
            ws.send(json.dumps(metrics))
            time.sleep(2)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")


@app.route("/health", methods=["GET"])
def health():
    """Health check"""
    mem_count = get_memory_count()
    return jsonify({
        "status": "healthy",
        "service": "Complex Logic Control Center",
        "lact_available": LACT_AVAILABLE,
        "pg_connected": mem_count is not None,
        "memory_count": mem_count,
        "metrics_running": metrics_collector.running
    })


# ============= METRICS CHARTS =============

METRICS_CHARTS_DIR = Path("/mnt/Wolf-code/Wolf-Ai-Enterptises/metrics/charts")

@app.route("/api/charts", methods=["GET"])
def get_charts_list():
    """Get list of available chart images"""
    charts = []
    if METRICS_CHARTS_DIR.exists():
        for png in sorted(METRICS_CHARTS_DIR.glob("*.png"), key=os.path.getmtime, reverse=True):
            charts.append({
                "name": png.stem,
                "filename": png.name,
                "url": f"/charts/{png.name}"
            })
    return jsonify({"charts": charts})


@app.route("/charts/<path:filename>")
def serve_chart(filename):
    """Serve chart images"""
    return send_from_directory(str(METRICS_CHARTS_DIR), filename)


# ============= SCRIPT EXECUTION =============

SCRIPTS_BASE = Path("/mnt/Wolf-code/Wolf-Ai-Enterptises/writers")
MESSIAH_PYTHON = Path.home() / "anaconda3/envs/messiah/bin/python"

AVAILABLE_SCRIPTS = {
    "ingest": {
        "ingest_agent": {"path": "ingest/ingest_agent.py", "description": "Main file ingestion agent"},
        "ingest_api": {"path": "ingest/ingest_agent_api.py", "description": "Ingestion API wrapper"},
        "bulk_import": {"path": "ingest/bulk_import.py", "description": "Bulk data import"}
    },
    "analysis": {
        "youtube_analyst": {"path": "analysis/youtube_analyst.py", "description": "YouTube video coordinator"},
        "visual_agent": {"path": "analysis/visual_agent.py", "description": "Frame-by-frame visual analysis"},
        "audio_agent": {"path": "analysis/audio_agent.py", "description": "Audio mood/energy analysis"},
        "transcript_agent": {"path": "analysis/transcript_agent.py", "description": "Transcription extraction"}
    },
    "retrieval": {
        "librarian": {"path": "retrieval/librarian.py", "description": "Semantic memory search"},
        "librarian_fleet": {"path": "retrieval/librarian_fleet.py", "description": "Parallel memory processing"},
        "load_context": {"path": "retrieval/load_session_context.py", "description": "Load session context"},
        "rank_memories": {"path": "retrieval/rank_memories.py", "description": "Rank memories by relevance"}
    },
    "vectorization": {
        "process_verbatim": {"path": "vectorization/process_verbatim.py", "description": "Process verbatim transcripts"},
        "process_optimized": {"path": "vectorization/process_verbatim_optimized.py", "description": "Optimized parallel processing"}
    },
    "utilities": {
        "context_monitor": {"path": "utilities/context_monitor.py", "description": "Monitor Claude context usage"},
        "session_manager": {"path": "utilities/session_manager.py", "description": "Session lifecycle management"},
        "pg_to_neo4j": {"path": "utilities/postgres_to_neo4j_etl.py", "description": "PostgreSQL to Neo4j ETL"}
    }
}

# Track running processes
running_processes = {}

import subprocess

@app.route("/api/scripts", methods=["GET"])
def list_scripts():
    """List all available scripts by category"""
    return jsonify(AVAILABLE_SCRIPTS)


@app.route("/api/scripts/run", methods=["POST"])
def run_script():
    """Execute a script by category and name"""
    data = request.get_json()
    category = data.get("category")
    script_name = data.get("script")
    args = data.get("args", [])

    if not category or not script_name:
        return jsonify({"error": "Missing category or script name"}), 400

    if category not in AVAILABLE_SCRIPTS:
        return jsonify({"error": f"Unknown category: {category}"}), 404

    if script_name not in AVAILABLE_SCRIPTS[category]:
        return jsonify({"error": f"Unknown script: {script_name}"}), 404

    script_info = AVAILABLE_SCRIPTS[category][script_name]
    script_path = SCRIPTS_BASE / script_info["path"]

    if not script_path.exists():
        return jsonify({"error": f"Script not found: {script_path}"}), 404

    try:
        # Run script in background
        cmd = [str(MESSIAH_PYTHON), str(script_path)] + args
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(SCRIPTS_BASE)
        )

        process_id = f"{category}_{script_name}_{int(time.time())}"
        running_processes[process_id] = {
            "process": process,
            "script": script_name,
            "category": category,
            "started": time.time(),
            "pid": process.pid
        }

        logger.info(f"Started script: {script_path} (PID: {process.pid})")

        return jsonify({
            "status": "started",
            "process_id": process_id,
            "pid": process.pid,
            "script": script_name,
            "category": category
        })

    except Exception as e:
        logger.error(f"Script execution error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/scripts/status", methods=["GET"])
def scripts_status():
    """Get status of running scripts"""
    status = {}
    for proc_id, info in list(running_processes.items()):
        proc = info["process"]
        poll = proc.poll()
        status[proc_id] = {
            "script": info["script"],
            "category": info["category"],
            "pid": info["pid"],
            "running": poll is None,
            "return_code": poll,
            "elapsed": time.time() - info["started"]
        }
        # Clean up finished processes
        if poll is not None:
            del running_processes[proc_id]

    return jsonify(status)


@app.route("/api/scripts/stop", methods=["POST"])
def stop_script():
    """Stop a running script"""
    data = request.get_json()
    process_id = data.get("process_id")

    if not process_id or process_id not in running_processes:
        return jsonify({"error": "Process not found"}), 404

    try:
        proc = running_processes[process_id]["process"]
        proc.terminate()
        proc.wait(timeout=5)
        del running_processes[process_id]
        return jsonify({"status": "stopped", "process_id": process_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============= STATIC FILES =============

@app.route("/")
def index():
    return send_from_directory('control_center', 'index.html')


@app.route("/<path:path>")
def serve_static(path):
    try:
        return send_from_directory('control_center', path)
    except:
        return jsonify({"error": "File not found"}), 404


# ============= STARTUP =============

def startup():
    logger.info("Complex Logic Control Center Starting...")
    logger.info(f"PostgreSQL: {PG_CONFIG['host']}:{PG_CONFIG['port']}/{PG_CONFIG['dbname']}")
    logger.info(f"LACT Available: {LACT_AVAILABLE}")

    mem_count = get_memory_count()
    if mem_count:
        logger.info(f"Memory Count: {mem_count:,}")

    metrics_collector.start()
    port = int(os.environ.get('PORT', 4500))
    logger.info(f"Backend API: http://0.0.0.0:{port}")


if __name__ == "__main__":
    startup()
    port = int(os.environ.get('PORT', 4500))
    app.run(debug=False, port=port, host="0.0.0.0", threaded=True)
