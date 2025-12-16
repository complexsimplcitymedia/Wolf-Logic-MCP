#!/usr/bin/env python3
"""
Wolf Hunt UI Server
Serves the job hunting command center interface
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import sys
from pathlib import Path

class WolfHuntHandler(SimpleHTTPRequestHandler):
    """Custom handler for Wolf Hunt UI"""

    def __init__(self, *args, **kwargs):
        # Set the directory to serve files from
        super().__init__(*args, directory=str(Path(__file__).parent), **kwargs)

    def end_headers(self):
        """Add CORS headers"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

    def do_OPTIONS(self):
        """Handle preflight requests"""
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        """Custom log format"""
        print(f"[WOLF-HUNT] {self.address_string()} - {format % args}")


def run_server(port=3001):
    """Start the Wolf Hunt UI server"""

    server_address = ('', port)
    httpd = HTTPServer(server_address, WolfHuntHandler)

    print(f"""
╔════════════════════════════════════════════════════════╗
║              WOLF HUNT COMMAND CENTER                  ║
║              Job Search War Room v1.0                  ║
╠════════════════════════════════════════════════════════╣
║  Server running on: http://localhost:{port}            ║
║  UI ready: Job hunting interface active               ║
║  MCP Servers: 7 ROCN + 5 COMS ready                   ║
╚════════════════════════════════════════════════════════╝

Available Features:
  ✓ Multi-board job search (7 job boards)
  ✓ Resume generator integration
  ✓ Application tracker
  ✓ Bulk apply operations
  ✓ Campaign management
  ✓ CSV export

MCP Servers:
  ROCN: ZipRecruiter, Indeed, Remotive, GraphQL Jobs,
        GameBrain, Fantastic Jobs, WhatJobs
  COMS: Thunderbird, Linux Kernel, LibreOffice,
        Vulkan, Firefox

Press Ctrl+C to stop server...
    """)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[WOLF-HUNT] Shutting down server...")
        httpd.shutdown()


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 3001
    run_server(port)
