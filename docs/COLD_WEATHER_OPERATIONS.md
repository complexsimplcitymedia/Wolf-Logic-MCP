# Cold Weather Operations Guide

**Last Updated:** 2025-12-25  
**Applies To:** Wolf Logic MCP Infrastructure  
**Critical:** Server Hardware & Environmental Monitoring

---

## Overview

This guide addresses operational considerations for the Wolf Logic MCP infrastructure during cold weather conditions. Cold weather can significantly impact hardware performance, reliability, and safety.

---

## Infrastructure at Risk

### Primary Production Server (csmcloud-server)
- **Location:** `100.110.82.181`
- **GPU:** AMD RX 7900 XT (21.4GB VRAM)
- **Critical Services:**
  - PostgreSQL (wolf_logic) on port 5433
  - Ollama embedding fleet
  - Neo4j graph database
  - Memory API
  - Prometheus/Grafana monitoring

### Development Machine (Wolfbook)
- **Location:** `100.110.82.245`
- **Services:**
  - Caddy reverse proxy
  - Docker MCP Gateway
  - Portainer

---

## Cold Weather Risks

### 1. **Condensation & Moisture**
- **Risk:** Water damage from condensation when bringing cold equipment into warm spaces
- **Critical Temp Range:** Below 32°F (0°C)
- **Impact:** Short circuits, corrosion, data loss

### 2. **Hardware Startup Issues**
- **Risk:** Hard drives, SSDs may fail to spin up or initialize properly
- **Critical Temp Range:** Below 40°F (4°C)
- **Impact:** Boot failures, data unavailability

### 3. **Battery Performance Degradation**
- **Risk:** UPS and backup batteries lose capacity in cold
- **Critical Temp Range:** Below 50°F (10°C)
- **Impact:** Reduced backup power, unexpected shutdowns

### 4. **GPU Thermal Shock**
- **Risk:** Rapid temperature changes can damage GPU components
- **GPU at Risk:** AMD RX 7900 XT
- **Impact:** Compute failures, memory errors, permanent damage

### 5. **Network Equipment**
- **Risk:** Tailscale mesh network interruptions
- **Impact:** Loss of remote access, service unavailability

---

## Pre-Cold Weather Checklist

### Before Temperature Drops

- [ ] **Verify UPS battery health**
  ```bash
  # Check UPS status if available
  upsc ups-name@localhost
  ```

- [ ] **Test backup power systems**
  - Simulate power loss
  - Verify graceful shutdown procedures
  - Test automatic restart

- [ ] **Document current system temperatures**
  ```bash
  # CPU temperature
  sensors
  
  # GPU temperature (AMD)
  rocm-smi --showtemp
  
  # Drive temperatures
  sudo smartctl -A /dev/sda | grep Temperature
  ```

- [ ] **Verify heating/environmental controls**
  - Check server room/area heating
  - Set temperature alarms if available
  - Minimum safe temperature: 50°F (10°C)

- [ ] **Update emergency contact list**
  - Include phone numbers for remote restart procedures
  - Document physical access procedures

- [ ] **Test Tailscale connectivity**
  ```bash
  tailscale status
  tailscale ping 100.110.82.181
  ```

---

## Cold Weather Operating Procedures

### Daily Operations (When Temp < 50°F / 10°C)

1. **Morning System Check**
   ```bash
   # Check all critical services
   systemctl status postgresql@14-main
   docker ps
   tailscale status
   
   # Verify GPU temperature
   rocm-smi --showtemp
   ```

2. **Monitor Temperature Trends**
   - Check ambient temperature every 4 hours
   - Log system temperatures to Prometheus
   - Alert if ambient temp drops below 45°F (7°C)

3. **Verify Database Integrity**
   ```bash
   # PostgreSQL health check
   PGPASSWORD=wolflogic2024 psql -h 100.110.82.181 -p 5433 -U wolf -d wolf_logic \
     -c "SELECT COUNT(*) as total_memories FROM memories;"
   ```

4. **Check Memory System Status**
   ```bash
   # Verify embedding system is operational
   curl -s http://localhost:5000/health
   ```

### Startup Procedure (Cold Start)

**When bringing equipment online after exposure to cold (<40°F / 4°C):**

1. **Gradual Warming (CRITICAL)**
   - Do NOT power on immediately
   - Allow hardware to warm to room temperature
   - Wait minimum 2-3 hours in warm environment
   - Prevents condensation damage

2. **Visual Inspection**
   - Check for condensation on components
   - Look for ice crystals around vents
   - Verify no moisture on PCBs
   - Check cable connections are dry

3. **Controlled Power-On**
   ```bash
   # Start with basic services first
   sudo systemctl start postgresql@14-main
   
   # Wait 2 minutes, verify stability
   sleep 120
   
   # Start Docker services
   sudo systemctl start docker
   
   # Wait and verify
   docker ps
   
   # Start GPU-dependent services last
   docker start <ollama-container-name>
   ```

4. **Temperature Monitoring**
   ```bash
   # Monitor for first 30 minutes
   watch -n 60 'sensors && echo "---GPU---" && rocm-smi --showtemp'
   ```

