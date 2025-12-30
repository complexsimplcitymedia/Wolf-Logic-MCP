#!/usr/bin/env python3
"""
Prometheus Metrics Exporter for Wolf AI Memory System
Exposes memory counts, ingestion rates, and system health
"""

from flask import Flask, Response
from prometheus_client import Counter, Gauge, generate_latest, REGISTRY
import psycopg2
import time

app = Flask(__name__)

# Database connection
DB_CONFIG = {
    'host': '100.110.82.181',
    'port': 5433,
    'database': 'wolf_logic',
    'user': 'wolf',
    'password': 'wolflogic2024'
}

# Prometheus metrics
total_memories = Gauge('wolf_ai_total_memories', 'Total number of memories in system')
memories_by_namespace = Gauge('wolf_ai_memories_by_namespace', 'Memories per namespace', ['namespace'])
memory_ingestion_rate = Counter('wolf_ai_memory_ingestion_total', 'Total memories ingested')
database_size_bytes = Gauge('wolf_ai_database_size_bytes', 'Total database size in bytes')
vector_dimensions = Gauge('wolf_ai_vector_dimensions', 'Embedding vector dimensions')

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def update_metrics():
    """Update all Prometheus metrics from database"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Total memories
        cur.execute("SELECT COUNT(*) FROM memories")
        total = cur.fetchone()[0]
        total_memories.set(total)

        # Memories by namespace
        cur.execute("""
            SELECT namespace, COUNT(*) as count
            FROM memories
            GROUP BY namespace
        """)
        for row in cur.fetchall():
            namespace, count = row
            memories_by_namespace.labels(namespace=namespace).set(count)

        # Database size
        cur.execute("""
            SELECT pg_database_size('wolf_logic')
        """)
        db_size = cur.fetchone()[0]
        database_size_bytes.set(db_size)

        # Vector dimensions (static)
        vector_dimensions.set(768)

        cur.close()
        conn.close()

    except Exception as e:
        print(f"Error updating metrics: {e}")

@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint"""
    update_metrics()
    return Response(generate_latest(REGISTRY), mimetype='text/plain')

@app.route('/health')
def health():
    """Health check endpoint"""
    return {'status': 'healthy', 'service': 'wolf-ai-metrics'}

if __name__ == '__main__':
    # Initial metrics update
    update_metrics()

    # Start server
    app.run(host='0.0.0.0', port=9091, debug=False)
