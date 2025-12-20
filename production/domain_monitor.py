#!/usr/bin/env python3
"""
Domain & Subdomain Monitor
Checks all Complex Logic services and alerts on failures
"""

import requests
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Services to monitor
SERVICES = {
    "Production Services": [
        {
            "name": "Wolf Hunt UI",
            "url": "http://localhost:3333",
            "timeout": 5
        },
        {
            "name": "Complex Logic Container",
            "url": "http://localhost:4500/health",
            "timeout": 5
        },
    ],
    "Databases": [
        {
            "name": "Neo4j",
            "url": "http://localhost:8474",  # Neo4j HTTP API
            "timeout": 3
        },
        {
            "name": "PostgreSQL",
            "type": "tcp",
            "host": "100.110.82.181",
            "port": 5433,
            "timeout": 3
        },
    ],
    "Job Boards (ROCN)": [
        {
            "name": "ZipRecruiter MCP",
            "url": "http://localhost:5001/health",
            "timeout": 5,
            "optional": True
        },
        {
            "name": "GameBrain MCP",
            "url": "http://localhost:5002/health",
            "timeout": 5,
            "optional": True
        },
        {
            "name": "Fantastic Jobs MCP",
            "url": "http://localhost:5003/health",
            "timeout": 5,
            "optional": True
        },
        {
            "name": "Indeed MCP",
            "url": "http://localhost:5004/health",
            "timeout": 5,
            "optional": True
        },
        {
            "name": "GraphQL Jobs MCP",
            "url": "http://localhost:5005/health",
            "timeout": 5,
            "optional": True
        },
        {
            "name": "Remotive MCP",
            "url": "http://localhost:5006/health",
            "timeout": 5,
            "optional": True
        },
        {
            "name": "WhatJobs MCP",
            "url": "http://localhost:5007/health",
            "timeout": 5,
            "optional": True
        },
    ],
    "External Domains (Tailscale)": [
        {
            "name": "Portainer (Mac)",
            "url": "https://mactainer.complexsimplicityai.com",
            "timeout": 10,
            "verify_ssl": False
        },
        {
            "name": "Caddy Manager",
            "url": "https://caddy-manager.complexsimplicityai.com",
            "timeout": 10,
            "verify_ssl": False
        },
        {
            "name": "Portainer (Server)",
            "url": "https://portainer.complexsimplicityai.com",
            "timeout": 10,
            "verify_ssl": False
        },
    ]
}

class ServiceMonitor:
    def __init__(self):
        self.failures = {}
        self.last_status = {}

    def check_http(self, name: str, url: str, timeout: int = 5, verify_ssl: bool = True) -> Dict:
        """Check HTTP/HTTPS endpoint"""
        try:
            response = requests.get(
                url,
                timeout=timeout,
                verify=verify_ssl,
                allow_redirects=True
            )

            if response.status_code < 400:
                return {
                    "status": "UP",
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds()
                }
            else:
                return {
                    "status": "ERROR",
                    "status_code": response.status_code,
                    "error": f"HTTP {response.status_code}"
                }

        except requests.exceptions.Timeout:
            return {"status": "TIMEOUT", "error": "Request timeout"}
        except requests.exceptions.ConnectionError:
            return {"status": "DOWN", "error": "Connection refused"}
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}

    def check_tcp(self, name: str, host: str, port: int, timeout: int = 3) -> Dict:
        """Check TCP port connectivity"""
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()

            if result == 0:
                return {"status": "UP", "port": port}
            else:
                return {"status": "DOWN", "error": f"Port {port} not accessible"}

        except Exception as e:
            return {"status": "ERROR", "error": str(e)}

    def check_service(self, service: Dict) -> Dict:
        """Check a single service"""
        name = service["name"]

        if service.get("type") == "tcp":
            result = self.check_tcp(
                name,
                service["host"],
                service["port"],
                service.get("timeout", 3)
            )
        else:
            result = self.check_http(
                name,
                service["url"],
                service.get("timeout", 5),
                service.get("verify_ssl", True)
            )

        result["name"] = name
        result["timestamp"] = datetime.now().isoformat()
        result["optional"] = service.get("optional", False)

        return result

    def alert(self, service_name: str, result: Dict):
        """Alert on service failure"""
        # Only alert on status changes (not every failure)
        current_status = result["status"]
        last_status = self.last_status.get(service_name)

        if current_status != last_status:
            if current_status in ["DOWN", "ERROR", "TIMEOUT"]:
                logger.error(f"🚨 {service_name}: {current_status} - {result.get('error', 'Unknown error')}")
            elif current_status == "UP" and last_status in ["DOWN", "ERROR", "TIMEOUT"]:
                logger.info(f"✅ {service_name}: Recovered")

        self.last_status[service_name] = current_status

    def check_all(self) -> Dict[str, List[Dict]]:
        """Check all services"""
        results = {}

        for category, services in SERVICES.items():
            results[category] = []

            for service in services:
                result = self.check_service(service)
                results[category].append(result)

                # Alert on failures (skip optional services)
                if not result.get("optional"):
                    if result["status"] in ["DOWN", "ERROR", "TIMEOUT"]:
                        self.alert(service["name"], result)
                    elif result["status"] == "UP":
                        # Only log recovery, not every success
                        if self.last_status.get(service["name"]) in ["DOWN", "ERROR", "TIMEOUT"]:
                            self.alert(service["name"], result)

        return results

    def print_status(self, results: Dict[str, List[Dict]]):
        """Print formatted status report"""
        print("\n" + "="*60)
        print(f"Service Status Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)

        for category, services in results.items():
            print(f"\n{category}:")

            for service in services:
                name = service["name"]
                status = service["status"]

                if status == "UP":
                    icon = "✅"
                    color = ""
                elif status in ["DOWN", "ERROR"]:
                    icon = "❌"
                    color = ""
                elif status == "TIMEOUT":
                    icon = "⏱️"
                    color = ""
                else:
                    icon = "⚠️"
                    color = ""

                optional_tag = " [optional]" if service.get("optional") else ""

                if status == "UP":
                    response_time = service.get("response_time", 0)
                    print(f"  {icon} {name}{optional_tag}: {status} ({response_time:.2f}s)")
                else:
                    error = service.get("error", "Unknown")
                    print(f"  {icon} {name}{optional_tag}: {status} - {error}")

def main():
    """Main monitoring loop"""
    monitor = ServiceMonitor()

    logger.info("🔍 Starting Domain Monitor")
    logger.info("Monitoring Complex Logic infrastructure")

    check_interval = 60  # Check every 60 seconds

    try:
        while True:
            results = monitor.check_all()
            monitor.print_status(results)

            time.sleep(check_interval)

    except KeyboardInterrupt:
        logger.info("\n⏸️  Stopping monitor")
        print("\nFinal status:")
        results = monitor.check_all()
        monitor.print_status(results)

if __name__ == "__main__":
    main()
