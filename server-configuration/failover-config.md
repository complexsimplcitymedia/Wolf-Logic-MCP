# Failover Configuration - 181 → 250

## Architecture

**Primary Gateway:** 181 (csmcloud-server)
**Backup Gateway:** 250 (debian-wolf-logic-node)

When 181 goes offline, 250 becomes the entry point.

## Components Requiring Failover

### 1. Tailscale Exit Node (250)

**Enable exit node on 250:**
```bash
# On 250
sudo tailscale up --advertise-exit-node
```

**Approve in Tailscale admin:**
- Go to https://login.tailscale.com/admin/machines
- Find 250 (debian-wolf-logic-node)
- Approve as exit node

**Auto-route when 181 offline:**
Client devices detect 181 down → switch to 250 exit node

### 2. PostgreSQL Failover

**Option A: Connection String Failover (Simplest)**

Update all clients to use failover connection:
```bash
# Multi-host connection string
psql "host=100.110.82.181,100.110.82.250 port=5433 dbname=wolf_logic user=wolf"
```

PostgreSQL client tries 181 first, falls back to 250 if offline.

**Option B: PostgreSQL Replication (More Complex)**

Set up streaming replication 181 → 250:
1. Primary: 181 (read/write)
2. Standby: 250 (read-only, becomes primary when 181 fails)

**Requirement:** PostgreSQL on 250 must be running and have replicated data.

### 3. MCP Gateway on 250

Deploy MCP Gateway container on 250:

```bash
# Copy from Mac to 250
scp -r /Users/apexwolf/Wolf-Logic-MCP/mcp-gateway/ user@100.110.82.250:/tmp/

# On 250
cd /tmp/mcp-gateway
docker-compose up -d
```

Gateway accessible at: `http://100.110.82.250:8080`

**Client failover:**
```python
gateways = [
    "http://100.110.82.181:8080",  # Primary
    "http://100.110.82.250:8080"   # Backup
]

for gateway in gateways:
    try:
        response = requests.post(f"{gateway}/health", timeout=5)
        if response.ok:
            # Use this gateway
            break
    except:
        continue  # Try next gateway
```

### 4. Ollama (llama3.1-claude)

**Option A:** Run Ollama on 250 with same models
**Option B:** Wolf Intelligence queries failover to 250's Ollama

```swift
// Swift failover
let ollamaEndpoints = [
    "http://100.110.82.181:11434",
    "http://100.110.82.250:11434"
]
```

## Health Check Script

**Monitor 181, trigger failover when down:**

```python
#!/usr/bin/env python3
# /usr/local/bin/check_181_health.py

import requests
import subprocess
import time

PRIMARY = "100.110.82.181"
BACKUP = "100.110.82.250"

def check_health(host):
    try:
        # Check PostgreSQL
        result = subprocess.run(
            ["psql", f"host={host}", "port=5433", "-U", "wolf", "-d", "wolf_logic", "-c", "SELECT 1;"],
            env={"PGPASSWORD": "wolflogic2024"},
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            return True
    except:
        pass
    return False

while True:
    if not check_health(PRIMARY):
        print(f"⚠️  {PRIMARY} is DOWN - Failover to {BACKUP}")
        # Trigger failover actions here
        # e.g., update DNS, send alerts, etc.
    else:
        print(f"✓ {PRIMARY} is UP")

    time.sleep(30)  # Check every 30 seconds
```

## DNS/Service Discovery

**Option: Use Tailscale MagicDNS + health checks**

Update service discovery to return:
- `wolf-gateway` → 181 (if up) OR 250 (if 181 down)

**Option: Kubernetes-style service:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: wolf-gateway
spec:
  selector:
    role: gateway
  endpoints:
    - 100.110.82.181:8080  # Primary
    - 100.110.82.250:8080  # Backup (only used if primary fails)
```

## Messiah Environment on 250

**Does 250 have messiah environment?**

Check:
```bash
ssh 100.110.82.250
conda env list | grep messiah
```

If not, create:
```bash
conda create -n messiah python=3.12
conda activate messiah
pip install -r requirements.txt
```

## Testing Failover

**Simulate 181 offline:**
```bash
# On 181
sudo systemctl stop postgresql
sudo systemctl stop docker  # Stops MCP Gateway
sudo systemctl stop ollama
```

**Verify clients fail over to 250:**
- PostgreSQL connections → 250:5433
- MCP Gateway → 250:8080
- Ollama → 250:11434

**Restore 181:**
```bash
sudo systemctl start postgresql
sudo systemctl start docker
sudo systemctl start ollama
```

## Implementation Priority

1. **PostgreSQL multi-host failover** (easiest, immediate benefit)
2. **MCP Gateway on 250** (critical for Gemini access)
3. **Tailscale exit node on 250** (network-level failover)
4. **Ollama on 250** (if Wolf Intelligence needs it)
5. **Health monitoring script** (automated failover detection)

## Current Status

- 181: Gateway, PostgreSQL, Ollama, MCP Gateway (Mac) ✓
- 250: Tailscale node ✓
- Failover: Not configured ✗

## Next Steps

1. SSH to 250, check if PostgreSQL is running
2. Deploy MCP Gateway to 250
3. Configure multi-host connection strings
4. Enable Tailscale exit node on 250
5. Test failover by stopping services on 181
