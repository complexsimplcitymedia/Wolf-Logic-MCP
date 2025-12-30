#!/usr/bin/env python3
"""
Infrastructure Benchmark Script - Workstation vs Cloud
Compares performance of both environments for migration validation
"""
import subprocess
import time
import json
import sys
from datetime import datetime
import psycopg2
import pymysql
import requests
from typing import Dict, Any

# Environment configs
WORKSTATION = {
    'name': 'Workstation',
    'ip': '100.110.82.181',
    'postgres_port': 5433,
    'mysql_port': 3307,
    'ollama_port': 11434,
}

CLOUD = {
    'name': 'Bookworm Cloud',
    'ip': '100.110.82.250',
    'postgres_port': 5432,
    'mysql_port': 3307,
    'ollama_port': 11434,
}

DB_PASSWORD = 'wolflogic2024'

def log(msg: str):
    """Print timestamped log message"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def benchmark_postgres(env: Dict[str, Any]) -> Dict[str, float]:
    """Benchmark PostgreSQL performance"""
    log(f"Benchmarking PostgreSQL on {env['name']}...")
    
    results = {}
    
    try:
        conn = psycopg2.connect(
            host=env['ip'],
            port=env['postgres_port'],
            database='wolf_logic',
            user='wolf',
            password=DB_PASSWORD
        )
        cursor = conn.cursor()
        
        # 1. Simple SELECT benchmark (1000 rows)
        start = time.time()
        cursor.execute("SELECT * FROM memories LIMIT 1000;")
        cursor.fetchall()
        results['select_1000_rows'] = time.time() - start
        
        # 2. COUNT query benchmark
        start = time.time()
        cursor.execute("SELECT COUNT(*) FROM memories;")
        cursor.fetchone()
        results['count_all'] = time.time() - start
        
        # 3. Complex JOIN benchmark
        start = time.time()
        cursor.execute("""
            SELECT m.content, m.namespace, COUNT(*) as freq
            FROM memories m
            WHERE m.created_at >= NOW() - INTERVAL '7 days'
            GROUP BY m.content, m.namespace
            LIMIT 100;
        """)
        cursor.fetchall()
        results['complex_join'] = time.time() - start
        
        # 4. INSERT benchmark (10 records)
        start = time.time()
        for i in range(10):
            cursor.execute("""
                INSERT INTO memories (user_id, content, namespace, memory_type)
                VALUES (%s, %s, %s, %s)
            """, ('benchmark_test', f'Benchmark insert {i}', 'benchmark', 'test'))
        conn.commit()
        results['insert_10_records'] = time.time() - start
        
        # Cleanup
        cursor.execute("DELETE FROM memories WHERE namespace = 'benchmark';")
        conn.commit()
        
        cursor.close()
        conn.close()
        
        log(f"  ✓ PostgreSQL benchmark complete: {results}")
        
    except Exception as e:
        log(f"  ✗ PostgreSQL benchmark failed: {e}")
        results['error'] = str(e)
    
    return results

def benchmark_mysql(env: Dict[str, Any]) -> Dict[str, float]:
    """Benchmark MySQL performance"""
    log(f"Benchmarking MySQL on {env['name']}...")
    
    results = {}
    
    try:
        conn = pymysql.connect(
            host=env['ip'],
            port=env['mysql_port'],
            user='root',
            password=DB_PASSWORD,
            database='wolf_logic_mysql'
        )
        cursor = conn.cursor()
        
        # 1. Create test table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS benchmark_test (
                id INT AUTO_INCREMENT PRIMARY KEY,
                data VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # 2. INSERT benchmark (100 records)
        start = time.time()
        for i in range(100):
            cursor.execute("INSERT INTO benchmark_test (data) VALUES (%s)", (f'test_data_{i}',))
        conn.commit()
        results['insert_100_records'] = time.time() - start
        
        # 3. SELECT benchmark
        start = time.time()
        cursor.execute("SELECT * FROM benchmark_test;")
        cursor.fetchall()
        results['select_all'] = time.time() - start
        
        # 4. UPDATE benchmark
        start = time.time()
        cursor.execute("UPDATE benchmark_test SET data = 'updated' WHERE id < 50;")
        conn.commit()
        results['update_50_records'] = time.time() - start
        
        # 5. DELETE benchmark
        start = time.time()
        cursor.execute("DELETE FROM benchmark_test;")
        conn.commit()
        results['delete_all'] = time.time() - start
        
        # Cleanup
        cursor.execute("DROP TABLE benchmark_test;")
        conn.commit()
        
        cursor.close()
        conn.close()
        
        log(f"  ✓ MySQL benchmark complete: {results}")
        
    except Exception as e:
        log(f"  ✗ MySQL benchmark failed: {e}")
        results['error'] = str(e)
    
    return results

def benchmark_ollama(env: Dict[str, Any]) -> Dict[str, float]:
    """Benchmark Ollama embedding generation"""
    log(f"Benchmarking Ollama on {env['name']}...")
    
    results = {}
    
    try:
        url = f"http://{env['ip']}:{env['ollama_port']}/api/embeddings"
        
        test_text = "This is a benchmark test for embedding generation performance."
        
        # Test with qwen3-embedding:4b (2560 dimensions)
        start = time.time()
        response = requests.post(url, json={
            'model': 'qwen3-embedding:4b',
            'prompt': test_text
        }, timeout=30)
        
        if response.status_code == 200:
            results['qwen3_embedding_single'] = time.time() - start
            
            # Batch test (10 embeddings)
            start = time.time()
            for i in range(10):
                requests.post(url, json={
                    'model': 'qwen3-embedding:4b',
                    'prompt': f"{test_text} {i}"
                }, timeout=30)
            results['qwen3_embedding_batch_10'] = time.time() - start
            
            log(f"  ✓ Ollama benchmark complete: {results}")
        else:
            results['error'] = f"HTTP {response.status_code}"
            log(f"  ✗ Ollama benchmark failed: HTTP {response.status_code}")
            
    except Exception as e:
        log(f"  ✗ Ollama benchmark failed: {e}")
        results['error'] = str(e)
    
    return results

def benchmark_disk_io(env: Dict[str, Any]) -> Dict[str, float]:
    """Benchmark disk I/O using dd"""
    log(f"Benchmarking Disk I/O on {env['name']}...")
    
    results = {}
    
    try:
        # Write test (1GB file)
        cmd = f"ssh -o StrictHostKeyChecking=no -i ~/.ssh/id_ed25519 {'thewolf@' + env['ip'] if env['ip'] == '100.110.82.250' else ''} dd if=/dev/zero of=/tmp/benchmark_write bs=1M count=1024 oflag=direct 2>&1 | grep -oP '\\d+\\.?\\d* MB/s'"
        
        if env['ip'] == '100.110.82.181':
            cmd = "dd if=/dev/zero of=/tmp/benchmark_write bs=1M count=1024 oflag=direct 2>&1 | grep -oP '\\d+\\.?\\d* MB/s'"
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        if result.stdout.strip():
            results['disk_write_speed_mbps'] = float(result.stdout.strip().split()[0])
        
        # Read test (1GB file)
        cmd_read = cmd.replace('if=/dev/zero of=/tmp/benchmark_write', 'if=/tmp/benchmark_write of=/dev/null').replace('oflag=direct', 'iflag=direct')
        
        result_read = subprocess.run(cmd_read, shell=True, capture_output=True, text=True, timeout=60)
        if result_read.stdout.strip():
            results['disk_read_speed_mbps'] = float(result_read.stdout.strip().split()[0])
        
        # Cleanup
        cleanup_cmd = f"ssh -i ~/.ssh/id_ed25519 thewolf@{env['ip']} rm -f /tmp/benchmark_write" if env['ip'] == '100.110.82.250' else "rm -f /tmp/benchmark_write"
        subprocess.run(cleanup_cmd, shell=True)
        
        log(f"  ✓ Disk I/O benchmark complete: {results}")
        
    except Exception as e:
        log(f"  ✗ Disk I/O benchmark failed: {e}")
        results['error'] = str(e)
    
    return results

def benchmark_network(source_env: Dict[str, Any], dest_env: Dict[str, Any]) -> Dict[str, float]:
    """Benchmark network throughput between environments"""
    log(f"Benchmarking Network: {source_env['name']} → {dest_env['name']}...")
    
    results = {}
    
    try:
        # Ping latency
        cmd = f"ping -c 10 {dest_env['ip']} | tail -1 | awk '{{print $4}}' | cut -d '/' -f 2"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.stdout.strip():
            results['ping_latency_ms'] = float(result.stdout.strip())
        
        log(f"  ✓ Network benchmark complete: {results}")
        
    except Exception as e:
        log(f"  ✗ Network benchmark failed: {e}")
        results['error'] = str(e)
    
    return results

def generate_comparison_report(workstation_results: Dict, cloud_results: Dict) -> str:
    """Generate comparison report"""
    
    report = f"""
{'='*80}
INFRASTRUCTURE BENCHMARK REPORT
Workstation (100.110.82.181) vs Bookworm Cloud (100.110.82.250)
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*80}

