#!/usr/bin/env python3
"""
Wolf System Baseline Check
Collects comprehensive system state for integrity monitoring
Run by: incept5/llama3.1-claude (candidate) vs Claude (reference)
Location: /mnt/Wolf-code/Wolf-Ai-Enterptises/security/
"""

import subprocess
import json
import datetime
import hashlib
import os
from pathlib import Path

def run_command(cmd, description):
    """Execute shell command and return output"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        return {
            "command": cmd,
            "description": description,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "timestamp": datetime.datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "command": cmd,
            "description": description,
            "error": str(e),
            "timestamp": datetime.datetime.now().isoformat()
        }

def collect_baseline():
    """Collect comprehensive system baseline"""

    baseline = {
        "collection_time": datetime.datetime.now().isoformat(),
        "hostname": subprocess.run("hostname", shell=True, capture_output=True, text=True).stdout.strip(),
        "checks": {}
    }

    # Filesystem checks
    baseline["checks"]["filesystems"] = run_command(
        "df -h | grep -E '(Filesystem|/dev/)'",
        "All mounted filesystems and usage"
    )

    # Docker container status
    baseline["checks"]["docker_containers"] = run_command(
        'docker ps --format "table {{.Names}}\\t{{.Image}}\\t{{.Status}}\\t{{.Ports}}"',
        "Running Docker containers"
    )

    # Docker volumes
    baseline["checks"]["docker_volumes"] = run_command(
        'docker volume ls --format "{{.Name}}"',
        "Docker volumes"
    )

    # System services
    baseline["checks"]["systemd_services"] = run_command(
        "systemctl list-units --type=service --state=running --no-pager | head -60",
        "Running systemd services"
    )

    # Network listening ports
    baseline["checks"]["network_listeners"] = run_command(
        "ss -tulpn | grep LISTEN",
        "All listening network endpoints"
    )

    # PostgreSQL status (wolf_logic)
    baseline["checks"]["postgres_wolf_logic"] = run_command(
        "PGPASSWORD=wolflogic2024 psql -h localhost -p 5433 -U wolf -d wolf_logic -c '\\dt' 2>&1",
        "PostgreSQL wolf_logic tables"
    )

    # PostgreSQL memory count
    baseline["checks"]["postgres_memory_count"] = run_command(
        "PGPASSWORD=wolflogic2024 psql -h localhost -p 5433 -U wolf -d wolf_logic -c 'SELECT COUNT(*) as total_memories FROM memories;' 2>&1",
        "Total memories in database"
    )

    # Neo4j node count (if accessible)
    baseline["checks"]["neo4j_nodes"] = run_command(
        'curl -s http://localhost:7474/db/neo4j/tx/commit -H "Content-Type: application/json" -d \'{"statements":[{"statement":"MATCH (n) RETURN count(n) as count"}]}\' 2>&1 | grep -o \'"count":[0-9]*\' | cut -d: -f2',
        "Neo4j total node count"
    )

    # Ollama models
    baseline["checks"]["ollama_models"] = run_command(
        "ollama list",
        "Available Ollama models"
    )

    # Critical directories
    baseline["checks"]["wolf_directories"] = run_command(
        "ls -la /mnt/ | tail -n +4",
        "Wolf mounted drives"
    )

    # Memory usage
    baseline["checks"]["memory_usage"] = run_command(
        "free -h",
        "System memory usage"
    )

    # Disk I/O
    baseline["checks"]["disk_io"] = run_command(
        "iostat -x 1 2 | tail -20",
        "Disk I/O statistics"
    )

    # Process count by user
    baseline["checks"]["process_counts"] = run_command(
        "ps aux | awk '{print $1}' | sort | uniq -c | sort -rn",
        "Process count by user"
    )

    # Tailscale status
    baseline["checks"]["tailscale"] = run_command(
        "tailscale status --json | jq -r '.Self.TailscaleIPs[0]' 2>&1",
        "Tailscale IP (this machine)"
    )

    # Generate checksum of entire baseline
    baseline_str = json.dumps(baseline, sort_keys=True)
    baseline["baseline_hash"] = hashlib.sha256(baseline_str.encode()).hexdigest()

    return baseline

def save_baseline(baseline, filename):
    """Save baseline to JSON file"""
    output_path = Path(filename)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(baseline, f, indent=2)

    print(f"Baseline saved to: {output_path}")
    print(f"Baseline hash: {baseline['baseline_hash']}")
    return output_path

def compare_baselines(baseline1_path, baseline2_path):
    """Compare two baseline snapshots"""
    with open(baseline1_path) as f1, open(baseline2_path) as f2:
        b1 = json.load(f1)
        b2 = json.load(f2)

    differences = []

    for check_name in b1["checks"]:
        if check_name not in b2["checks"]:
            differences.append(f"Missing check in baseline 2: {check_name}")
            continue

        c1 = b1["checks"][check_name]
        c2 = b2["checks"][check_name]

        if c1.get("stdout") != c2.get("stdout"):
            differences.append(f"DIFF in {check_name}")

    return differences

if __name__ == "__main__":
    print("=" * 60)
    print("WOLF SYSTEM BASELINE CHECK")
    print("=" * 60)

    # Activate messiah environment
    os.environ["PATH"] = f"/home/thewolfwalksalone/anaconda3/envs/messiah/bin:{os.environ['PATH']}"

    baseline = collect_baseline()

    # Save with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"/mnt/Wolf-code/Wolf-Ai-Enterptises/security/baselines/baseline_{timestamp}.json"

    save_baseline(baseline, output_file)

    print(f"\nHostname: {baseline['hostname']}")
    print(f"Collection time: {baseline['collection_time']}")
    print(f"Total checks: {len(baseline['checks'])}")
    print("\nBaseline collection complete.")
