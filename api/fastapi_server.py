#!/usr/bin/env python3
"""
Wolf AI FastAPI Server - Control Dashboard Backend
Endpoints for all dashboard buttons with proper schemas
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import subprocess
import json
import psycopg2
import requests
from requests.auth import HTTPBasicAuth
from pathlib import Path
import asyncio
import time

app = FastAPI(
    title="Wolf AI Control API",
    description="Production Memory System Control Interface",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database config
PG_CONFIG = {
    "host": "100.110.82.181",
    "port": 5433,
    "database": "wolf_logic",
    "user": "wolf",
    "password": "wolflogic2024"
}

# Neo4j config (redundancy/load balancing)
NEO4J_SERVERS = [
    {
        "name": "mac_primary",
        "host": "100.110.82.245",  # Wolfbook Mac (Tailscale) - PRIMARY
        "http_port": 7474,
        "user": "neo4j",
        "password": "wolflogic2024",
        "database": "neo4j"
    },
    {
        "name": "local_backup",
        "host": "100.110.82.181",  # Local fallback
        "http_port": 7474,
        "user": "neo4j",
        "password": "wolflogic2024",
        "database": "neo4j"
    }
]

# Script paths
SCRIPTS = {
    "scripty_control": "/mnt/Wolf-code/Wolf-Ai-Enterptises/scripty/scripty_control.py",
    "dashboard_generator": "/mnt/Wolf-code/Wolf-Ai-Enterptises/metrics/visual_dashboard_api.py",
    "ingest_agent": "/mnt/Wolf-code/Wolf-Ai-Enterptises/writers/ingest_agent_api.py",
    "memory_counter": "/mnt/Wolf-code/Wolf-Ai-Enterptises/api/memory_counter.py",
    "session_logger": "/mnt/Wolf-code/Wolf-Ai-Enterptises/camera/session_logger.py",
    "rank_memories": "/mnt/Wolf-code/Wolf-Ai-Enterptises/writers/rank_memories.py",
    "youtube_analyst": "/mnt/Wolf-code/Wolf-Ai-Enterptises/writers/youtube_analyst.py"
}

PYTHON_BIN = str(Path.home() / "anaconda3/envs/messiah/bin/python")


# ============================================================================
# SCHEMAS / MODELS
# ============================================================================

class CommandResponse(BaseModel):
    """Standard command response"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class MemoryStats(BaseModel):
    """Memory system statistics"""
    total_memories: int
    today_count: int
    last_hour_count: int
    last_updated: Optional[str]
    top_namespace: Dict[str, Any]
    avg_per_day_7d: int
    timestamp: str


class ScriptyStatus(BaseModel):
    """Scripty daemon status"""
    running: bool
    pid: Optional[int] = None
    uptime_minutes: Optional[int] = None
    log_file: Optional[str] = None
    message: str
    status: str


class DashboardRefreshResponse(BaseModel):
    """Dashboard generation response"""
    success: bool
    message: str
    charts: Dict[str, str]
    html_dashboard: str
    charts_dir: str
    generated_at: str


class IngestRequest(BaseModel):
    """File ingestion request"""
    filepath: str = Field(..., description="Absolute path to file to ingest")


class IngestResponse(BaseModel):
    """File ingestion response"""
    success: bool
    message: str
    file: str
    file_type: str
    chunks_stored: Optional[int] = None
    pages_processed: Optional[int] = None


class YouTubeRequest(BaseModel):
    """YouTube analysis request"""
    url: str = Field(..., description="YouTube video URL")
    frame_interval: int = Field(default=15, description="Extract every Nth frame")
    store: bool = Field(default=True, description="Store analysis in database")


class ProcessStatusResponse(BaseModel):
    """Running process status"""
    process_name: str
    running: bool
    count: int
    pids: List[int] = []


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def execute_python_script(script_path: str, args: List[str] = None, json_output: bool = True) -> Dict[str, Any]:
    """Execute a Python script and return JSON result"""
    try:
        cmd = [PYTHON_BIN, script_path]
        if args:
            cmd.extend(args)
        if json_output and '--json' not in cmd:
            cmd.append('--json')

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        if json_output:
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "error": "Failed to parse JSON output",
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
        else:
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None
            }

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_db_connection():
    """Get PostgreSQL connection"""
    return psycopg2.connect(**PG_CONFIG)