## POSTGRESQL PERFORMANCE

| Metric                  | Workstation      | Cloud            | Winner      |
|-------------------------|------------------|------------------|-------------|
"""
    
    # PostgreSQL comparison
    for metric in ['select_1000_rows', 'count_all', 'complex_join', 'insert_10_records']:
        ws_val = workstation_results['postgres'].get(metric, 'N/A')
        cl_val = cloud_results['postgres'].get(metric, 'N/A')
        
        if isinstance(ws_val, float) and isinstance(cl_val, float):
            winner = "Workstation" if ws_val < cl_val else "Cloud"
            diff_pct = abs(ws_val - cl_val) / min(ws_val, cl_val) * 100
            report += f"| {metric:23} | {ws_val:>14.4f}s | {cl_val:>14.4f}s | {winner:11} ({diff_pct:.1f}% faster) |\n"
        else:
            report += f"| {metric:23} | {str(ws_val):>14} | {str(cl_val):>14} | {'N/A':11} |\n"
    
    report += f"\n## MYSQL PERFORMANCE\n\n"
    report += "| Metric                  | Workstation      | Cloud            | Winner      |\n"
    report += "|-------------------------|------------------|------------------|-------------|\n"
    
    # MySQL comparison
    for metric in ['insert_100_records', 'select_all', 'update_50_records', 'delete_all']:
        ws_val = workstation_results['mysql'].get(metric, 'N/A')
        cl_val = cloud_results['mysql'].get(metric, 'N/A')
        
        if isinstance(ws_val, float) and isinstance(cl_val, float):
            winner = "Workstation" if ws_val < cl_val else "Cloud"
            diff_pct = abs(ws_val - cl_val) / min(ws_val, cl_val) * 100
            report += f"| {metric:23} | {ws_val:>14.4f}s | {cl_val:>14.4f}s | {winner:11} ({diff_pct:.1f}% faster) |\n"
        else:
            report += f"| {metric:23} | {str(ws_val):>14} | {str(cl_val):>14} | {'N/A':11} |\n"
    
    report += f"\n## OLLAMA EMBEDDING PERFORMANCE\n\n"
    report += "| Metric                  | Workstation      | Cloud            | Winner      |\n"
    report += "|-------------------------|------------------|------------------|-------------|\n"
    
    # Ollama comparison
    for metric in ['qwen3_embedding_single', 'qwen3_embedding_batch_10']:
        ws_val = workstation_results['ollama'].get(metric, 'N/A')
        cl_val = cloud_results['ollama'].get(metric, 'N/A')
        
        if isinstance(ws_val, float) and isinstance(cl_val, float):
            winner = "Workstation" if ws_val < cl_val else "Cloud"
            diff_pct = abs(ws_val - cl_val) / min(ws_val, cl_val) * 100
            report += f"| {metric:23} | {ws_val:>14.4f}s | {cl_val:>14.4f}s | {winner:11} ({diff_pct:.1f}% faster) |\n"
        else:
            report += f"| {metric:23} | {str(ws_val):>14} | {str(cl_val):>14} | {'N/A':11} |\n"
    
    report += f"\n## DISK I/O PERFORMANCE\n\n"
    report += "| Metric                  | Workstation      | Cloud            | Winner      |\n"
    report += "|-------------------------|------------------|------------------|-------------|\n"
    
    # Disk I/O comparison
    for metric in ['disk_write_speed_mbps', 'disk_read_speed_mbps']:
        ws_val = workstation_results['disk_io'].get(metric, 'N/A')
        cl_val = cloud_results['disk_io'].get(metric, 'N/A')
        
        if isinstance(ws_val, float) and isinstance(cl_val, float):
            winner = "Workstation" if ws_val > cl_val else "Cloud"  # Higher is better for speed
            diff_pct = abs(ws_val - cl_val) / min(ws_val, cl_val) * 100
            report += f"| {metric:23} | {ws_val:>12.2f} MB/s | {cl_val:>12.2f} MB/s | {winner:11} ({diff_pct:.1f}% faster) |\n"
        else:
            report += f"| {metric:23} | {str(ws_val):>14} | {str(cl_val):>14} | {'N/A':11} |\n"
    
    report += f"\n## NETWORK PERFORMANCE\n\n"
    ws_to_cloud = workstation_results.get('network_to_cloud', {})
    cloud_to_ws = cloud_results.get('network_to_workstation', {})
    
    report += f"Workstation → Cloud Latency: {ws_to_cloud.get('ping_latency_ms', 'N/A')} ms\n"
    report += f"Cloud → Workstation Latency: {cloud_to_ws.get('ping_latency_ms', 'N/A')} ms\n"
    
    report += f"\n{'='*80}\n"
    
    return report

def main():
    """Run full benchmark suite"""
    log("Starting Infrastructure Benchmark...")
    log("This will test PostgreSQL, MySQL, Ollama, Disk I/O, and Network on both environments")
    
    workstation_results = {
        'postgres': {},
        'mysql': {},
        'ollama': {},
        'disk_io': {},
        'network_to_cloud': {}
    }
    
    cloud_results = {
        'postgres': {},
        'mysql': {},
        'ollama': {},
        'disk_io': {},
        'network_to_workstation': {}
    }
    
    # Benchmark Workstation
    log("\n=== BENCHMARKING WORKSTATION ===\n")
    workstation_results['postgres'] = benchmark_postgres(WORKSTATION)
    workstation_results['mysql'] = benchmark_mysql(WORKSTATION)
    workstation_results['ollama'] = benchmark_ollama(WORKSTATION)
    workstation_results['disk_io'] = benchmark_disk_io(WORKSTATION)
    workstation_results['network_to_cloud'] = benchmark_network(WORKSTATION, CLOUD)
    
    # Benchmark Cloud
    log("\n=== BENCHMARKING BOOKWORM CLOUD ===\n")
    cloud_results['postgres'] = benchmark_postgres(CLOUD)
    cloud_results['mysql'] = benchmark_mysql(CLOUD)
    cloud_results['ollama'] = benchmark_ollama(CLOUD)
    cloud_results['disk_io'] = benchmark_disk_io(CLOUD)
    cloud_results['network_to_workstation'] = benchmark_network(CLOUD, WORKSTATION)
    
    # Generate report
    log("\n=== GENERATING COMPARISON REPORT ===\n")
    report = generate_comparison_report(workstation_results, cloud_results)
    
    # Save to file
    report_path = f"/mnt/Wolf-code/Wolf-Ai-Enterptises/docs/BENCHMARK_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(report)
    log(f"\nReport saved to: {report_path}")
    
    # Save raw JSON data
    json_path = report_path.replace('.md', '.json')
    with open(json_path, 'w') as f:
        json.dump({
            'workstation': workstation_results,
            'cloud': cloud_results,
            'timestamp': datetime.now().isoformat()
        }, f, indent=2)
    
    log(f"Raw data saved to: {json_path}")
    log("\n✓ Benchmark complete!")

if __name__ == "__main__":
    main()
