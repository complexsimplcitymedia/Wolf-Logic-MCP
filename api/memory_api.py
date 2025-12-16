#!/usr/bin/env python3
"""
Wolf AI Memory System - Public API
Demonstrates production-ready AI memory architecture with semantic search
"""

from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
import psycopg2
import psycopg2.extras
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'port': 5436,
    'database': 'wolf_logic',
    'user': 'wolf',
    'password': 'wolflogic2024'
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

@app.route('/')
def index():
    """Landing page with query interface"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/dashboard')
def dashboard():
    """Full control center dashboard"""
    with open('/mnt/Wolf-code/Wolf-Ai-Enterptises/api/dashboard.html', 'r') as f:
        return f.read()

@app.route('/api/stats')
def stats():
    """Get system statistics"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Total memories
    cur.execute("SELECT COUNT(*) as total FROM memories")
    total = cur.fetchone()['total']

    # By namespace
    cur.execute("""
        SELECT namespace, COUNT(*) as count, MAX(created_at) as last_updated
        FROM memories
        GROUP BY namespace
        ORDER BY count DESC
    """)
    namespaces = cur.fetchall()

    # Recent activity
    cur.execute("""
        SELECT namespace, created_at
        FROM memories
        ORDER BY created_at DESC
        LIMIT 10
    """)
    recent = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify({
        'total_memories': total,
        'namespaces': [dict(n) for n in namespaces],
        'recent_activity': [dict(r) for r in recent],
        'system': 'PostgreSQL 16 + pgai + nomic-embed-text:v1.5',
        'vector_dimensions': 768
    })

@app.route('/api/search')
def search():
    """Semantic search across memories"""
    query = request.args.get('q', '')
    namespace = request.args.get('namespace', None)
    limit = int(request.args.get('limit', 10))

    if not query:
        return jsonify({'error': 'Query parameter required'}), 400

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Text search (semantic search would require embedding the query)
    sql = """
        SELECT id, namespace, content, created_at,
               ts_rank(to_tsvector('english', content), plainto_tsquery('english', %s)) as relevance
        FROM memories
        WHERE to_tsvector('english', content) @@ plainto_tsquery('english', %s)
    """
    params = [query, query]

    if namespace:
        sql += " AND namespace = %s"
        params.append(namespace)

    sql += " ORDER BY relevance DESC LIMIT %s"
    params.append(limit)

    cur.execute(sql, params)
    results = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify({
        'query': query,
        'namespace': namespace,
        'results': [dict(r) for r in results],
        'count': len(results)
    })

