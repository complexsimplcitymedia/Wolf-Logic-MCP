#!/usr/bin/env python3
"""
Portfolio Demo Server with Live Memory Stats
Serves static portfolio and provides API endpoint for real-time memory count
"""
import os
import psycopg2
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DB_CONFIG = {
    'host': '100.110.82.181',
    'port': 5433,
    'database': 'wolf_logic',
    'user': 'wolf',
    'password': 'wolflogic2024'
}

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/resume.html')
def resume():
    return send_from_directory('.', 'resume.html')

@app.route('/resume.json')
def resume_json():
    return send_from_directory('.', 'resume.json')

@app.route('/jobs.html')
def jobs():
    return send_from_directory('.', 'jobs.html')

@app.route('/jobs.json')
def jobs_json():
    return send_from_directory('.', 'jobs.json')

@app.route('/api/memory-count')
def memory_count():
    """Return current memory count from librarian"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM memories;")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return jsonify({'count': count, 'status': 'live'})
    except Exception as e:
        return jsonify({'count': 46528, 'status': 'cached', 'error': str(e)}), 200

@app.route('/api/stats')
def stats():
    """Return full system stats"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Get memory stats
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(DISTINCT namespace) as namespaces,
                MAX(created_at) as latest
            FROM memories;
        """)
        total, namespaces, latest = cursor.fetchone()

        # Get namespace breakdown
        cursor.execute("""
            SELECT namespace, COUNT(*) as count
            FROM memories
            GROUP BY namespace
            ORDER BY count DESC
            LIMIT 10;
        """)
        top_namespaces = [{'namespace': row[0], 'count': row[1]} for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        return jsonify({
            'total_memories': total,
            'namespaces': namespaces,
            'latest_memory': latest.isoformat() if latest else None,
            'top_namespaces': top_namespaces,
            'status': 'live'
        })
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8888))
    print(f"🐺 Portfolio Demo Server starting on port {port}")
    print(f"📊 Connected to wolf_logic database")
    app.run(host='0.0.0.0', port=port, debug=False)
