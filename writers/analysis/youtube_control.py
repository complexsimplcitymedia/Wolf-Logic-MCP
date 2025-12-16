#!/usr/bin/env python3
"""
YouTube Video Analysis Control Panel
Simple web UI to control video processing
"""

from flask import Flask, render_template_string, request, jsonify
import subprocess
import os
import signal

app = Flask(__name__)

MESSIAH_ACTIVATE = "source ~/anaconda3/bin/activate messiah"
ANALYST_LLAVA = "/mnt/Wolf-code/Wolf-Ai-Enterptises/writers/analysis/youtube_analyst_llava.py"
ANALYST_LLAMA = "/mnt/Wolf-code/Wolf-Ai-Enterptises/writers/analysis/youtube_analyst_llama.py"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>YouTube Control Panel</title>
    <style>
        body {
            font-family: 'Courier New', monospace;
            background: #0a0a0a;
            color: #00ff00;
            padding: 20px;
            max-width: 800px;
            margin: 0 auto;
        }
        h1 {
            border-bottom: 2px solid #00ff00;
            padding-bottom: 10px;
        }
        .section {
            background: #1a1a1a;
            border: 1px solid #00ff00;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }
        input[type="text"] {
            width: 100%;
            padding: 10px;
            background: #0a0a0a;
            border: 1px solid #00ff00;
            color: #00ff00;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            margin: 10px 0;
        }
        button {
            background: #00ff00;
            color: #0a0a0a;
            border: none;
            padding: 12px 24px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            font-weight: bold;
            cursor: pointer;
            margin: 5px;
            border-radius: 3px;
        }
        button:hover {
            background: #00cc00;
        }
        button.danger {
            background: #ff0000;
            color: #fff;
        }
        button.danger:hover {
            background: #cc0000;
        }
        .status {
            background: #0a0a0a;
            border: 1px solid #00ff00;
            padding: 15px;
            margin: 10px 0;
            font-size: 13px;
            max-height: 400px;
            overflow-y: auto;
        }
        .process {
            padding: 8px;
            margin: 5px 0;
            background: #1a1a1a;
            border-left: 3px solid #00ff00;
        }
        .label {
            color: #00cc00;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <h1>🎬 YouTube Video Control Panel</h1>

    <div class="section">
        <h2>Run Single Video</h2>
        <input type="text" id="videoUrl" placeholder="Paste YouTube URL here...">
        <div>
            <button onclick="runVideo('llava')">▶ Run with LLaVA 13b</button>
            <button onclick="runVideo('llama')">▶ Run with LLaMA 3.2 Vision</button>
        </div>
    </div>

    <div class="section">
        <h2>Control</h2>
        <button onclick="checkStatus()">🔄 Refresh Status</button>
        <button class="danger" onclick="killAll()">⛔ KILL ALL</button>
    </div>

    <div class="section">
        <h2>Status</h2>
        <div class="status" id="status">
            <p>Click "Refresh Status" to check running processes...</p>
        </div>
    </div>

    <script>
        function runVideo(model) {
            const url = document.getElementById('videoUrl').value.trim();
            if (!url) {
                alert('Enter a YouTube URL first');
                return;
            }

            fetch('/run', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({url: url, model: model})
            })
            .then(r => r.json())
            .then(data => {
                alert(data.message);
                checkStatus();
            })
            .catch(err => alert('Error: ' + err));
        }

        function killAll() {
            if (!confirm('Kill all YouTube analyst processes?')) return;

            fetch('/kill', {method: 'POST'})
            .then(r => r.json())
            .then(data => {
                alert(data.message);
                checkStatus();
            })
            .catch(err => alert('Error: ' + err));
        }

        function checkStatus() {
            fetch('/status')
            .then(r => r.json())
            .then(data => {
                const statusDiv = document.getElementById('status');
                if (data.processes.length === 0) {
                    statusDiv.innerHTML = '<p style="color: #888;">No processes running.</p>';
                } else {
                    let html = '<p class="label">Running Processes:</p>';
                    data.processes.forEach(p => {
                        html += `<div class="process">
                            <strong>PID ${p.pid}</strong> | ${p.model} | ${p.runtime}<br>
                            <small>${p.video}</small>
                        </div>`;
                    });
                    statusDiv.innerHTML = html;
                }
            })
            .catch(err => {
                document.getElementById('status').innerHTML = '<p style="color: #ff0000;">Error: ' + err + '</p>';
            });
        }

        // Auto-refresh every 5 seconds
        setInterval(checkStatus, 5000);
        checkStatus();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/run', methods=['POST'])
def run_video():
    data = request.json
    url = data.get('url', '').strip()
    model = data.get('model', 'llava')

    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    script = ANALYST_LLAVA if model == 'llava' else ANALYST_LLAMA
    model_name = "LLaVA 13b" if model == 'llava' else "LLaMA 3.2 Vision"

    cmd = f'{MESSIAH_ACTIVATE} && python {script} "{url}" --store --interval 15 > /tmp/youtube_analyst_{model}.log 2>&1 &'

    try:
        subprocess.Popen(cmd, shell=True, executable='/bin/bash')
        return jsonify({
            'success': True,
            'message': f'Started {model_name} on video'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/kill', methods=['POST'])
def kill_all():
    try:
        # Kill all youtube_analyst processes
        subprocess.run(['pkill', '-f', 'youtube_analyst'], check=False)

        # Kill auto-restart scripts
        subprocess.run(['pkill', '-f', 'auto_restart'], check=False)
        subprocess.run(['pkill', '-f', 'process_existing_videos'], check=False)

        return jsonify({
            'success': True,
            'message': 'All processes killed'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/status')
def status():
    try:
        result = subprocess.run(
            ['ps', 'aux'],
            capture_output=True,
            text=True
        )

        processes = []
        for line in result.stdout.split('\n'):
            if 'youtube_analyst' in line and 'grep' not in line:
                parts = line.split()
                pid = parts[1]
                runtime = parts[9]

                # Extract video name from command
                video = 'unknown'
                if 'yt_' in line:
                    video = line.split('yt_')[1].split('/')[0]

                # Determine model
                model = 'LLaVA 13b' if 'llava' in line else 'LLaMA 3.2 Vision'

                processes.append({
                    'pid': pid,
                    'runtime': runtime,
                    'video': f'yt_{video}',
                    'model': model
                })

        return jsonify({'processes': processes})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*50)
    print("YouTube Video Control Panel")
    print("="*50)
    print("\nAccess at: http://localhost:8889")
    print("\nPress Ctrl+C to stop\n")
    app.run(host='0.0.0.0', port=8889, debug=False)