@app.route('/api/namespaces')
def namespaces():
    """List all available namespaces"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("""
        SELECT namespace, COUNT(*) as count,
               MIN(created_at) as first_entry,
               MAX(created_at) as last_entry
        FROM memories
        GROUP BY namespace
        ORDER BY count DESC
    """)
    results = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify({
        'namespaces': [dict(r) for r in results]
    })

@app.route('/api/memory/<int:memory_id>')
def get_memory(memory_id):
    """Get specific memory by ID"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("""
        SELECT id, user_id, content, metadata, memory_type, namespace, created_at, updated_at
        FROM memories
        WHERE id = %s
    """, (memory_id,))

    result = cur.fetchone()

    cur.close()
    conn.close()

    if not result:
        return jsonify({'error': 'Memory not found'}), 404

    return jsonify(dict(result))

# HTML Template for UI
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wolf AI Memory System - Live Demo</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Courier New', monospace;
            background: #0a0a0a;
            color: #00ff00;
            padding: 20px;
            line-height: 1.6;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            text-shadow: 0 0 10px #00ff00;
        }
        .subtitle {
            color: #00aa00;
            margin-bottom: 30px;
            font-size: 1.1rem;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: #111;
            border: 2px solid #00ff00;
            padding: 20px;
            border-radius: 5px;
        }
        .stat-value {
            font-size: 2rem;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .stat-label { color: #00aa00; }
        .search-box {
            background: #111;
            border: 2px solid #00ff00;
            padding: 30px;
            margin-bottom: 30px;
            border-radius: 5px;
        }
        input, select {
            background: #0a0a0a;
            border: 1px solid #00ff00;
            color: #00ff00;
            padding: 12px;
            font-size: 1rem;
            font-family: 'Courier New', monospace;
            width: 100%;
            margin-bottom: 15px;
        }
        button {
            background: #00ff00;
            color: #0a0a0a;
            border: none;
            padding: 12px 30px;
            font-size: 1rem;
            font-weight: bold;
            cursor: pointer;
            font-family: 'Courier New', monospace;
        }
        button:hover { background: #00aa00; }
        .results {
            background: #111;
            border: 2px solid #00ff00;
            padding: 20px;
            border-radius: 5px;
            display: none;
        }
        .result-item {
            border-bottom: 1px solid #003300;
            padding: 15px 0;
        }
        .result-item:last-child { border-bottom: none; }
        .namespace-badge {
            background: #003300;
            padding: 3px 10px;
            border-radius: 3px;
            font-size: 0.8rem;
            margin-right: 10px;
        }
        .loading { display: none; color: #00aa00; }
        .api-info {
            background: #111;
            border: 2px solid #00ff00;
            padding: 20px;
            margin-top: 30px;
            border-radius: 5px;
        }
        code {
            background: #0a0a0a;
            padding: 2px 6px;
            border-radius: 3px;
        }
        pre {
            background: #0a0a0a;
            padding: 15px;
            overflow-x: auto;
            margin: 10px 0;
            border-radius: 3px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>⚡ WOLF AI MEMORY SYSTEM</h1>
        <div class="subtitle">Production-Ready AI Memory Architecture | PostgreSQL + pgai + Vector Embeddings</div>

        <div class="stats" id="stats">
            <div class="stat-card">
                <div class="stat-value" id="total">...</div>
                <div class="stat-label">Total Memories</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="namespaces">...</div>
                <div class="stat-label">Namespaces</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">768</div>
                <div class="stat-label">Vector Dimensions</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">nomic-v1.5</div>
                <div class="stat-label">Embedding Model</div>
            </div>
        </div>

        <div class="search-box">
            <h2>🔍 Search Memories</h2>
            <input type="text" id="searchQuery" placeholder="Enter search query..." />
            <select id="namespaceFilter">
                <option value="">All Namespaces</option>
            </select>
            <button onclick="search()">SEARCH</button>
            <div class="loading" id="loading">Searching...</div>
        </div>

        <div class="results" id="results">
            <h2>Results</h2>
            <div id="resultsList"></div>
        </div>

        <div class="api-info">
            <h2>📡 API Endpoints</h2>
            <p>This is a live, queryable API. Test it yourself:</p>

            <h3>GET /api/stats</h3>
            <pre><code>curl https://demo.complexsimplicityai.com/api/stats</code></pre>

            <h3>GET /api/search?q=query&namespace=wolf_story</h3>
            <pre><code>curl "https://demo.complexsimplicityai.com/api/search?q=memory&limit=5"</code></pre>

            <h3>GET /api/namespaces</h3>
            <pre><code>curl https://demo.complexsimplicityai.com/api/namespaces</code></pre>

            <p style="margin-top: 20px;">
                <strong>Built by:</strong> The Wolf<br>
                <strong>Stack:</strong> Python + Flask + PostgreSQL 16 + pgai + Ollama<br>
                <strong>Source:</strong> Available on request
            </p>
        </div>
    </div>

    <script>
        // Load stats on page load
        async function loadStats() {
            const response = await fetch('/api/stats');
            const data = await response.json();

            document.getElementById('total').textContent = data.total_memories.toLocaleString();
            document.getElementById('namespaces').textContent = data.namespaces.length;

            // Populate namespace filter
            const select = document.getElementById('namespaceFilter');
            data.namespaces.forEach(ns => {
                const option = document.createElement('option');
                option.value = ns.namespace;
                option.textContent = `${ns.namespace} (${ns.count.toLocaleString()})`;
                select.appendChild(option);
            });
        }

        async function search() {
            const query = document.getElementById('searchQuery').value;
            const namespace = document.getElementById('namespaceFilter').value;

            if (!query) {
                alert('Please enter a search query');
                return;
            }

            document.getElementById('loading').style.display = 'block';
            document.getElementById('results').style.display = 'none';

            const url = `/api/search?q=${encodeURIComponent(query)}&namespace=${namespace}&limit=20`;
            const response = await fetch(url);
            const data = await response.json();

            document.getElementById('loading').style.display = 'none';
            document.getElementById('results').style.display = 'block';

            const resultsList = document.getElementById('resultsList');
            resultsList.innerHTML = '';

            if (data.results.length === 0) {
                resultsList.innerHTML = '<p>No results found.</p>';
                return;
            }

            data.results.forEach(result => {
                const item = document.createElement('div');
                item.className = 'result-item';

                const preview = result.content.length > 200
                    ? result.content.substring(0, 200) + '...'
                    : result.content;

                item.innerHTML = `
                    <div>
                        <span class="namespace-badge">${result.namespace}</span>
                        <small>${new Date(result.created_at).toLocaleString()}</small>
                    </div>
                    <div style="margin-top: 10px;">${preview}</div>
                `;
                resultsList.appendChild(item);
            });
        }

        // Allow search on Enter key
        document.getElementById('searchQuery').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') search();
        });

        // Load stats when page loads
        loadStats();
    </script>
</body>
</html>