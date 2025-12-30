"""
Complex Logic Memory Control Center - Enhanced Backend
Support for fully programmable script execution with absolute paths
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import os
import sys
import asyncio
import subprocess
import json
import logging
import uuid
import psutil
import tempfile
import shutil
from pathlib import Path
from contextlib import asynccontextmanager
import httpx

# GPU monitoring
try:
    import pynvml
    pynvml.nvmlInit()
    NVIDIA_AVAILABLE = True
except:
    NVIDIA_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
class Config:
    HOST = "0.0.0.0"
    PORT = int(os.getenv("PORT", "4500"))
    USER_ID = os.getenv("USER_ID", "thewolfwalksalone")

    # Memory APIs
    OPENMEMORY_API = os.getenv("OPENMEMORY_API", "http://100.110.82.181:8765")
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")

    # Execution settings
    SCRIPT_TIMEOUT = int(os.getenv("SCRIPT_TIMEOUT", "300"))
    MAX_OUTPUT_SIZE = int(os.getenv("MAX_OUTPUT_SIZE", "10485760"))  # 10MB
    ALLOW_SUDO = os.getenv("ALLOW_SUDO", "false").lower() == "true"

config = Config()

# System Monitor
class SystemMonitor:
    def __init__(self):
        self.metrics_history = {
            "cpu": [],
            "memory": [],
            "gpu": [],
            "memory_counts": {},
            "timestamps": []
        }
        self.max_history = 100

    async def get_gpu_metrics(self):
        """Get GPU metrics"""
        gpu_data = []

        if NVIDIA_AVAILABLE:
            try:
                device_count = pynvml.nvmlDeviceGetCount()
                for i in range(device_count):
                    handle = pynvml.nvmlDeviceGetHandleByIndex(i)

                    name = pynvml.nvmlDeviceGetName(handle).decode('utf-8')
                    mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                    util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                    temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)

                    try:
                        power = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000
                    except:
                        power = 0

                    gpu_data.append({
                        "index": i,
                        "name": name,
                        "memory_total": round(mem_info.total / 1024**3, 2),
                        "memory_used": round(mem_info.used / 1024**3, 2),
                        "memory_free": round(mem_info.free / 1024**3, 2),
                        "memory_percent": round((mem_info.used / mem_info.total) * 100, 1),
                        "gpu_utilization": util.gpu,
                        "memory_utilization": util.memory,
                        "temperature": temp,
                        "power": round(power, 1)
                    })
            except Exception as e:
                logger.error(f"Error getting GPU metrics: {e}")

        return gpu_data

    async def get_memory_counts(self):
        """Get memory counts from PostgreSQL and Neo4j"""
        counts = {
            "postgresql": 0,
            "neo4j": 0,
            "total": 0
        }

        # Query PostgreSQL via wolf-dashboard (3550)
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get("http://localhost:3550/api/memories/stats")
                if response.status_code == 200:
                    data = response.json()
                    counts["postgresql"] = data.get("total", 0)
        except Exception as e:
            logger.error(f"PostgreSQL count error: {e}")

        # Query Neo4j
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.post(
                    "http://localhost:7474/db/neo4j/tx/commit",
                    auth=("neo4j", "wolflogic2024"),
                    json={"statements": [{"statement": "MATCH (n:Memory) RETURN count(n) as count"}]}
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("results") and len(data["results"]) > 0:
                        result_data = data["results"][0].get("data", [])
                        if result_data:
                            counts["neo4j"] = result_data[0]["row"][0]
        except Exception as e:
            logger.error(f"Neo4j count error: {e}")

        counts["total"] = counts["postgresql"] + counts["neo4j"]
        return counts

    async def get_gpu_from_dashboard(self):
        """Get GPU metrics from wolf-dashboard (3550) which has LACT access"""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get("http://localhost:3550/api/metrics")
                if response.status_code == 200:
                    data = response.json()
                    return data.get("gpu", {})
        except:
            pass
        return {}

    async def get_system_metrics(self):
        """Get comprehensive system metrics"""
        return {
            "cpu": {
                "percent": psutil.cpu_percent(interval=0.1),
                "cores": psutil.cpu_count(),
                "frequency": psutil.cpu_freq().current if psutil.cpu_freq() else 0
            },
            "memory": {
                "total": round(psutil.virtual_memory().total / 1024**3, 2),
                "used": round(psutil.virtual_memory().used / 1024**3, 2),
                "available": round(psutil.virtual_memory().available / 1024**3, 2),
                "percent": psutil.virtual_memory().percent
            },
            "disk": {
                "total": round(psutil.disk_usage('/').total / 1024**3, 2),
                "used": round(psutil.disk_usage('/').used / 1024**3, 2),
                "free": round(psutil.disk_usage('/').free / 1024**3, 2),
                "percent": psutil.disk_usage('/').percent
            },
            "gpu": await self.get_gpu_from_dashboard(),
            "memory_counts": await self.get_memory_counts(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

monitor = SystemMonitor()

# Script Executor
class ScriptExecutor:
    def __init__(self):
        self.running_processes = {}

    async def execute_command(
        self,
        command: str,
        args: List[str] = None,
        cwd: str = None,
        env: str = None,
        timeout: int = None
    ):
        """Execute any command with absolute path"""

        # Parse environment variables
        env_dict = os.environ.copy()
        if env:
            for line in env.split('\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    env_dict[key.strip()] = value.strip()

        # Build full command
        full_command = command
        if args:
            full_command = f"{command} {' '.join(args)}"

        logger.info(f"Executing: {full_command}")
        if cwd:
            logger.info(f"Working directory: {cwd}")

        # Create process ID
        process_id = str(uuid.uuid4())

        try:
            # Execute command
            process = await asyncio.create_subprocess_shell(
                full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=env_dict
            )

            self.running_processes[process_id] = process

            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout or config.SCRIPT_TIMEOUT
                )
            except asyncio.TimeoutError:
                process.terminate()
                await asyncio.sleep(1)
                if process.returncode is None:
                    process.kill()
                raise TimeoutError(f"Command exceeded timeout of {timeout or config.SCRIPT_TIMEOUT} seconds")

            return {
                "success": process.returncode == 0,
                "returncode": process.returncode,
                "stdout": stdout.decode('utf-8', errors='replace') if stdout else "",
                "stderr": stderr.decode('utf-8', errors='replace') if stderr else "",
                "command": full_command,
                "process_id": process_id
            }

        except Exception as e:
            logger.error(f"Execution error: {e}")
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "command": full_command,
                "process_id": process_id
            }
        finally:
            if process_id in self.running_processes:
                del self.running_processes[process_id]

    async def execute_inline(
        self,
        code: str,
        cwd: str = None,
        env: str = None
    ):
        """Execute inline Python code"""

        # Create temporary file
        temp_dir = tempfile.mkdtemp(prefix="wolf_inline_")
        script_path = os.path.join(temp_dir, "inline_script.py")

        try:
            # Write code to file
            with open(script_path, 'w') as f:
                f.write(code)

            # Execute as Python script
            result = await self.execute_command(
                f"{sys.executable} {script_path}",
                cwd=cwd,
                env=env
            )

            return result

        finally:
            # Cleanup
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def stop_process(self, process_id: str):
        """Stop a running process"""
        if process_id in self.running_processes:
            process = self.running_processes[process_id]
            process.terminate()
            return True
        return False

executor = ScriptExecutor()

# WebSocket Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.monitoring_task = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

        if not self.monitoring_task:
            self.monitoring_task = asyncio.create_task(self.monitor_loop())

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        if not self.active_connections and self.monitoring_task:
            self.monitoring_task.cancel()
            self.monitoring_task = None

    async def broadcast_metrics(self, data: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except:
                disconnected.append(connection)

        for conn in disconnected:
            self.disconnect(conn)

    async def monitor_loop(self):
        while self.active_connections:
            try:
                metrics = await monitor.get_system_metrics()
                monitor.metrics_history["timestamps"].append(metrics["timestamp"])
                monitor.metrics_history["cpu"].append(metrics["cpu"]["percent"])
                monitor.metrics_history["memory"].append(metrics["memory"]["percent"])

                if metrics["gpu"] and isinstance(metrics["gpu"], dict) and "gpu_usage" in metrics["gpu"]:
                    monitor.metrics_history["gpu"].append(metrics["gpu"]["gpu_usage"])
                else:
                    monitor.metrics_history["gpu"].append(0)

                monitor.metrics_history["memory_counts"] = metrics["memory_counts"]

                # Limit history
                if len(monitor.metrics_history["timestamps"]) > monitor.max_history:
                    for key in ["timestamps", "cpu", "memory", "gpu"]:
                        monitor.metrics_history[key] = monitor.metrics_history[key][-monitor.max_history:]

                await self.broadcast_metrics({
                    "type": "metrics",
                    "data": metrics,
                    "history": monitor.metrics_history
                })

                await asyncio.sleep(30)  # Update every 30 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                await asyncio.sleep(5)

manager = ConnectionManager()

# FastAPI Application
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🧠 Complex Logic Memory Control Center starting...")
    logger.info(f"Listening on http://{config.HOST}:{config.PORT}")
    yield
    logger.info("Shutting down...")

app = FastAPI(
    title="Complex Logic Memory Control Center",
    description="Fully programmable Python execution dashboard",
    version="4.0.0",
    lifespan=lifespan
)

# Mount static files directory
static_dir = Path("static")
if not static_dir.exists():
    static_dir.mkdir(exist_ok=True)

if static_dir.exists():
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data Models
class CommandExecuteRequest(BaseModel):
    command: str
    args: Optional[List[str]] = []
    cwd: Optional[str] = None
    env: Optional[str] = None
    timeout: Optional[int] = None

class InlineExecuteRequest(BaseModel):
    code: str
    cwd: Optional[str] = None
    env: Optional[str] = None

# API Routes
@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve the programmable dashboard"""
    dashboard_path = Path("programmable_dashboard.html")
    if dashboard_path.exists():
        return HTMLResponse(content=dashboard_path.read_text())
    else:
        return HTMLResponse(content="<h1>Dashboard file not found. Please ensure programmable_dashboard.html is in the same directory.</h1>")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "connections": len(manager.active_connections),
        "running_processes": len(executor.running_processes)
    }

