#!/usr/bin/env python3
"""
Performance Visualization Dashboard
Generates charts and reports from benchmark data.
Visual brain = visual metrics.

Union Way: Show the numbers. Make them impossible to ignore.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

METRICS_DIR = Path("/mnt/Wolf-code/Wolf-Ai-Enterptises/metrics/data")
REPORTS_DIR = Path("/mnt/Wolf-code/Wolf-Ai-Enterptises/metrics/reports")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def load_latest_metrics():
    """Load most recent benchmark data"""
    benchmark_files = list(METRICS_DIR.glob("benchmark_*.json"))
    if not benchmark_files:
        return None

    latest = max(benchmark_files, key=lambda p: p.stat().st_mtime)

    with open(latest, 'r') as f:
        return json.load(f)


def generate_text_report(metrics):
    """Generate text-based performance report"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    report = []
    report.append("=" * 80)
    report.append("DATABASE PERFORMANCE REPORT")
    report.append("=" * 80)
    report.append(f"Generated: {timestamp}")
    report.append(f"Total Benchmarks: {len(metrics)}")
    report.append("")

    # Group by query description
    queries = {}
    for m in metrics:
        query = m.get('query', 'Unknown')
        if query not in queries:
            queries[query] = {'pg': None, 'neo4j': None}

        if m['database'] == 'PostgreSQL':
            queries[query]['pg'] = m
        else:
            queries[query]['neo4j'] = m

    # Results table
    report.append(f"{'Query':<40} | {'PostgreSQL':<15} | {'Neo4j':<15} | {'Winner':<15}")
    report.append("-" * 80)

    pg_wins = 0
    neo4j_wins = 0

    for query, data in queries.items():
        pg = data.get('pg')
        neo4j = data.get('neo4j')

        if pg and neo4j and pg['status'] == 'success' and neo4j['status'] == 'success':
            pg_time = pg['duration_ms']
            neo4j_time = neo4j['duration_ms']

            if pg_time < neo4j_time:
                winner = "PostgreSQL"
                speedup = f"{neo4j_time / pg_time:.2f}x"
                pg_wins += 1
            else:
                winner = "Neo4j"
                speedup = f"{pg_time / neo4j_time:.2f}x"
                neo4j_wins += 1

            report.append(f"{query[:38]:<40} | {pg_time:>12}ms | {neo4j_time:>12}ms | {winner} ({speedup})")
        else:
            report.append(f"{query[:38]:<40} | {'ERROR':<15} | {'ERROR':<15} | N/A")

    report.append("-" * 80)
    report.append("")

    # Summary statistics
    report.append("SUMMARY:")
    report.append(f"  PostgreSQL wins: {pg_wins}")
    report.append(f"  Neo4j wins:      {neo4j_wins}")

    if pg_wins + neo4j_wins > 0:
        pg_pct = (pg_wins / (pg_wins + neo4j_wins)) * 100
        neo4j_pct = (neo4j_wins / (pg_wins + neo4j_wins)) * 100
        report.append(f"  PostgreSQL:      {pg_pct:.1f}%")
        report.append(f"  Neo4j:           {neo4j_pct:.1f}%")

    report.append("")

    # Average query times
    pg_times = [m['duration_ms'] for m in metrics if m['database'] == 'PostgreSQL' and m['status'] == 'success']
    neo4j_times = [m['duration_ms'] for m in metrics if m['database'] == 'Neo4j' and m['status'] == 'success']

    if pg_times:
        report.append(f"PostgreSQL avg query time: {sum(pg_times) / len(pg_times):.2f}ms")
    if neo4j_times:
        report.append(f"Neo4j avg query time:      {sum(neo4j_times) / len(neo4j_times):.2f}ms")

    report.append("")
    report.append("=" * 80)

    return "\n".join(report)


def generate_ascii_chart(metrics):
    """Generate ASCII bar chart for visual comparison"""
    queries = {}
    for m in metrics:
        query = m.get('query', 'Unknown')
        if query not in queries:
            queries[query] = {'pg': None, 'neo4j': None}

        if m['database'] == 'PostgreSQL':
            queries[query]['pg'] = m['duration_ms'] if m['status'] == 'success' else 0
        else:
            queries[query]['neo4j'] = m['duration_ms'] if m['status'] == 'success' else 0

    chart = []
    chart.append("\nPERFORMANCE CHART (lower = faster):")
    chart.append("")

    max_time = max([max(q.get('pg', 0), q.get('neo4j', 0)) for q in queries.values()])
    scale = 50  # Chart width

    for query, times in queries.items():
        pg_time = times.get('pg', 0)
        neo4j_time = times.get('neo4j', 0)

        chart.append(f"{query[:30]:<30}")

        # PostgreSQL bar
        if pg_time > 0:
            bar_len = int((pg_time / max_time) * scale) if max_time > 0 else 0
            chart.append(f"  PG:    [{'█' * bar_len}{' ' * (scale - bar_len)}] {pg_time:.2f}ms")
        else:
            chart.append(f"  PG:    ERROR")

        # Neo4j bar
        if neo4j_time > 0:
            bar_len = int((neo4j_time / max_time) * scale) if max_time > 0 else 0
            chart.append(f"  Neo4j: [{'█' * bar_len}{' ' * (scale - bar_len)}] {neo4j_time:.2f}ms")
        else:
            chart.append(f"  Neo4j: ERROR")

        chart.append("")

    return "\n".join(chart)


def save_report(content):
    """Save report to file and display"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = REPORTS_DIR / f"performance_report_{timestamp}.txt"

    with open(report_file, 'w') as f:
        f.write(content)

    print(content)
    print(f"\nReport saved to: {report_file}")

    return report_file


if __name__ == "__main__":
    metrics = load_latest_metrics()

    if not metrics:
        print("No benchmark data found. Run db_performance_tracker.py first.")
        sys.exit(1)

    # Generate text report
    report = generate_text_report(metrics)

    # Add ASCII chart
    chart = generate_ascii_chart(metrics)
    full_report = report + "\n" + chart

    # Save and display
    save_report(full_report)