5. **Service Verification**
   - Test database connections
   - Verify Ollama embedding generation
   - Check Neo4j graph queries
   - Test Memory API endpoints

### Shutdown Procedure (Pre-Cold Exposure)

**When temperatures are expected to drop below 40°F (4°C) and heating is unavailable:**

1. **Graceful Service Shutdown**
   ```bash
   # Stop all Docker containers gracefully
   docker stop $(docker ps -q)
   
   # Stop database
   sudo systemctl stop postgresql@14-main
   
   # Stop monitoring
   sudo systemctl stop prometheus grafana-server
   ```

2. **GPU Shutdown**
   ```bash
   # Verify no GPU processes running
   rocm-smi --showpids
   
   # Allow GPU to cool down (if was under load)
   sleep 300
   ```

3. **System Shutdown**
   ```bash
   sudo shutdown -h now
   ```

4. **Physical Protection** (if possible)
   - Cover equipment with insulating material
   - Seal vents to prevent moisture entry
   - Place desiccant packs near equipment
   - Document shutdown time and temperature

---

## Temperature Monitoring & Alerts

### Prometheus Queries

Add these queries to Grafana for cold weather monitoring:

```promql
# System temperature alert
node_hwmon_temp_celsius{chip="platform_coretemp_0"} < 10

# GPU temperature monitoring
amdgpu_gpu_temperature_celsius < 15

# Drive temperature warning
smartmon_temperature_celsius_raw_value < 5
```

### Alert Rules

Create `/etc/prometheus/rules/cold_weather.yml`:

```yaml
groups:
  - name: cold_weather_alerts
    interval: 60s
    rules:
      - alert: AmbientTempCritical
        expr: node_hwmon_temp_celsius < 10
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Ambient temperature critically low"
          description: "Temperature below 10°C detected"
      
      - alert: GPUTempLow
        expr: amdgpu_gpu_temperature_celsius < 15
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "GPU temperature low"
          description: "GPU below safe operating temperature"
```

### Manual Temperature Logging

```bash
#!/bin/bash
# Save as: /usr/local/bin/log_temps.sh

LOGFILE="/var/log/wolf-logic/temperature_log.txt"

echo "$(date '+%Y-%m-%d %H:%M:%S') - System Temperature Check" >> $LOGFILE
sensors | grep -E 'Core|temp' >> $LOGFILE
rocm-smi --showtemp >> $LOGFILE 2>&1
echo "---" >> $LOGFILE
```

Run every hour:
```bash
crontab -e
# Add: 0 * * * * /usr/local/bin/log_temps.sh
```

---

## Remote Recovery Procedures

### If Server Becomes Unresponsive in Cold Weather

1. **Check Tailscale Connectivity**
   ```bash
   tailscale ping 100.110.82.181
   ```

2. **Attempt SSH Recovery**
   ```bash
   ssh user@100.110.82.181
   # If no response, hardware is likely offline
   ```

3. **Physical Access Required**
   - Contact person with physical access
   - Follow cold start procedures above
   - Document incident for post-mortem

4. **Service Restart Sequence**
   ```bash
   # After physical restart, in this order:
   sudo systemctl start postgresql@14-main
   sleep 30
   sudo systemctl start docker
   sleep 30
   docker start $(docker ps -aq)
   sudo systemctl start prometheus grafana-server
   ```

---

## Hardware Protection Recommendations

### Minimum Safe Operating Temperatures

| Component | Minimum Safe Temp | Optimal Range |
|-----------|------------------|---------------|
| GPU (AMD RX 7900 XT) | 50°F (10°C) | 59-86°F (15-30°C) |
| HDDs | 41°F (5°C) | 68-77°F (20-25°C) |
| SSDs | 32°F (0°C) | 32-158°F (0-70°C) |
| CPU | 32°F (0°C) | 50-95°F (10-35°C) |
| RAM | 32°F (0°C) | 32-185°F (0-85°C) |
| PostgreSQL Data | 50°F (10°C) | 68-77°F (20-25°C) |

### Insulation Solutions

1. **Server Area Heating**
   - Space heater with thermostat
   - Set to maintain 60°F (15°C) minimum
   - Use with temperature monitoring

2. **Equipment Enclosure**
   - Insulated server rack
   - Maintain internal temperature
   - Adequate ventilation when operational

3. **Emergency Heat Retention**
   - Thermal blankets (non-conductive)
   - Styrofoam insulation around case
   - Do NOT block ventilation during operation

---

## Data Protection

### Backup Verification

Before cold weather events:

```bash
# Verify recent backups exist
ls -lah /backup/wolf_logic/
pg_dump --version

# Test backup restoration (on test system)
PGPASSWORD=wolflogic2024 pg_dump -h 100.110.82.181 -p 5433 -U wolf wolf_logic \
  | gzip > /backup/wolf_logic/cold_weather_backup_$(date +%Y%m%d).sql.gz
```

### Critical Data Locations

