# Cold Weather Monitoring Setup

Quick setup guide for enabling automated cold weather monitoring on Wolf Logic MCP infrastructure.

## Prerequisites

- Root/sudo access to the server
- Git repository cloned to `/opt/Wolf-Logic-MCP` (or adjust paths)
- Required packages: `lm-sensors`, `smartmontools`, `bc`

## Installation Steps

### 1. Install Required Packages

```bash
# Update package list
sudo apt update

# Install monitoring tools
sudo apt install -y lm-sensors smartmontools bc

# Configure sensors (answer YES to all prompts)
sudo sensors-detect

# Test sensors
sensors
```

### 2. Create Log Directory

```bash
sudo mkdir -p /var/log/wolf-logic
sudo chown $USER:$USER /var/log/wolf-logic
```

### 3. Test the Monitoring Script

```bash
# Navigate to repository
cd /opt/Wolf-Logic-MCP

# Run the check script
sudo ./scripts/check_cold_weather_status.sh
```

### 4. Install Systemd Service (Optional - Automated Monitoring)

```bash
# Update the service file path
sudo sed -i 's|/path/to/Wolf-Logic-MCP|/opt/Wolf-Logic-MCP|g' \
  /opt/Wolf-Logic-MCP/server-configuration/systemd/cold-weather-monitor.service

# Copy service and timer to systemd
sudo cp /opt/Wolf-Logic-MCP/server-configuration/systemd/cold-weather-monitor.service \
  /etc/systemd/system/

sudo cp /opt/Wolf-Logic-MCP/server-configuration/systemd/cold-weather-monitor.timer \
  /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start the timer (runs every 4 hours)
sudo systemctl enable cold-weather-monitor.timer
sudo systemctl start cold-weather-monitor.timer

# Check timer status
sudo systemctl status cold-weather-monitor.timer
```

### 5. Manual Monitoring (Alternative to Systemd)

Add to crontab for hourly checks:

```bash
crontab -e

# Add this line:
0 * * * * /opt/Wolf-Logic-MCP/scripts/check_cold_weather_status.sh >> /var/log/wolf-logic/cold_weather_check.log 2>&1
```

## Verification

### Check Timer Status

```bash
# View timer schedule
systemctl list-timers cold-weather-monitor.timer

# View recent logs
journalctl -u cold-weather-monitor.service -n 50
```

### View Log File

```bash
tail -f /var/log/wolf-logic/cold_weather_check.log
```

## Uninstall

```bash
# Stop and disable timer
sudo systemctl stop cold-weather-monitor.timer
sudo systemctl disable cold-weather-monitor.timer

# Remove systemd files
sudo rm /etc/systemd/system/cold-weather-monitor.service
sudo rm /etc/systemd/system/cold-weather-monitor.timer

# Reload systemd
sudo systemctl daemon-reload

# Remove cron job (if using cron instead)
crontab -e
# Delete the cold weather monitoring line
```

## Troubleshooting

### Script Permission Denied

```bash
chmod +x /opt/Wolf-Logic-MCP/scripts/check_cold_weather_status.sh
```

### Sensors Not Working

```bash
# Re-run sensor detection
sudo sensors-detect

# Load kernel modules
sudo modprobe coretemp
sudo modprobe drivetemp

# Test again
sensors
```

### GPU Temperature Not Available

```bash
# Check if ROCm is installed
rocm-smi --version

# If not installed, install ROCm drivers
# See: https://rocmdocs.amd.com/en/latest/Installation_Guide/Installation-Guide.html
```

### PostgreSQL Connection Failed

```bash
# Check if PostgreSQL is running
systemctl status postgresql

# Test connection manually
PGPASSWORD=wolflogic2024 psql -h 100.110.82.181 -p 5433 -U wolf -d wolf_logic -c "SELECT 1;"

# Check Tailscale connectivity
tailscale status
```

## Configuration

### Adjust Temperature Thresholds

Edit `/opt/Wolf-Logic-MCP/scripts/check_cold_weather_status.sh`:

```bash
# Temperature thresholds (in Celsius)
CRITICAL_TEMP=10  # Change to your critical threshold
WARNING_TEMP=15   # Change to your warning threshold
SAFE_TEMP=20      # Change to your safe threshold
```

### Change Monitoring Frequency

Edit `/etc/systemd/system/cold-weather-monitor.timer`:

```ini
[Timer]
OnBootSec=5min
OnUnitActiveSec=2h  # Change from 4h to desired interval
```

Then reload:
```bash
sudo systemctl daemon-reload
sudo systemctl restart cold-weather-monitor.timer
```

## Additional Resources

- **Full Operations Guide:** [docs/COLD_WEATHER_OPERATIONS.md](../docs/COLD_WEATHER_OPERATIONS.md)
- **Network Architecture:** [docs/NETWORK_ARCHITECTURE.md](../docs/NETWORK_ARCHITECTURE.md)
- **Main README:** [README.md](../README.md)

## Support

For issues or questions:
1. Check the logs: `/var/log/wolf-logic/cold_weather_check.log`
2. Review the operations guide: `docs/COLD_WEATHER_OPERATIONS.md`
3. Check service status: `systemctl status cold-weather-monitor.service`