@app.get("/api/metrics")
async def get_metrics():
    """Get current system metrics"""
    metrics = await monitor.get_system_metrics()
    return {
        "current": metrics,
        "history": monitor.metrics_history
    }

@app.post("/api/execute/command")
async def execute_command(request: CommandExecuteRequest):
    """Execute any command with absolute path"""
    try:
        result = await executor.execute_command(
            request.command,
            request.args,
            request.cwd,
            request.env,
            request.timeout
        )
        return result
    except Exception as e:
        logger.error(f"Command execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/execute/inline")
async def execute_inline(request: InlineExecuteRequest):
    """Execute inline Python code"""
    try:
        result = await executor.execute_inline(
            request.code,
            request.cwd,
            request.env
        )
        return result
    except Exception as e:
        logger.error(f"Inline execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/metrics")
async def websocket_metrics(websocket: WebSocket):
    """WebSocket for real-time metrics"""
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/api/memory/detailed-stats")
async def get_detailed_memory_stats():
    """Get detailed vector storage statistics"""
    stats = {
        "postgresql": {
            "total": 0,
            "namespaces": [],
            "memory_types": []
        },
        "neo4j": {
            "total": 0,
            "nodes": {},
            "relationships": {}
        },
        "total": 0
    }

    # Get PostgreSQL stats
    try:
        # Total count
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:3550/api/memories/stats")
            if response.status_code == 200:
                data = response.json()
                stats["postgresql"]["total"] = data.get("total", 0)

        # Top namespaces (hardcoded from recent query - refresh periodically)
        stats["postgresql"]["namespaces"] = [
            {"name": "wolf_story", "count": 13316},
            {"name": "scripty", "count": 12321},
            {"name": "mem0_import", "count": 6576},
            {"name": "session_recovery", "count": 6229},
            {"name": "imported", "count": 3847},
            {"name": "ingested", "count": 2321},
            {"name": "wolf_hunt", "count": 1836},
            {"name": "stenographer", "count": 502}
        ]

        # Top memory types (hardcoded from recent query - refresh periodically)
        stats["postgresql"]["memory_types"] = [
            {"type": "autobiography", "count": 13316},
            {"type": "continuity_note", "count": 12321},
            {"type": "jsonl_record", "count": 4885},
            {"type": "learning", "count": 3867},
            {"type": "general", "count": 2351},
            {"type": "document", "count": 2321},
            {"type": "job_listing", "count": 1836},
            {"type": "task", "count": 1566}
        ]
    except Exception as e:
        logger.error(f"PostgreSQL stats error: {e}")

    # Get Neo4j stats
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Total memories
            response = await client.post(
                "http://localhost:7474/db/neo4j/tx/commit",
                auth=("neo4j", "wolflogic2024"),
                json={"statements": [{"statement": "MATCH (n:Memory) RETURN count(n) as count"}]}
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("results") and len(data["results"]) > 0:
                    result_data = data["results"][0].get("data", [])
                    if result_data:
                        stats["neo4j"]["total"] = result_data[0]["row"][0]

            # Node type counts
            response = await client.post(
                "http://localhost:7474/db/neo4j/tx/commit",
                auth=("neo4j", "wolflogic2024"),
                json={"statements": [{"statement": "MATCH (n) RETURN labels(n)[0] as label, count(n) as count ORDER BY count DESC"}]}
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("results") and len(data["results"]) > 0:
                    result_data = data["results"][0].get("data", [])
                    for row in result_data:
                        label = row["row"][0]
                        count = row["row"][1]
                        stats["neo4j"]["nodes"][label] = count

            # Relationship type counts
            response = await client.post(
                "http://localhost:7474/db/neo4j/tx/commit",
                auth=("neo4j", "wolflogic2024"),
                json={"statements": [{"statement": "MATCH ()-[r]->() RETURN type(r) as rel_type, count(r) as count ORDER BY count DESC"}]}
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("results") and len(data["results"]) > 0:
                    result_data = data["results"][0].get("data", [])
                    for row in result_data:
                        rel_type = row["row"][0]
                        count = row["row"][1]
                        stats["neo4j"]["relationships"][rel_type] = count
    except Exception as e:
        logger.error(f"Neo4j stats error: {e}")

    stats["total"] = stats["postgresql"]["total"] + stats["neo4j"]["total"]
    return stats

@app.post("/api/memory/add")
async def add_memory(content: str, metadata: Dict[str, Any] = {}):
    """Add a memory"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{config.OPENMEMORY_API}/memories",
            json={
                "text": content,
                "metadata": metadata,
                "user_id": config.USER_ID
            }
        )
        return response.json()

@app.post("/api/memory/search")
async def search_memory(query: str, limit: int = 10):
    """Search memories"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{config.OPENMEMORY_API}/search",
            json={
                "query": query,
                "user_id": config.USER_ID,
                "limit": limit
            }
        )
        return response.json()

@app.delete("/api/memory/clear")
async def clear_memory():
    """Clear all memories"""
    async with httpx.AsyncClient() as client:
        response = await client.delete(
            f"{config.OPENMEMORY_API}/memories",
            params={"user_id": config.USER_ID}
        )
        return response.json()


# ============= SCRIPT MANAGEMENT ENDPOINTS =============

# Config file path
CONFIG_FILE = Path("/app/config/button_layout.json")
SCRIPTS_FILE = Path("/mnt/Wolf-code/Wolf-Ai-Enterptises/api/dashboard_scripts.json")

def load_scripts():
    """Load available scripts from dashboard_scripts.json"""
    try:
        if SCRIPTS_FILE.exists():
            with open(SCRIPTS_FILE, 'r') as f:
                data = json.load(f)
                return data.get("memory_server_scripts", [])
        return []
    except Exception as e:
        logger.error(f"Error loading scripts: {e}")
        return []

def load_config():
    """Load button layout configuration"""
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        return {"layout": [], "categories": {}}
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {"layout": [], "categories": {}}

def save_config(config_data):
    """Save button layout configuration"""
    try:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config_data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving config: {e}")
        return False

@app.get("/api/scripts")
async def get_scripts():
    """Get list of available scripts"""
    scripts = load_scripts()
    return {"success": True, "scripts": scripts}

@app.get("/api/config")
async def get_config():
    """Get current button layout configuration"""
    config_data = load_config()
    return {"success": True, **config_data}

@app.post("/api/config")
async def update_config(config_data: Dict[str, Any]):
    """Save button layout configuration"""
    success = save_config(config_data)
    if success:
        return {"success": True, "message": "Configuration saved"}
    else:
        raise HTTPException(status_code=500, detail="Failed to save configuration")

@app.get("/api/config/reset")
async def reset_config():
    """Reset button layout to defaults"""
    try:
        if CONFIG_FILE.exists():
            CONFIG_FILE.unlink()
        return {"success": True, "message": "Configuration reset to defaults"}
    except Exception as e:
        logger.error(f"Error resetting config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/wolftv")
async def websocket_wolftv(websocket: WebSocket):
    """WebSocket for Wolf TV logs"""
    await websocket.accept()
    log_file = Path("/tmp/wolf_tv.log")
    
    try:
        # Create file if not exists
        if not log_file.exists():
            log_file.touch()
            
        with open(log_file, mode='r') as f:
            f.seek(0, 2) # Go to end
            
            while True:
                line = f.readline()
                if line:
                    await websocket.send_text(line)
                else:
                    await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        logger.info("Wolf TV client disconnected")
    except Exception as e:
        logger.error(f"Wolf TV stream error: {e}")
        try:
            await websocket.close()
        except:
            pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.HOST, port=config.PORT, reload=False)
