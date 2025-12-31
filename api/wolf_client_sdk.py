#!/usr/bin/env python3
"""
Wolf Client SDK - Smart multi-server failover for conversation threads
Handles geographic routing, automatic failover, and load balancing
"""

import requests
import json
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging
from dataclasses import dataclass
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ServerStatus(Enum):
    """Server health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"


@dataclass
class ServerEndpoint:
    """MCP Gateway server endpoint configuration"""
    name: str
    url: str
    region: str
    priority: int  # Lower = higher priority
    status: ServerStatus = ServerStatus.HEALTHY
    last_check: float = 0
    response_time: float = 0


class WolfClient:
    """
    Wolf MCP Gateway Client with automatic failover
    
    Features:
    - Geographic routing (prefer closest server)
    - Automatic failover on server failure
    - Health monitoring with exponential backoff
    - Load balancing between healthy servers
    - Conversation thread submission
    """
    
    def __init__(
        self,
        oauth_token: str,
        servers: List[Dict[str, Any]] = None,
        timeout: int = 30,
        retry_attempts: int = 3,
        health_check_interval: int = 60
    ):
        """
        Initialize Wolf Client
        
        Args:
            oauth_token: Authentik OAuth token
            servers: List of server configs [{name, url, region, priority}]
            timeout: Request timeout in seconds
            retry_attempts: Number of retry attempts per server
            health_check_interval: Seconds between health checks
        """
        self.oauth_token = oauth_token
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.health_check_interval = health_check_interval
        
        # Initialize servers
        self.servers = [
            ServerEndpoint(**server) for server in (servers or self._default_servers())
        ]
        self.servers.sort(key=lambda s: s.priority)
        
        # Headers
        self.headers = {
            "Authorization": f"Bearer {self.oauth_token}",
            "Content-Type": "application/json"
        }
        
        logger.info(f"Wolf Client initialized with {len(self.servers)} servers")
        for server in self.servers:
            logger.info(f"  [{server.priority}] {server.name} ({server.region}): {server.url}")
    
    @staticmethod
    def _default_servers() -> List[Dict[str, Any]]:
        """Default server configuration (Server A and Server B)"""
        return [
            {
                "name": "Server-A-Primary",
                "url": "https://wolf-logic-mcp.complexsimplicityai.com",
                "region": "us-east",
                "priority": 1
            },
            {
                "name": "Server-B-Secondary",
                "url": "https://wolf-logic-mcp-backup.complexsimplicityai.com",
                "region": "us-west",
                "priority": 2
            }
        ]
    
    def _check_server_health(self, server: ServerEndpoint) -> Tuple[ServerStatus, float]:
        """
        Check server health and measure response time
        
        Returns:
            (status, response_time_ms)
        """
        # Skip if recently checked
        if time.time() - server.last_check < self.health_check_interval:
            return server.status, server.response_time
        
        try:
            start = time.time()
            response = requests.get(
                f"{server.url}/health",
                timeout=5
            )
            response_time = (time.time() - start) * 1000  # ms
            
            server.last_check = time.time()
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'healthy':
                    server.status = ServerStatus.HEALTHY
                    server.response_time = response_time
                    return ServerStatus.HEALTHY, response_time
                else:
                    server.status = ServerStatus.DEGRADED
                    return ServerStatus.DEGRADED, response_time
            else:
                server.status = ServerStatus.DOWN
                return ServerStatus.DOWN, 0
                
        except Exception as e:
            logger.warning(f"Health check failed for {server.name}: {e}")
            server.status = ServerStatus.DOWN
            server.last_check = time.time()
            return ServerStatus.DOWN, 0
    
    def _get_best_server(self) -> Optional[ServerEndpoint]:
        """
        Get best available server based on:
        1. Health status
        2. Priority
        3. Response time
        """
        # Update health status for all servers
        for server in self.servers:
            self._check_server_health(server)
        
        # Filter healthy servers
        healthy = [s for s in self.servers if s.status == ServerStatus.HEALTHY]
        
        if healthy:
            # Sort by priority, then response time
            healthy.sort(key=lambda s: (s.priority, s.response_time))
            return healthy[0]
        
        # Try degraded servers if no healthy ones
        degraded = [s for s in self.servers if s.status == ServerStatus.DEGRADED]
        if degraded:
            degraded.sort(key=lambda s: s.priority)
            logger.warning(f"Using degraded server: {degraded[0].name}")
            return degraded[0]
        
        logger.error("All servers are down!")
        return None
    
    def _make_request(
        self,
        endpoint: str,
        method: str = "POST",
        data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Make request with automatic failover
        
        Args:
            endpoint: API endpoint path (e.g., '/mcp/conversations/submit')
            method: HTTP method
            data: Request payload
            
        Returns:
            Response JSON
            
        Raises:
            Exception if all servers fail
        """
        last_error = None
        
        # Try each server in priority order
        for attempt in range(self.retry_attempts):
            server = self._get_best_server()
            
            if not server:
                if attempt < self.retry_attempts - 1:
                    logger.warning(f"No servers available, retrying in {2 ** attempt}s...")
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    raise Exception("All servers unavailable after retries")
            
            url = f"{server.url}{endpoint}"
            
            try:
                logger.info(f"[{server.name}] {method} {endpoint}")
                
                if method == "POST":
                    response = requests.post(
                        url,
                        headers=self.headers,
                        json=data,
                        timeout=self.timeout
                    )
                elif method == "GET":
                    response = requests.get(
                        url,
                        headers=self.headers,
                        timeout=self.timeout
                    )
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"✓ Success via {server.name} ({server.response_time:.0f}ms)")
                return result
                
            except requests.exceptions.RequestException as e:
                last_error = e
                logger.warning(f"✗ {server.name} failed: {e}")
                server.status = ServerStatus.DOWN
                server.last_check = time.time()
                
                # Try next server
                if attempt < self.retry_attempts - 1:
                    logger.info(f"Failing over to next server...")
                    time.sleep(0.5)
                    continue
        
        # All attempts failed
        raise Exception(f"All server attempts failed. Last error: {last_error}")
    
    def submit_conversation(
        self,
        messages: List[Dict[str, Any]],
        source: str,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Submit conversation thread to best available server
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            source: Client source (android, ios, web, desktop)
            title: Optional conversation title
            metadata: Optional metadata dict
            
        Returns:
            Response data with thread_id, filename, etc.
        """
        payload = {
            "title": title or f"Conversation {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "messages": messages,
            "source": source,
            "metadata": metadata or {}
        }
        
        return self._make_request("/mcp/conversations/submit", method="POST", data=payload)
    
    def list_conversations(self, limit: int = 20) -> Dict[str, Any]:
        """List user's conversations"""
        return self._make_request(f"/mcp/conversations/list?limit={limit}", method="GET")
    
    def get_conversation(self, thread_id: str) -> Dict[str, Any]:
        """Get specific conversation by thread_id"""
        return self._make_request(f"/mcp/conversations/{thread_id}", method="GET")
    
    def get_server_status(self) -> List[Dict[str, Any]]:
        """Get status of all configured servers"""
        status = []
        for server in self.servers:
            health, response_time = self._check_server_health(server)
            status.append({
                "name": server.name,
                "url": server.url,
                "region": server.region,
                "priority": server.priority,
                "status": health.value,
                "response_time_ms": response_time,
                "last_check": datetime.fromtimestamp(server.last_check).isoformat() if server.last_check > 0 else None
            })
        return status


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Wolf Client SDK - Multi-server conversation submission")
    parser.add_argument('--token', required=True, help='OAuth token')
    parser.add_argument('--source', default='cli', help='Client source')
    parser.add_argument('--file', help='JSON file with conversation')
    parser.add_argument('--status', action='store_true', help='Show server status only')
    
    # Custom server configuration
    parser.add_argument('--server-a', default='https://wolf-logic-mcp.complexsimplicityai.com', help='Server A URL')
    parser.add_argument('--server-b', default='https://wolf-logic-mcp-backup.complexsimplicityai.com', help='Server B URL')
    
    args = parser.parse_args()
    
    # Configure servers
    servers = [
        {
            "name": "Server-A",
            "url": args.server_a,
            "region": "primary",
            "priority": 1
        },
        {
            "name": "Server-B",
            "url": args.server_b,
            "region": "secondary",
            "priority": 2
        }
    ]
    
    # Initialize client
    client = WolfClient(oauth_token=args.token, servers=servers)
    
    # Show server status
    if args.status:
        print("\n📊 Server Status:")
        for server_info in client.get_server_status():
            status_emoji = "✅" if server_info['status'] == 'healthy' else "⚠️" if server_info['status'] == 'degraded' else "❌"
            print(f"{status_emoji} {server_info['name']} ({server_info['region']})")
            print(f"   URL: {server_info['url']}")
            print(f"   Status: {server_info['status']}")
            print(f"   Response: {server_info['response_time_ms']:.0f}ms")
            print(f"   Priority: {server_info['priority']}")
            print()
    
    # Submit conversation
    elif args.file:
        with open(args.file, 'r') as f:
            data = json.load(f)
        
        messages = data.get('messages', [])
        title = data.get('title')
        metadata = data.get('metadata', {})
        
        print(f"\n🚀 Submitting conversation: {len(messages)} messages")
        
        result = client.submit_conversation(
            messages=messages,
            source=args.source,
            title=title,
            metadata=metadata
        )
        
        if result.get('success'):
            print(f"✅ Success!")
            print(f"   Thread ID: {result['data']['thread_id']}")
            print(f"   Server: {result['data'].get('server', 'unknown')}")
            print(f"   Filename: {result['data']['filename']}")
        else:
            print(f"❌ Failed: {result.get('message')}")
    
    else:
        print("Use --status to check servers or --file to submit conversation")
