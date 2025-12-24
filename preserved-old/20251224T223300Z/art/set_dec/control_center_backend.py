"""
Wolf Logic Control Center - Backend
Functional script execution interface
Port 2500
"""

from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
import subprocess
import os
from pathlib import Path

app = Flask(__name__)
CORS(app)

# Writers department scripts
WRITERS_DIR = Path("/mnt/Wolf-code/Wolf-Ai-Enterptises/writers")

def get_scripts():
    """Get all Python scripts from writers department"""
    scripts = []
    if WRITERS_DIR.exists():
        for subdir in WRITERS_DIR.iterdir():
            if subdir.is_dir() and not subdir.name.startswith('_'):
                for script in subdir.glob("*.py"):
                    if not script.name.startswith('_'):
                        scripts.append({
                            'category': subdir.name,
                            'name': script.stem,
                            'path': str(script)
                        })
    return sorted(scripts, key=lambda x: (x['category'], x['name']))

def run_script(script_path):
    """Execute a script in the messiah environment"""
    try:
        result = subprocess.run(
            ['/home/thewolfwalksalone/anaconda3/envs/messiah/bin/python', script_path],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(Path(script_path).parent)
        )
        return {
            'ok': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
    except subprocess.TimeoutExpired:
        return {'ok': False, 'error': 'Script timed out (120s)'}
    except Exception as e:
        return {'ok': False, 'error': str(e)}

CONTROL_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Wolf Control Center</title>
    <style>
        body {
            font-family: monospace;
            background: #1a1a1a;
            color: #00ff66;
            padding: 20px;
            margin: 0;
        }
        h1 {
            border-bottom: 1px solid #333;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        .category {
            margin: 20px 0;
            padding: 15px;
            background: #222;
            border-left: 3px solid #00ff66;
        }
        .category-title {
            font-size: 1.1em;
            margin-bottom: 10px;
            color: #00aa44;
            text-transform: uppercase;
        }
        .scripts {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }
        button {
            background: #333;
            color: #00ff66;
            border: 1px solid #00ff66;
            padding: 8px 16px;
            cursor: pointer;
            font-family: monospace;
            font-size: 0.85em;
        }
        button:hover {
            background: #00ff66;
            color: #000;
        }
        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        button.running {
            background: #ffaa00;
            color: #000;
            border-color: #ffaa00;
        }
        #output {
            background: #000;
            padding: 15px;
            margin-top: 20px;
            white-space: pre-wrap;
            font-size: 0.85em;
            max-height: 400px;
            overflow-y: auto;
            border: 1px solid #333;
        }
        .success { color: #00ff66; }
        .error { color: #ff4444; }
        .info { color: #00aaff; }
    </style>
</head>
<body>
    <h1>WOLF CONTROL CENTER</h1>
    <div id="categories"></div>
    <div id="output">Ready.</div>

    <script>
        async function loadScripts() {
            const res = await fetch('/api/scripts');
            const data = await res.json();

            const categories = {};
            data.scripts.forEach(s => {
                if (!categories[s.category]) categories[s.category] = [];
                categories[s.category].push(s);
            });

            const container = document.getElementById('categories');
            container.innerHTML = '';

            Object.keys(categories).sort().forEach(cat => {
                const div = document.createElement('div');
                div.className = 'category';
                div.innerHTML = '<div class="category-title">' + cat + '</div><div class="scripts"></div>';

                const scriptsDiv = div.querySelector('.scripts');
                categories[cat].forEach(s => {
                    const btn = document.createElement('button');
                    btn.textContent = s.name;
                    btn.onclick = () => runScript(s.path, s.name, btn);
                    scriptsDiv.appendChild(btn);
                });

                container.appendChild(div);
            });
        }

        async function runScript(path, name, btn) {
            const output = document.getElementById('output');
            output.innerHTML = '<span class="info">[' + new Date().toLocaleTimeString() + '] Running: ' + name + '...</span>\\n';

            btn.disabled = true;
            btn.classList.add('running');

            try {
                const res = await fetch('/api/run', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({path: path})
                });
                const data = await res.json();

                if (data.ok) {
                    output.innerHTML += '<span class="success">[SUCCESS]</span>\\n';
                } else {
                    output.innerHTML += '<span class="error">[FAILED]</span>\\n';
                }

                if (data.stdout) output.innerHTML += data.stdout + '\\n';
                if (data.stderr) output.innerHTML += '<span class="error">' + data.stderr + '</span>\\n';
                if (data.error) output.innerHTML += '<span class="error">' + data.error + '</span>\\n';

            } catch (e) {
                output.innerHTML += '<span class="error">[ERROR] ' + e.message + '</span>\\n';
            }

            btn.disabled = false;
            btn.classList.remove('running');
            output.scrollTop = output.scrollHeight;
        }

        loadScripts();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(CONTROL_HTML)

@app.route('/api/scripts')
def api_scripts():
    return jsonify({'scripts': get_scripts()})

@app.route('/api/run', methods=['POST'])
def api_run():
    data = request.json or {}
    path = data.get('path')
    if not path or not os.path.exists(path):
        return jsonify({'ok': False, 'error': 'Script not found'})
    return jsonify(run_script(path))

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'service': 'Wolf Control Center Backend'})

if __name__ == '__main__':
    print("Wolf Control Center Backend starting on port 2500...")
    print(f"Scripts directory: {WRITERS_DIR}")
    scripts = get_scripts()
    print(f"Found {len(scripts)} scripts")
    app.run(host='0.0.0.0', port=2500, debug=False)
