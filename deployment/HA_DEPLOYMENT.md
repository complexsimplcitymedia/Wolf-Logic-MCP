# Wolf MCP Gateway - High Availability Deployment

## Architecture Overview

```
                          ┌─────────────────┐
                          │   HAProxy LB    │
                          │   Port 8000     │
                          └────────┬────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
           ┌────────▼────────┐         ┌─────────▼────────┐
           │   Server A      │         │   Server B       │
           │   (Primary)     │         │   (Secondary)    │
           │   Port 8001     │         │   Port 8002      │
           └────────┬────────┘         └─────────┬────────┘
                    │                             │
                    └──────────────┬──────────────┘
                                   │
                          ┌────────▼────────┐
                          │   PostgreSQL    │
                          │   Shared Data   │
                          │   NFS Storage   │
                          └─────────────────┘
```

## Features

- **Automatic Failover**: If Server A goes down, traffic routes to Server B
- **Health Monitoring**: HAProxy checks `/health` every 5 seconds
- **Load Balancing**: Distribute load across healthy servers
- **Shared Storage**: Both servers write to same NFS mount
- **Geographic Distribution**: Server A (us-east), Server B (us-west)
- **Client-Side Intelligence**: SDK automatically selects best server

## Quick Start

### 1. Deploy Both Servers

```bash
cd /home/thewolfwalksalone/cognitive-layer/Wolf-Logic-MCP/deployment

# Start Server A + Server B + Load Balancer
docker-compose -f docker-compose.ha-gateway.yml up -d

# Check status
docker-compose -f docker-compose.ha-gateway.yml ps

# View logs
docker-compose -f docker-compose.ha-gateway.yml logs -f
```

### 2. Verify Health

```bash
# Check Server A (Primary)
curl https://wolf-logic-mcp.complexsimplicityai.com/health

# Check Server B (Backup)
curl https://wolf-logic-mcp-backup.complexsimplicityai.com/health

# HAProxy Stats Dashboard (if using load balancer)
open https://wolf-logic-mcp.complexsimplicityai.com/haproxy/stats
```

### 3. Test Client Failover

```bash
cd /home/thewolfwalksalone/cognitive-layer/Wolf-Logic-MCP/api

# Test with SDK (automatic failover)
python wolf_client_sdk.py \
  --token YOUR_OAUTH_TOKEN \
  --status

# Should show both servers
```

## Client Configuration

### Python SDK (Recommended)

```python
from api.wolf_client_sdk import WolfClient

# Client automatically handles failover
client = WolfClient(
    oauth_token="your_token_here",
    servers=[
        {
            "name": "Server-A",
            "url": "https://wolf-logic-mcp.complexsimplicityai.com",
            "region": "us-east",
            "priority": 1
        },
        {
            "name": "Server-B",
            "url": "https://wolf-logic-mcp-backup.complexsimplicityai.com",
            "region": "us-west",
            "priority": 2
        }
    ]
)

# Submit conversation - automatically uses best server
result = client.submit_conversation(
    messages=[
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"}
    ],
    source="android"
)

print(f"Submitted to: {result['data']['queue_path']}")
```

### Direct API Calls

```bash
# Submit to primary server
curl -X POST https://wolf-logic-mcp.complexsimplicityai.com/mcp/conversations/submit \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Conversation",
    "messages": [
      {"role": "user", "content": "Hello"}
    ],
    "source": "cli",
    "metadata": {}
  }'

# If Server A fails, try Server B
curl -X POST https://wolf-logic-mcp-backup.complexsimplicityai.com/mcp/conversations/submit \
  ...same payload...
```

### Standard Entry Point

```bash
# Reverse proxy routes to healthy backend
curl -X POST https://wolf-logic-mcp.complexsimplicityai.com/mcp/conversations/submit \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '...'
```

## Server Endpoints

### Primary Server
- Base URL: https://wolf-logic-mcp.complexsimplicityai.com
- Health: https://wolf-logic-mcp.complexsimplicityai.com/health
- Swagger: https://wolf-logic-mcp.complexsimplicityai.com/docs
- Submit: https://wolf-logic-mcp.complexsimplicityai.com/mcp/conversations/submit

### Backup Server (optional separate subdomain)
- Base URL: https://wolf-logic-mcp-backup.complexsimplicityai.com
- Health: https://wolf-logic-mcp-backup.complexsimplicityai.com/health
- Swagger: https://wolf-logic-mcp-backup.complexsimplicityai.com/docs
- Submit: https://wolf-logic-mcp-backup.complexsimplicityai.com/mcp/conversations/submit

**Note**: Both URLs route through reverse proxy (Caddy/nginx) on port 443. Backend services run on ports 8001/8002 internally.

## Failure Scenarios

### Scenario 1: Server A Goes Down
```
Client Request → LB Port 8000 → Server A (DOWN) → Failover to Server B ✓
```

### Scenario 2: Server B Goes Down
```
Client Request → LB Port 8000 → Server A (UP) → Success ✓
```

### Scenario 3: Both Servers Down
```
Client Request → LB Port 8000 → 503 Service Unavailable
SDK: Retries with exponential backoff (3 attempts)
```

### Scenario 4: Network Partition
```
Client → Direct to Server A → Success
Client → Direct to Server B → Success
(Both independent, shared data via NFS)
```

## Monitoring

### HAProxy Stats Dashboard

Visit https://wolf-logic-mcp.complexsimplicityai.com:9090/stats

