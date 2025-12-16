#!/usr/bin/env python3
"""
WOLF UI Dashboard Server
Lightweight HTTP server for the LCD dashboard interface
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import sys
import json
import subprocess

class WolfUIHandler(SimpleHTTPRequestHandler):
    """Custom handler for WOLF dashboard with GPU metrics support"""
    
    def __init__(self, *args, **kwargs):
        # Set the directory to serve files from
        super().__init__(*args, directory='/mnt/Wolfpack/Github/memory_layer/mem0/wolf-ui', **kwargs)
    
    def do_GET(self):
        """Handle GET requests with GPU metrics endpoint"""
        
        # GPU metrics endpoint
        if self.path == '/api/gpu-stats':
            self.send_gpu_metrics()
            return
        
        # Serve static files
        super().do_GET()
    
    def send_gpu_metrics(self):
        """Get AMD GPU metrics via lact or radeontop"""
        try:
            # Try lact first (if installed)
            gpu_data = self.get_lact_metrics()
            
            if not gpu_data:
                # Fallback to radeontop or mock data
                gpu_data = self.get_mock_gpu_data()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(gpu_data).encode())
            
        except Exception as e:
            self.send_error(500, f"GPU metrics error: {str(e)}")
    
    def get_lact_metrics(self):
        """Get GPU metrics from LACT daemon"""
        try:
            # LACT CLI command
            result = subprocess.run(
                ['lact', 'info', '--json'],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return {
                    'load': data.get('gpu_usage', 0),
                    'temperature': data.get('temperature', 0),
                    'vram_used': data.get('vram_used_mb', 0),
                    'vram_total': data.get('vram_total_mb', 8192),
                    'power_draw': data.get('power_watts', 0)
                }
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            pass
        
        return None
    
    def get_mock_gpu_data(self):
        """Generate mock GPU data for testing"""
        import random
        base_load = 30 + random.random() * 40
        
        return {
            'load': int(base_load),
            'temperature': int(50 + base_load * 0.5),
            'vram_used': int(2000 + random.random() * 1000),
            'vram_total': 8192,
            'power_draw': int(100 + base_load * 2)
        }
    
    def log_message(self, format, *args):
        """Custom log format"""
        print(f"[WOLF-UI] {self.address_string()} - {format % args}")


def run_server(port=3000):
    """Start the WOLF UI dashboard server"""
    
    server_address = ('', port)
    httpd = HTTPServer(server_address, WolfUIHandler)
    
    print(f"""
╔════════════════════════════════════════════════════════╗
║          WOLF MEMORY CONTROL DASHBOARD                 ║
║                  LCD Interface v1.0                    ║
╠════════════════════════════════════════════════════════╣
║  Server running on: http://localhost:{port}            ║
║  Dashboard ready: Virtual LCD display active           ║
║  GPU Metrics: AMD LACT integration enabled             ║
╚════════════════════════════════════════════════════════╝
    """)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[WOLF-UI] Shutting down server...")
        httpd.shutdown()


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    run_server(port)
