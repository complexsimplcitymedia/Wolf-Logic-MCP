"""
LACT API Client for AMD GPU Metrics
Connects to lactd Unix socket using JSON API
"""

import socket
import json
from typing import Dict, Any, Optional


class LACTClient:
    """Client for interacting with LACT daemon via JSON API"""

    def __init__(self, socket_path: str = "/var/run/lactd.sock"):
        self.socket_path = socket_path

    def _send_command(self, command: str, args: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Send a command to LACT daemon and return response"""
        try:
            # Create Unix socket connection
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect(self.socket_path)

            # Build request
            request = {"command": command}
            if args:
                request["args"] = args

            # Send request
            sock.sendall(json.dumps(request).encode('utf-8'))
            sock.shutdown(socket.SHUT_WR)

            # Receive response
            response_data = b''
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response_data += chunk

            sock.close()

            # Parse response
            response = json.loads(response_data.decode('utf-8'))

            if response.get('status') == 'ok':
                return response.get('data', {})
            else:
                print(f"LACT error: {response}")
                return None

        except FileNotFoundError:
            print(f"LACT socket not found at {self.socket_path}")
            return None
        except Exception as e:
            print(f"Error communicating with LACT: {e}")
            return None

    def ping(self) -> bool:
        """Check if LACT daemon is responsive"""
        result = self._send_command("ping")
        return result is not None

    def list_devices(self) -> Optional[list]:
        """List all available GPU devices"""
        return self._send_command("list_devices")

    def get_device_info(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a GPU device"""
        return self._send_command("device_info", {"id": device_id})

    def get_device_stats(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get live statistics for a GPU device"""
        return self._send_command("device_stats", {"id": device_id})

    def get_device_clocks_info(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get clock information for a GPU device"""
        return self._send_command("device_clocks_info", {"id": device_id})

    def get_gpu_config(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get current GPU configuration"""
        return self._send_command("get_gpu_config", {"id": device_id})

    def system_info(self) -> Optional[Dict[str, Any]]:
        """Get system-wide information"""
        return self._send_command("system_info")

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all available GPU metrics"""
        metrics = {
            'available': False,
            'devices': [],
            'system_info': {}
        }

        # Check if LACT is available
        if not self.ping():
            return metrics

        metrics['available'] = True

        # Get system info
        sys_info = self.system_info()
        if sys_info:
            metrics['system_info'] = sys_info

        # Get device list
        devices = self.list_devices()
        if not devices:
            return metrics

        # Get detailed info for each device
        for device in devices:
            device_id = device.get('id')
            if not device_id:
                continue

            device_data = {
                'id': device_id,
                'name': device.get('name', 'Unknown'),
                'info': self.get_device_info(device_id),
                'stats': self.get_device_stats(device_id),
                'clocks': self.get_device_clocks_info(device_id),
                'config': self.get_gpu_config(device_id)
            }

            # Extract summary metrics
            if device_data['stats']:
                stats = device_data['stats']
                device_data['summary'] = {
                    'gpu_name': device_data['name'],
                    'temperature': stats.get('temps', {}).get('edge', 0),
                    'power': stats.get('power', {}).get('average', 0),
                    'fan_rpm': stats.get('fan', {}).get('speed_current', 0),
                    'fan_percent': stats.get('fan', {}).get('speed_percent', 0),
                    'gpu_usage': stats.get('busy_percent', 0),
                    'vram_usage': stats.get('vram', {}).get('used', 0),
                    'vram_total': stats.get('vram', {}).get('total', 0),
                }

                # Add clock speeds if available
                if device_data['clocks']:
                    clocks = device_data['clocks']
                    device_data['summary']['gpu_clock'] = clocks.get('core_clock', {}).get('current', 0)
                    device_data['summary']['mem_clock'] = clocks.get('memory_clock', {}).get('current', 0)

            metrics['devices'].append(device_data)

        return metrics


# Test the client
if __name__ == "__main__":
    client = LACTClient()

    if client.ping():
        print("✓ LACT daemon is running")
        metrics = client.get_all_metrics()
        print(json.dumps(metrics, indent=2))
    else:
        print("✗ LACT daemon is not accessible")
        print(f"  Make sure lactd is running and socket exists at {client.socket_path}")
        print(f"  Try: systemctl status lactd")