Shows:
- Active/backup server status
- Request rates
- Response times
- Failed health checks

### Prometheus + Grafana (Optional)

```bash
# Start monitoring stack
docker-compose -f docker-compose.ha-gateway.yml --profile monitoring up -d

# Grafana: https://wolf-logic-mcp.complexsimplicityai.com:3001
# Default: admin / admin
```

## Maintenance

### Rolling Updates

```bash
# Update Server B (zero downtime)
docker-compose -f docker-compose.ha-gateway.yml stop wolf-gateway-b
docker-compose -f docker-compose.ha-gateway.yml up -d --build wolf-gateway-b

# Wait for health check
sleep 30

# Update Server A
docker-compose -f docker-compose.ha-gateway.yml stop wolf-gateway-a
docker-compose -f docker-compose.ha-gateway.yml up -d --build wolf-gateway-a
```

### Backup Server Only Mode

```bash
# Edit haproxy.cfg - remove "backup" from server-b
# Restart load balancer
docker-compose -f docker-compose.ha-gateway.yml restart wolf-loadbalancer
```

### Geographic Routing (Future)

```nginx
# Nginx geo-routing example
geo $closest_server {
    default server-a;
    # West coast IPs → Server B
    198.51.100.0/24 server-b;
}

upstream wolf_gateway {
    server 100.110.82.181:8001;  # Server A
    server 100.110.82.181:8002;  # Server B
}
```

## Data Consistency

Both servers share:
- **PostgreSQL**: Same database connection
- **NFS Storage**: `/mnt/Wolf-code/Wolf-Ai-Enterptises/data/`
  - `/data/conversations/` - Shared conversation queue
  - `/data/intake/` - Shared intake queue

No data synchronization needed - all writes go to shared storage.

## Security

### OAuth Token Validation
Both servers validate tokens against same Authentik instance:
- Authentik URL: http://100.110.82.181:9000
- Userinfo endpoint: `/application/o/userinfo/`

### Network Isolation
```bash
# Firewall rules (example)
# Only allow clients to hit LB port 8000
iptables -A INPUT -p tcp --dport 8000 -j ACCEPT

# Block direct access to 8001/8002 from outside
iptables -A INPUT -p tcp --dport 8001 -s 172.28.0.0/16 -j ACCEPT
iptables -A INPUT -p tcp --dport 8002 -s 172.28.0.0/16 -j ACCEPT
iptables -A INPUT -p tcp --dport 8001 -j DROP
iptables -A INPUT -p tcp --dport 8002 -j DROP
```

## Client Examples

### Android App
```kotlin
val client = WolfClient(
    oauthToken = getAuthToken(),
    servers = listOf(
        Server("https://wolf-logic-mcp.complexsimplicityai.com", priority = 1),
        Server("https://wolf-logic-mcp-backup.complexsimplicityai.com", priority = 2)
    )
)

client.submitConversation(messages, "android")
```

### iOS App
```swift
let client = WolfClient(
    oauthToken: getAuthToken(),
    servers: [
        Server(url: "https://wolf-logic-mcp.complexsimplicityai.com", priority: 1),
        Server(url: "https://wolf-logic-mcp-backup.complexsimplicityai.com", priority: 2)
    ]
)

client.submitConversation(messages: messages, source: "ios")
```

### Web App
```javascript
const client = new WolfClient({
    oauthToken: getAuthToken(),
    servers: [
        { url: 'https://wolf-logic-mcp.complexsimplicityai.com', priority: 1 },
        { url: 'https://wolf-logic-mcp-backup.complexsimplicityai.com', priority: 2 }
    ]
});

await client.submitConversation(messages, 'web');
```

## Troubleshooting

### Server A not responding
```bash
# Check container
docker logs wolf-gateway-server-a

# Check health through reverse proxy
curl https://wolf-logic-mcp.complexsimplicityai.com/health

# Check backend directly (internal port)
curl http://localhost:8002/health

# Check database connection
docker exec wolf-gateway-server-a psql -h 100.110.82.181 -p 5433 -U wolf -d wolf_logic -c "SELECT 1"
```

### Load balancer issues
```bash
# Check HAProxy config
docker exec wolf-loadbalancer cat /usr/local/etc/haproxy/haproxy.cfg

# Test backend connectivity
docker exec wolf-loadbalancer curl http://wolf-gateway-a:8001/health
docker exec wolf-loadbalancer curl http://wolf-gateway-b:8002/health
```

### NFS mount issues
```bash
# Verify mount
df -h | grep Wolf-code

# Check permissions
ls -la /mnt/Wolf-code/Wolf-Ai-Enterptises/data/conversations/
```

## Production Checklist

- [ ] Both servers deployed and healthy
- [ ] HAProxy load balancer running
- [ ] Health checks passing every 5s
- [ ] NFS storage mounted on both servers
- [ ] PostgreSQL connection pooling configured
- [ ] OAuth tokens validated against Authentik
- [ ] Client SDK tested with failover scenarios
- [ ] Monitoring dashboards configured
- [ ] Backup strategy implemented
- [ ] Rolling update procedure tested
- [ ] Network firewall rules applied
- [ ] SSL/TLS certificates installed (if public)

## Next Steps

1. **Geographic Distribution**: Deploy Server B to different data center
2. **Auto-scaling**: Add more servers dynamically based on load
3. **CDN Integration**: Cache static assets closer to clients
4. **Database Replication**: PostgreSQL read replicas for scaling
5. **Message Queue**: Add Redis/RabbitMQ for async processing