def neo4j_query(cypher: str, params: Dict = None) -> Dict[str, Any]:
    """Execute Cypher query with automatic failover"""
    errors = []

    # Try each server in order (primary first, then fallbacks)
    for server in NEO4J_SERVERS:
        try:
            url = f"http://{server['host']}:{server['http_port']}/db/{server['database']}/tx/commit"

            payload = {
                "statements": [{
                    "statement": cypher,
                    "parameters": params or {}
                }]
            }

            response = requests.post(
                url,
                json=payload,
                auth=HTTPBasicAuth(server['user'], server['password']),
                headers={"Content-Type": "application/json"},
                timeout=10  # Short timeout for fast failover
            )

            response.raise_for_status()
            result = response.json()
            result["_server"] = server["name"]  # Track which server responded
            return result

        except requests.exceptions.RequestException as e:
            errors.append(f"{server['name']}: {str(e)}")
            continue  # Try next server

    # All servers failed
    return {
        "error": "All Neo4j servers unavailable",
        "details": errors,
        "success": False
    }


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/", response_model=Dict[str, str])
async def root():
    """API root"""
    return {
        "service": "Wolf AI Control API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs"
    }


@app.get("/api/health", response_model=Dict[str, Any])
async def health_check():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        conn.close()
        db_status = "healthy"
    except:
        db_status = "unhealthy"

    return {
        "status": "healthy",
        "database": db_status,
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# MEMORY STATISTICS
# ============================================================================

@app.get("/api/memory-stats", response_model=MemoryStats)
async def get_memory_stats():
    """Get comprehensive memory statistics"""
    result = execute_python_script(SCRIPTS["memory_counter"])

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to get stats"))

    return MemoryStats(**result)


@app.get("/api/memory/count", response_model=Dict[str, int])
async def get_memory_count():
    """Get simple memory count (fast)"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM memories")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()

        return {"total": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SCRIPTY CONTROL
# ============================================================================

@app.post("/api/scripty/start", response_model=ScriptyStatus)
async def start_scripty():
    """Start scripty daemon"""
    result = execute_python_script(SCRIPTS["scripty_control"], ["start"])

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("message"))

    return ScriptyStatus(**result)


@app.post("/api/scripty/stop", response_model=ScriptyStatus)
async def stop_scripty():
    """Stop scripty daemon"""
    result = execute_python_script(SCRIPTS["scripty_control"], ["stop"])
    return ScriptyStatus(**result)


@app.get("/api/scripty/status", response_model=ScriptyStatus)
async def get_scripty_status():
    """Get scripty daemon status"""
    result = execute_python_script(SCRIPTS["scripty_control"], ["status"])
    return ScriptyStatus(**result)


@app.post("/api/scripty/restart", response_model=ScriptyStatus)
async def restart_scripty():
    """Restart scripty daemon"""
    result = execute_python_script(SCRIPTS["scripty_control"], ["restart"])
    return ScriptyStatus(**result)


# ============================================================================
# DASHBOARD CONTROL
# ============================================================================

@app.post("/api/dashboard/refresh", response_model=DashboardRefreshResponse)
async def refresh_dashboard(days: int = 30):
    """Generate fresh dashboard charts"""
    result = execute_python_script(SCRIPTS["dashboard_generator"], ["--days", str(days)])

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))

    return DashboardRefreshResponse(**result)


@app.get("/api/dashboard/charts", response_model=Dict[str, str])
async def get_dashboard_charts():
    """Get paths to current dashboard charts"""
    charts_dir = Path("/mnt/Wolf-code/Wolf-Ai-Enterptises/metrics/charts")

    charts = {}
    for chart_type in ["timeline", "namespaces", "hourly"]:
        chart_files = sorted(charts_dir.glob(f"{chart_type}_*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
        if chart_files:
            charts[chart_type] = str(chart_files[0])

    return charts


# ============================================================================
# FILE INGESTION
# ============================================================================

@app.post("/api/ingest/file", response_model=IngestResponse)
async def ingest_file(request: IngestRequest):
    """Ingest a file into the memory system"""
    if not Path(request.filepath).exists():
        raise HTTPException(status_code=404, detail=f"File not found: {request.filepath}")

    result = execute_python_script(SCRIPTS["ingest_agent"], [request.filepath])

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))

    return IngestResponse(**result)


# ============================================================================
# SESSION LOGGER CONTROL
# ============================================================================

@app.post("/api/logger/start", response_model=CommandResponse)
async def start_session_logger(background_tasks: BackgroundTasks):
    """Start session logger (dailies)"""
    try:
        subprocess.Popen(
            [PYTHON_BIN, SCRIPTS["session_logger"]],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )

        return CommandResponse(
            success=True,
            message="Session logger started"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/logger/stop", response_model=CommandResponse)
async def stop_session_logger():
    """Stop session logger"""
    try:
        subprocess.run(["pkill", "-f", "session_logger.py"], check=False)
        return CommandResponse(
            success=True,
            message="Session logger stopped"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# UTILITIES
# ============================================================================

@app.post("/api/rank-memories", response_model=CommandResponse)
async def rank_memories():
    """Rank memories by importance"""
    result = execute_python_script(SCRIPTS["rank_memories"], json_output=False)

    return CommandResponse(
        success=result["success"],
        message="Memory ranking complete" if result["success"] else "Ranking failed",
        data={"output": result.get("output")}
    )


@app.post("/api/youtube/analyze", response_model=CommandResponse)
async def analyze_youtube(request: YouTubeRequest, background_tasks: BackgroundTasks):
    """Analyze YouTube video (runs in background)"""

    def run_analysis():
        args = [request.url, "--interval", str(request.frame_interval)]
        if request.store:
            args.append("--store")
        execute_python_script(SCRIPTS["youtube_analyst"], args, json_output=False)

    background_tasks.add_task(run_analysis)

    return CommandResponse(
        success=True,
        message=f"YouTube analysis queued: {request.url}",
        data={"url": request.url, "frame_interval": request.frame_interval}
    )


@app.get("/api/logs", response_model=Dict[str, str])
async def get_logs(lines: int = 50):
    """Get recent log entries"""
    try:
        result = subprocess.run(
            ["tail", "-n", str(lines), "/tmp/scripty.log"],
            capture_output=True,
            text=True
        )

        return {
            "logs": result.stdout,
            "lines": lines
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/system/status", response_model=List[ProcessStatusResponse])
async def get_system_status():
    """Get status of all running processes"""
    processes = {
        "memory_api": "memory_api.py",
        "scripty": "scripty.py",
        "session_logger": "session_logger.py"
    }

    status_list = []

    for name, process_name in processes.items():
        try:
            result = subprocess.run(
                ["pgrep", "-f", process_name],
                capture_output=True,
                text=True
            )

            pids = [int(pid) for pid in result.stdout.strip().split('\n') if pid]

            status_list.append(ProcessStatusResponse(
                process_name=name,
                running=len(pids) > 0,
                count=len(pids),
                pids=pids
            ))
        except:
            status_list.append(ProcessStatusResponse(
                process_name=name,
                running=False,
                count=0
            ))

    return status_list


# ============================================================================
# DATABASE QUERIES
# ============================================================================

@app.get("/api/namespaces", response_model=List[Dict[str, Any]])
async def get_namespaces():
    """Get all namespaces with counts"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT namespace, COUNT(*) as count,
                   MIN(created_at) as first_entry,
                   MAX(created_at) as last_entry
            FROM memories
            WHERE namespace IS NOT NULL
            GROUP BY namespace
            ORDER BY count DESC
        """)

        results = []
        for row in cur.fetchall():
            results.append({
                "namespace": row[0],
                "count": row[1],
                "first_entry": row[2].isoformat() if row[2] else None,
                "last_entry": row[3].isoformat() if row[3] else None
            })

        cur.close()
        conn.close()

        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# NEO4J GRAPH ENDPOINTS (with redundancy/failover)
# ============================================================================

@app.get("/api/neo4j/health", response_model=Dict[str, Any])
async def neo4j_health():
    """Check Neo4j server health and failover status"""
    health_status = []

    for server in NEO4J_SERVERS:
        try:
            url = f"http://{server['host']}:{server['http_port']}"
            response = requests.get(url, timeout=5)

            health_status.append({
                "server": server["name"],
                "host": server["host"],
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "reachable": True
            })
        except:
            health_status.append({
                "server": server["name"],
                "host": server["host"],
                "status": "unreachable",
                "reachable": False
            })

    return {
        "servers": health_status,
        "primary": NEO4J_SERVERS[0]["name"],
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/neo4j/stats", response_model=Dict[str, Any])
async def neo4j_stats():
    """Get Neo4j graph statistics"""
    cypher = """
    MATCH (n)
    WITH labels(n) AS nodeType, count(*) AS count
    RETURN {
        total_nodes: sum(count),
        node_types: collect({type: nodeType[0], count: count})
    } AS stats

    UNION ALL

    MATCH ()-[r]->()
    WITH type(r) AS relType, count(*) AS count
    RETURN {
        total_relationships: sum(count),
        relationship_types: collect({type: relType, count: count})
    } AS stats
    """

    result = neo4j_query(cypher)

    if result.get("success") == False:
        raise HTTPException(status_code=500, detail=result.get("error"))

    return {
        "stats": result,
        "server_used": result.get("_server"),
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/neo4j/query", response_model=Dict[str, Any])
async def execute_neo4j_query(cypher: str, params: Optional[Dict] = None):
    """Execute custom Cypher query"""
    if not cypher.strip().upper().startswith(("MATCH", "RETURN", "WITH", "UNWIND")):
        raise HTTPException(
            status_code=400,
            detail="Only read-only queries allowed (MATCH, RETURN, WITH, UNWIND)"
        )

    result = neo4j_query(cypher, params)

    if result.get("success") == False:
        raise HTTPException(status_code=500, detail=result.get("error"))

    return {
        "results": result,
        "server_used": result.get("_server"),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/neo4j/graph/memories", response_model=Dict[str, Any])
async def get_memory_graph(limit: int = 100):
    """Get memory nodes and relationships for visualization"""
    cypher = f"""
    MATCH (m:Memory)
    OPTIONAL MATCH (m)-[r]->(related)
    RETURN m, collect({{rel: r, node: related}}) AS connections
    LIMIT {limit}
    """

    result = neo4j_query(cypher)

    if result.get("success") == False:
        raise HTTPException(status_code=500, detail=result.get("error"))

    return {
        "graph_data": result,
        "server_used": result.get("_server"),
        "limit": limit,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/neo4j/graph/applications", response_model=Dict[str, Any])
async def get_applications_graph():
    """Get job application graph (Application -> Company relationships)"""
    cypher = """
    MATCH (a:Application)-[r:APPLIED_TO]->(c:Company)
    RETURN a, r, c
    ORDER BY a.date_applied DESC
    LIMIT 100
    """

    result = neo4j_query(cypher)

    if result.get("success") == False:
        raise HTTPException(status_code=500, detail=result.get("error"))

    return {
        "graph_data": result,
        "server_used": result.get("_server"),
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# PROMETHEUS METRICS
# ============================================================================

PROMETHEUS_URL = "http://localhost:9090"

@app.get("/api/prometheus/containers", response_model=Dict[str, Any])
async def get_container_metrics():
    """Get container metrics from Prometheus/cAdvisor"""
    try:
        # Query for container count (all containers)
        container_count_query = 'count(container_last_seen)'
        response = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={"query": container_count_query},
            timeout=5
        )

        container_count = 0
        if response.ok:
            data = response.json()
            if data.get("data", {}).get("result"):
                container_count = int(data["data"]["result"][0]["value"][1])

        # Query for total CPU usage across all containers
        cpu_query = 'sum(rate(container_cpu_usage_seconds_total{name!=""}[5m])) * 100'
        cpu_response = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={"query": cpu_query},
            timeout=5
        )

        cpu_usage = 0
        if cpu_response.ok:
            cpu_data = cpu_response.json()
            if cpu_data.get("data", {}).get("result"):
                cpu_usage = round(float(cpu_data["data"]["result"][0]["value"][1]), 1)

        # Query for total memory usage
        mem_query = 'sum(container_memory_usage_bytes{name!=""}) / 1024 / 1024 / 1024'
        mem_response = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={"query": mem_query},
            timeout=5
        )

        memory_usage_gb = 0
        if mem_response.ok:
            mem_data = mem_response.json()
            if mem_data.get("data", {}).get("result"):
                memory_usage_gb = round(float(mem_data["data"]["result"][0]["value"][1]), 2)

        return {
            "success": True,
            "containers": container_count,
            "cpu_usage_percent": cpu_usage,
            "memory_usage_gb": memory_usage_gb,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "containers": 0,
            "cpu_usage_percent": 0,
            "memory_usage_gb": 0
        }


@app.get("/api/system/uptime", response_model=Dict[str, Any])
async def get_system_uptime():
    """Get system uptime"""
    try:
        result = subprocess.run(
            ["uptime", "-p"],
            capture_output=True,
            text=True,
            timeout=2
        )

        uptime_str = result.stdout.strip()

        return {
            "success": True,
            "uptime": uptime_str,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "uptime": "Unknown",
            "error": str(e)
        }


# ============================================================================
# GPU METRICS (AMD RX 7900 XT)
# ============================================================================

@app.get("/api/gpu/stats", response_model=Dict[str, Any])
async def get_gpu_stats():
    """Get AMD GPU statistics from LACT daemon"""
    try:
        # Call LACT CLI to get GPU stats
        result = subprocess.run(
            ["flatpak", "run", "io.github.ilya_zlobintsev.LACT", "cli", "stats"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"LACT command failed: {result.stderr}")

        # Parse LACT output
        output = result.stdout
        gpu_data = {}

        # Parse each line
        for line in output.split('\n'):
            line = line.strip()

            # GPU Clockspeed
            if line.startswith("GPU Clockspeed:"):
                gpu_data["gpu_clock_mhz"] = int(line.split(":")[1].strip().replace(" MHz", ""))

            # VRAM Usage: "3374/20464 MiB"
            elif line.startswith("VRAM Usage:"):
                vram_str = line.split(":")[1].strip()  # "3374/20464 MiB"
                used, total = vram_str.replace(" MiB", "").split("/")
                vram_used_mib = int(used)
                vram_total_mib = int(total)

                gpu_data["vram_used_gb"] = round(vram_used_mib / 1024, 2)
                gpu_data["vram_total_gb"] = round(vram_total_mib / 1024, 2)
                gpu_data["vram_free_gb"] = round((vram_total_mib - vram_used_mib) / 1024, 2)
                gpu_data["vram_usage_percent"] = round((vram_used_mib / vram_total_mib) * 100, 1)

            # Temperatures: "vrmem: 55°C, junction: 59°C, vrsoc: 51°C, edge: 50°C"
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

            # GPU Voltage
            elif line.startswith("GPU Voltage:"):
                voltage_mv = int(line.split(":")[1].strip().replace(" mV", ""))
                gpu_data["gpu_voltage_mv"] = voltage_mv

            # Fan Speed: "23% (506 RPM)"
            elif line.startswith("Fan Speed:"):
                fan_str = line.split(":")[1].strip()  # "23% (506 RPM)"
                percent = int(fan_str.split("%")[0])
                rpm = int(fan_str.split("(")[1].split(" RPM")[0])
                gpu_data["fan_speed_percent"] = percent
                gpu_data["fan_speed_rpm"] = rpm

        # Calculate GPU usage from clock speed (approximate)
        # Max clock for RX 7900 XT is ~2500 MHz
        max_clock = 2500
        current_clock = gpu_data.get("gpu_clock_mhz", 0)
        gpu_data["gpu_usage_percent"] = round((current_clock / max_clock) * 100, 1)

        # Add power estimate based on voltage and clock (rough approximation)
        # RX 7900 XT TDP is 315W
        gpu_data["power_draw_watts"] = round((current_clock / max_clock) * 315, 1)

        return {
            "success": True,
            "gpu": "AMD Radeon RX 7900 XT",
            "data": gpu_data,
            "timestamp": datetime.now().isoformat()
        }

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="LACT command timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GPU metrics error: {str(e)}")


# ============================================================================
# WRITER SCRIPTS - INGEST
# ============================================================================

@app.post("/api/writers/ingest", response_model=CommandResponse)
async def run_ingest_agent(filepath: str):
    """Run ingest agent on file"""
    script_path = "/mnt/Wolf-code/Wolf-Ai-Enterptises/writers/ingest/ingest_agent.py"
    result = execute_python_script(script_path, [filepath])

    return CommandResponse(
        success=result.get("success", False),
        message=result.get("message", "Ingestion complete"),
        data=result
    )


@app.post("/api/writers/bulk-import", response_model=CommandResponse)
async def run_bulk_import(directory: str):
    """Run bulk import on directory"""
    script_path = "/mnt/Wolf-code/Wolf-Ai-Enterptises/writers/ingest/bulk_import.py"
    result = execute_python_script(script_path, [directory])

    return CommandResponse(
        success=result.get("success", False),
        message="Bulk import complete",
        data=result
    )


# ============================================================================
# WRITER SCRIPTS - ANALYSIS
# ============================================================================

@app.post("/api/writers/youtube-analyze", response_model=CommandResponse)
async def run_youtube_analyst(url: str, background_tasks: BackgroundTasks):
    """Analyze YouTube video (coordinator)"""
    script_path = "/mnt/Wolf-code/Wolf-Ai-Enterptises/writers/analysis/youtube_analyst.py"

    def run_analysis():
        execute_python_script(script_path, [url], json_output=False)

    background_tasks.add_task(run_analysis)

    return CommandResponse(
        success=True,
        message=f"YouTube analysis queued: {url}",
        data={"url": url}
    )


# ============================================================================
# WRITER SCRIPTS - RETRIEVAL
# ============================================================================

@app.post("/api/writers/librarian-search", response_model=CommandResponse)
async def run_librarian(query: str, limit: int = 10):
    """Semantic memory search via librarian"""
    script_path = "/mnt/Wolf-code/Wolf-Ai-Enterptises/writers/retrieval/librarian.py"
    result = execute_python_script(script_path, ["--query", query, "--limit", str(limit)])

    return CommandResponse(
        success=result.get("success", False),
        message="Memory search complete",
        data=result
    )


@app.post("/api/writers/load-context", response_model=CommandResponse)
async def run_load_context(namespace: Optional[str] = None):
    """Load session context"""
    script_path = "/mnt/Wolf-code/Wolf-Ai-Enterptises/writers/retrieval/load_session_context.py"
    args = ["--namespace", namespace] if namespace else []
    result = execute_python_script(script_path, args)

    return CommandResponse(
        success=result.get("success", False),
        message="Context loaded",
        data=result
    )


# ============================================================================
# WRITER SCRIPTS - VECTORIZATION
# ============================================================================

@app.post("/api/writers/vectorize", response_model=CommandResponse)
async def run_vectorization(optimized: bool = True):
    """Run vectorization process"""
    script_path = "/mnt/Wolf-code/Wolf-Ai-Enterptises/writers/vectorization/"
    script_path += "process_verbatim_optimized.py" if optimized else "process_verbatim.py"

    result = execute_python_script(script_path, json_output=False)

    return CommandResponse(
        success=result.get("success", False),
        message="Vectorization complete",
        data=result
    )


# ============================================================================
# WRITER SCRIPTS - UTILITIES
# ============================================================================

@app.post("/api/writers/pg-to-neo4j", response_model=CommandResponse)
async def run_pg_to_neo4j_etl(background_tasks: BackgroundTasks):
    """Run Postgres to Neo4j ETL"""
    script_path = "/mnt/Wolf-code/Wolf-Ai-Enterptises/writers/utilities/postgres_to_neo4j_etl.py"

    def run_etl():
        execute_python_script(script_path, json_output=False)

    background_tasks.add_task(run_etl)

    return CommandResponse(
        success=True,
        message="ETL pipeline queued",
        data={}
    )


@app.get("/api/writers/context-monitor", response_model=Dict[str, Any])
async def get_context_monitor():
    """Get current context usage"""
    script_path = "/mnt/Wolf-code/Wolf-Ai-Enterptises/writers/utilities/context_monitor.py"
    result = execute_python_script(script_path)

    return result


# ============================================================================
# OLLAMA CONTROL
# ============================================================================

@app.get("/api/ollama/status", response_model=Dict[str, Any])
async def get_ollama_status():
    """Check Ollama service status"""
    try:
        result = subprocess.run(
            ["systemctl", "is-active", "ollama"],
            capture_output=True,
            text=True
        )

        running = result.stdout.strip() == "active"

        return {
            "service": "ollama",
            "running": running,
            "status": result.stdout.strip(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ollama/models", response_model=Dict[str, Any])
async def list_ollama_models():
    """List available Ollama models"""
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=10
        )

        return {
            "success": result.returncode == 0,
            "models": result.stdout,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ollama/run", response_model=CommandResponse)
async def run_ollama_model(model: str, background_tasks: BackgroundTasks):
    """Start an Ollama model"""

    def start_model():
        subprocess.run(
            ["ollama", "run", model],
            capture_output=True,
            timeout=30
        )

    background_tasks.add_task(start_model)

    return CommandResponse(
        success=True,
        message=f"Starting Ollama model: {model}",
        data={"model": model}
    )


# ============================================================================
# WOLF UI COMPATIBILITY ENDPOINTS
# ============================================================================

@app.get("/api/scripts", response_model=Dict[str, Any])
async def get_scripts_list():
    """Get list of all available scripts for Wolf UI buttons"""
    scripts = [
        # INGEST
        {"id": 0, "name": "📥 Ingest File", "category": "Ingest", "endpoint": "/api/writers/ingest"},
        {"id": 1, "name": "📦 Bulk Import", "category": "Ingest", "endpoint": "/api/writers/bulk-import"},

        # ANALYSIS
        {"id": 2, "name": "🎬 YouTube Analyst", "category": "Analysis", "endpoint": "/api/writers/youtube-analyst"},
        {"id": 3, "name": "👁️ Visual Agent", "category": "Analysis", "endpoint": "/api/writers/visual-agent"},
        {"id": 4, "name": "🔊 Audio Agent", "category": "Analysis", "endpoint": "/api/writers/audio-agent"},
        {"id": 5, "name": "📝 Transcript Agent", "category": "Analysis", "endpoint": "/api/writers/transcript-agent"},

        # RETRIEVAL
        {"id": 6, "name": "📚 Librarian Search", "category": "Retrieval", "endpoint": "/api/writers/librarian-search"},
        {"id": 7, "name": "🚀 Librarian Fleet", "category": "Retrieval", "endpoint": "/api/writers/librarian-fleet"},
        {"id": 8, "name": "📖 Load Session Context", "category": "Retrieval", "endpoint": "/api/writers/load-context"},
        {"id": 9, "name": "🎯 Rank Memories", "category": "Retrieval", "endpoint": "/api/writers/rank-memories"},

        # VECTORIZATION
        {"id": 10, "name": "🧠 Process Verbatim", "category": "Vectorization", "endpoint": "/api/writers/vectorize"},
        {"id": 11, "name": "⚡ Vectorize (Optimized)", "category": "Vectorization", "endpoint": "/api/writers/vectorize-optimized"},

        # UTILITIES
        {"id": 12, "name": "⏱️ Context Monitor", "category": "Utilities", "endpoint": "/api/writers/context-monitor"},
        {"id": 13, "name": "📊 Session Manager", "category": "Utilities", "endpoint": "/api/writers/session-manager"},
        {"id": 14, "name": "🔄 Postgres → Neo4j ETL", "category": "Utilities", "endpoint": "/api/writers/etl"},

        # SYSTEM
        {"id": 15, "name": "📊 Memory Stats", "category": "System", "endpoint": "/api/memory-stats"},
        {"id": 16, "name": "🗄️ Neo4j Stats", "category": "System", "endpoint": "/api/neo4j/stats"},
        {"id": 17, "name": "🎮 GPU Monitor", "category": "System", "endpoint": "/api/gpu/stats"},
        {"id": 18, "name": "💾 Database Health", "category": "System", "endpoint": "/api/health"},
        {"id": 19, "name": "🔗 Neo4j Relationships", "category": "System", "endpoint": "/api/neo4j/graph/memories"},
        {"id": 20, "name": "📈 System Dashboard", "category": "System", "endpoint": "/api/system/status"},
    ]

    return {"scripts": scripts, "total": len(scripts)}


@app.post("/api/execute/{script_id}", response_model=CommandResponse)
async def execute_script(script_id: int, background_tasks: BackgroundTasks):
    """Execute a script by ID (Wolf UI compatibility)"""
    script_map = {
        0: lambda: requests.get("http://localhost:8000/api/ollama/status").json(),
        1: lambda: requests.post("http://localhost:8000/api/ollama/run", json={"model": "mistral"}).json(),
        2: lambda: requests.post("http://localhost:8000/api/ollama/run", json={"model": "nomic-embed-text:v1.5"}).json(),
        5: lambda: requests.get("http://localhost:8000/api/memory-count").json(),
        6: lambda: requests.post("http://localhost:8000/api/writers/librarian-search", json={"query": "recent"}).json(),
        9: lambda: requests.get("http://localhost:8000/api/system/status").json(),
        15: lambda: requests.post("http://localhost:8000/api/writers/vectorize").json(),
        16: lambda: requests.get("http://localhost:8000/api/neo4j/stats").json(),
    }

    if script_id in script_map:
        try:
            result = script_map[script_id]()
            return CommandResponse(
                success=True,
                message=f"Script {script_id} executed",
                data=result
            )
        except Exception as e:
            return CommandResponse(
                success=False,
                message=f"Script {script_id} failed: {str(e)}",
                data={}
            )
    else:
        return CommandResponse(
            success=False,
            message=f"Script {script_id} not implemented yet",
            data={}
        )


@app.get("/api/status/{script_id}", response_model=Dict[str, Any])
async def get_script_status(script_id: int):
    """Get script execution status (Wolf UI compatibility)"""
    return {
        "script_id": script_id,
        "status": "ready",
        "last_run": None,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/config", response_model=Dict[str, Any])
async def get_config():
    """Get Wolf UI configuration"""
    return {
        "layout": list(range(21)),  # All 21 buttons
        "categories": {},
        "theme": "dark"
    }


@app.post("/api/config", response_model=Dict[str, Any])
async def save_config(layout: List[int] = None, categories: Dict = None):
    """Save Wolf UI configuration"""
    return {
        "success": True,
        "message": "Configuration saved"
    }


@app.get("/api/activity/stream")
async def activity_stream():
    """Server-Sent Events endpoint for live activity feed"""

    async def event_generator():
        last_memory_count = 0
        last_gpu_check = 0

        while True:
            try:
                current_time = time.time()
                events = []

                # Check memory count changes every 10 seconds
                if current_time - last_memory_count > 10:
                    try:
                        conn = psycopg2.connect(**PG_CONFIG)
                        cursor = conn.cursor()
                        cursor.execute("SELECT COUNT(*) FROM memories")
                        count = cursor.fetchone()[0]
                        cursor.close()
                        conn.close()

                        events.append({
                            "type": "info",
                            "message": f"Memory database: {count:,} vectors indexed"
                        })
                        last_memory_count = current_time
                    except Exception as e:
                        pass

                # Check GPU status every 15 seconds
                if current_time - last_gpu_check > 15:
                    try:
                        with open("/sys/class/drm/card0/device/gpu_busy_percent", "r") as f:
                            gpu_usage = int(f.read().strip())

                        if gpu_usage > 80:
                            events.append({
                                "type": "warning",
                                "message": f"GPU usage high: {gpu_usage}%"
                            })
                        elif gpu_usage > 50:
                            events.append({
                                "type": "info",
                                "message": f"GPU active: {gpu_usage}%"
                            })

                        last_gpu_check = current_time
                    except Exception as e:
                        pass

                # Send heartbeat if no events
                if not events:
                    events.append({
                        "type": "heartbeat",
                        "message": "System monitoring active"
                    })

                # Send all events
                for event in events:
                    yield f"data: {json.dumps(event)}\n\n"

                await asyncio.sleep(5)

            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
                await asyncio.sleep(5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "fastapi_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
