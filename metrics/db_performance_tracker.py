#!/usr/bin/env python3
"""
Database Performance Tracker
Logs query performance metrics for PostgreSQL vs Neo4j comparison.
Tracks: query time, result count, memory usage, connection overhead.

Union Way: Measure everything. Numbers don't lie.
"""

import time
import json
import psycopg2
from neo4j import GraphDatabase
from datetime import datetime
from pathlib import Path

# Database configs
PG_CONFIG = {
    "host": "100.110.82.181",
    "port": 5433,
    "database": "wolf_logic",
    "user": "wolf",
    "password": "wolflogic2024"
}

NEO4J_CONFIG = {
    "uri": "bolt://100.110.82.181:7687",
    "user": "neo4j",
    "password": "neo4j"  # Update with actual password
}

# Metrics output
METRICS_DIR = Path("/mnt/Wolf-code/Wolf-Ai-Enterptises/metrics/data")
METRICS_DIR.mkdir(parents=True, exist_ok=True)


class DatabaseBenchmark:
    """Run same queries against both databases, track performance"""

    def __init__(self):
        self.metrics = []

    def benchmark_postgres(self, query: str, description: str):
        """Execute query on Postgres, track metrics"""
        start = time.time()

        try:
            conn = psycopg2.connect(**PG_CONFIG)
            with conn.cursor() as cur:
                cur.execute(query)
                results = cur.fetchall()
                row_count = len(results)
            conn.close()

            elapsed = time.time() - start

            return {
                "database": "PostgreSQL",
                "query": description,
                "sql": query,
                "duration_ms": round(elapsed * 1000, 2),
                "row_count": row_count,
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }

        except Exception as e:
            elapsed = time.time() - start
            return {
                "database": "PostgreSQL",
                "query": description,
                "sql": query,
                "duration_ms": round(elapsed * 1000, 2),
                "row_count": 0,
                "timestamp": datetime.now().isoformat(),
                "status": "error",
                "error": str(e)
            }

    def benchmark_neo4j(self, cypher: str, description: str):
        """Execute query on Neo4j, track metrics"""
        start = time.time()

        try:
            driver = GraphDatabase.driver(NEO4J_CONFIG["uri"],
                                         auth=(NEO4J_CONFIG["user"], NEO4J_CONFIG["password"]))

            with driver.session() as session:
                result = session.run(cypher)
                records = list(result)
                row_count = len(records)

            driver.close()
            elapsed = time.time() - start

            return {
                "database": "Neo4j",
                "query": description,
                "cypher": cypher,
                "duration_ms": round(elapsed * 1000, 2),
                "row_count": row_count,
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }

        except Exception as e:
            elapsed = time.time() - start
            return {
                "database": "Neo4j",
                "query": description,
                "cypher": cypher,
                "duration_ms": round(elapsed * 1000, 2),
                "row_count": 0,
                "timestamp": datetime.now().isoformat(),
                "status": "error",
                "error": str(e)
            }

    def run_comparison(self, pg_query: str, neo4j_query: str, description: str):
        """Run same query on both databases, compare"""
        print(f"\n{'=' * 60}")
        print(f"BENCHMARK: {description}")
        print(f"{'=' * 60}")

        # PostgreSQL
        pg_result = self.benchmark_postgres(pg_query, description)
        print(f"PostgreSQL: {pg_result['duration_ms']}ms | {pg_result['row_count']} rows | {pg_result['status']}")
        self.metrics.append(pg_result)

        # Neo4j
        neo4j_result = self.benchmark_neo4j(neo4j_query, description)
        print(f"Neo4j:      {neo4j_result['duration_ms']}ms | {neo4j_result['row_count']} rows | {neo4j_result['status']}")
        self.metrics.append(neo4j_result)

        # Winner
        if pg_result['status'] == 'success' and neo4j_result['status'] == 'success':
            winner = "PostgreSQL" if pg_result['duration_ms'] < neo4j_result['duration_ms'] else "Neo4j"
            speedup = max(pg_result['duration_ms'], neo4j_result['duration_ms']) / min(pg_result['duration_ms'], neo4j_result['duration_ms'])
            print(f"Winner: {winner} ({speedup:.2f}x faster)")

    def save_metrics(self):
        """Save metrics to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = METRICS_DIR / f"benchmark_{timestamp}.json"

        with open(output_file, 'w') as f:
            json.dump(self.metrics, f, indent=2)

        print(f"\n{'=' * 60}")
        print(f"Metrics saved to: {output_file}")
        print(f"Total benchmarks: {len(self.metrics)}")
        print(f"{'=' * 60}")

        return output_file


def run_standard_benchmarks():
    """Standard benchmark suite"""
    bench = DatabaseBenchmark()

    # 1. Count all memories
    bench.run_comparison(
        pg_query="SELECT COUNT(*) FROM memories",
        neo4j_query="MATCH (m:Memory) RETURN count(m) as count",
        description="Count all memories"
    )

    # 2. Get recent memories (limit 100)
    bench.run_comparison(
        pg_query="SELECT id, user_id, memory_type, created_at FROM memories ORDER BY created_at DESC LIMIT 100",
        neo4j_query="MATCH (m:Memory) RETURN m.id, m.user_id, m.memory_type, m.created_at ORDER BY m.created_at DESC LIMIT 100",
        description="Fetch 100 most recent memories"
    )

    # 3. Count by namespace
    bench.run_comparison(
        pg_query="SELECT namespace, COUNT(*) FROM memories GROUP BY namespace",
        neo4j_query="MATCH (m:Memory) RETURN m.namespace as namespace, count(m) as count",
        description="Count memories by namespace"
    )

    # 4. Find specific user's memories
    bench.run_comparison(
        pg_query="SELECT id, content FROM memories WHERE user_id = 'stenographer' LIMIT 50",
        neo4j_query="MATCH (m:Memory {user_id: 'stenographer'}) RETURN m.id, m.content LIMIT 50",
        description="Find stenographer's memories"
    )

    bench.save_metrics()
    return bench.metrics


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Database Performance Benchmarking')
    parser.add_argument('--standard', action='store_true', help='Run standard benchmark suite')
    parser.add_argument('--custom', nargs=2, metavar=('PG_QUERY', 'NEO4J_QUERY'), help='Custom query comparison')

    args = parser.parse_args()

    if args.standard:
        run_standard_benchmarks()
    elif args.custom:
        bench = DatabaseBenchmark()
        bench.run_comparison(args.custom[0], args.custom[1], "Custom query")
        bench.save_metrics()
    else:
        print("Usage:")
        print("  --standard: Run standard benchmark suite")
        print("  --custom 'PG_QUERY' 'NEO4J_QUERY': Custom comparison")