| Data Type | Location | Backup Frequency | Cold Weather Action |
|-----------|----------|-----------------|-------------------|
| Memories DB | PostgreSQL (100.110.82.181:5433) | Daily | Create pre-cold backup |
| Embeddings | memories_embedding_store table | Daily | Included in DB backup |
| Neo4j Graph | /var/lib/neo4j/data | Weekly | Export to JSON before cold event |
| Metrics | Prometheus TSDB | Continuous | Archive 30-day window |
| Logs | /var/log/wolf-logic/ | Daily | Sync to remote storage |

---

## Troubleshooting Cold Weather Issues

### Issue: Server Won't Boot After Cold Exposure

**Symptoms:** No POST, no video output, no SSH response

**Solution:**
1. Check ambient temperature - is it above 50°F (10°C)?
2. Allow 3+ hours of warming time
3. Check for condensation/moisture
4. Verify power supply is functioning
5. Try minimal boot (disconnect non-essential devices)
6. Check BIOS for hardware errors

### Issue: PostgreSQL Won't Start

**Symptoms:** Database connection refused, service fails to start

**Solution:**
```bash
# Check disk temperature
sudo smartctl -A /dev/sda | grep Temperature

# If temp < 50°F, wait for warming
# Check PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-14-main.log

# Verify data directory permissions
ls -la /var/lib/postgresql/14/main/

# Attempt manual start with verbose output
sudo -u postgres /usr/lib/postgresql/14/bin/postgres -D /var/lib/postgresql/14/main/
```

### Issue: GPU Not Detected After Cold Start

**Symptoms:** `rocm-smi` shows no devices, Ollama can't access GPU

**Solution:**
```bash
# Check GPU detection
lspci | grep -i amd

# Verify ROCm drivers loaded
lsmod | grep amdgpu

# Check GPU temperature (if detected)
rocm-smi --showtemp

# If temp < 60°F and recently powered on:
# Wait 15 minutes for GPU to warm up
# Restart GPU-dependent services:
docker restart <ollama-container>
```

### Issue: Network Drops / Tailscale Disconnection

**Symptoms:** Can't reach 100.110.82.* IPs, Tailscale shows offline

**Solution:**
```bash
# Check Tailscale status
tailscale status

# Restart Tailscale
sudo systemctl restart tailscaled

# Verify network interfaces
ip addr show

# Check for hardware network adapter issues
ethtool eth0 | grep "Link detected"

# Cold weather can affect WiFi - use wired connection if possible
```

### Issue: Memory API Slow/Unresponsive

**Symptoms:** `/health` endpoint times out, embedding generation slow

**Solution:**
```bash
# Check service status
systemctl status wolf-memory-api

# Verify database connection
PGPASSWORD=wolflogic2024 psql -h 100.110.82.181 -p 5433 -U wolf -d wolf_logic \
  -c "SELECT 1;"

# Check GPU availability for embeddings
docker exec <ollama-container> rocm-smi

# Review API logs
sudo journalctl -u wolf-memory-api -f
```

---

## Emergency Contacts & Procedures

### Physical Access Required

**Primary Contact:** [Physical location access person]  
**Phone:** [Phone number]  
**Address:** [Server physical location]

### Remote Support

**Tailscale Admin:** [Admin email]  
**Infrastructure Lead:** [Contact info]

### Escalation Path

1. **Level 1:** Automated monitoring alerts
2. **Level 2:** Remote recovery attempt via SSH
3. **Level 3:** Contact for physical intervention
4. **Level 4:** Emergency hardware replacement

---

## Post-Cold Weather Recovery Checklist

After cold weather event and service restoration:

- [ ] Verify all services running: `docker ps`, `systemctl status postgresql`
- [ ] Check database integrity: Run PostgreSQL VACUUM ANALYZE
- [ ] Verify memory count: Should match pre-cold count (30,403+)
- [ ] Test embedding generation: Submit test memory via API
- [ ] Check Neo4j graph: Run test Cypher queries
- [ ] Review system logs for errors during cold period
- [ ] Document any hardware issues discovered
- [ ] Update this guide with lessons learned
- [ ] Schedule hardware inspection if issues detected

---

## Additional Resources

- **Network Architecture:** See `docs/NETWORK_ARCHITECTURE.md`
- **Memory System:** See `docs/MEMORY_INFRASTRUCTURE_WHITEPAPER.md`
- **Database Access:** See `README.md` - Database Access section
- **Monitoring:** Grafana dashboard at `http://100.110.82.181:3000`

---

## Maintenance Schedule

### Cold Weather Season (Nov-Mar)

- **Daily:** Temperature checks, service status verification
- **Weekly:** Backup verification, test recovery procedures
- **Monthly:** Hardware inspection, update documentation
- **End of Season:** Full system review, document improvements

---

## Document Revision History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-12-25 | 1.0 | Initial cold weather operations guide | Copilot Agent |

---

**CRITICAL REMINDER:** When ambient temperature drops below 50°F (10°C), increase monitoring frequency. Below 40°F (4°C), consider controlled shutdown to protect hardware.
