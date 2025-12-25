#!/bin/bash
#
# Cold Weather Status Check Script
# Monitors system temperatures and service health during cold weather
#
# Usage: ./check_cold_weather_status.sh
#

set -e

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo "========================================"
echo "Wolf Logic MCP - Cold Weather Status"
echo "========================================"
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Temperature thresholds (in Celsius)
CRITICAL_TEMP=10
WARNING_TEMP=15
SAFE_TEMP=20

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to get temperature status
get_temp_status() {
    local temp=$1
    if (( $(echo "$temp < $CRITICAL_TEMP" | bc -l) )); then
        echo "CRITICAL"
    elif (( $(echo "$temp < $WARNING_TEMP" | bc -l) )); then
        echo "WARNING"
    elif (( $(echo "$temp < $SAFE_TEMP" | bc -l) )); then
        echo "CAUTION"
    else
        echo "SAFE"
    fi
}

# Function to print colored status
print_status() {
    local status=$1
    local value=$2
    case $status in
        CRITICAL)
            echo -e "${RED}$status${NC} - $value"
            ;;
        WARNING)
            echo -e "${YELLOW}$status${NC} - $value"
            ;;
        CAUTION)
            echo -e "${YELLOW}$status${NC} - $value"
            ;;
        SAFE)
            echo -e "${GREEN}$status${NC} - $value"
            ;;
        *)
            echo "$status - $value"
            ;;
    esac
}

echo "--- SYSTEM TEMPERATURES ---"

# Check CPU temperature using sensors
if command_exists sensors; then
    echo ""
    echo "CPU Temperatures:"
    CPU_TEMPS=$(sensors | grep -E 'Core|temp' || echo "Unable to read CPU temps")
    echo "$CPU_TEMPS"
    
    # Extract average CPU temp if available
    AVG_TEMP=$(sensors | grep "Package id 0:" | awk '{print $4}' | sed 's/[+°C]//g' || echo "")
    if [ -n "$AVG_TEMP" ]; then
        STATUS=$(get_temp_status "$AVG_TEMP")
        print_status "$STATUS" "Average CPU: ${AVG_TEMP}°C"
    fi
else
    echo "sensors command not found. Install lm-sensors."
fi

# Check GPU temperature using rocm-smi
echo ""
if command_exists rocm-smi; then
    echo "GPU Temperature (AMD RX 7900 XT):"
    GPU_OUTPUT=$(rocm-smi --showtemp 2>&1 || echo "Unable to read GPU temps")
    echo "$GPU_OUTPUT"
    
    # Extract GPU temp
    GPU_TEMP=$(echo "$GPU_OUTPUT" | grep -oP '\d+\.\d+c' | head -1 | sed 's/c//' || echo "")
    if [ -n "$GPU_TEMP" ]; then
        STATUS=$(get_temp_status "$GPU_TEMP")
        print_status "$STATUS" "GPU: ${GPU_TEMP}°C"
    fi
else
    echo "rocm-smi not found. GPU temperature unavailable."
fi

# Check drive temperatures
echo ""
if command_exists smartctl; then
    echo "Drive Temperatures:"
    for drive in /dev/sd[a-z]; do
        if [ -e "$drive" ]; then
            DRIVE_NAME=$(basename "$drive")
            DRIVE_TEMP=$(sudo smartctl -A "$drive" 2>/dev/null | grep "Temperature_Celsius" | awk '{print $10}' || echo "")
            if [ -n "$DRIVE_TEMP" ]; then
                STATUS=$(get_temp_status "$DRIVE_TEMP")
                print_status "$STATUS" "$DRIVE_NAME: ${DRIVE_TEMP}°C"
            fi
        fi
    done
else
    echo "smartctl not found. Install smartmontools for drive temps."
fi

echo ""
echo "--- SERVICE STATUS ---"
echo ""

# Check critical services
services=(
    "postgresql@14-main:PostgreSQL Database"
    "docker:Docker Service"
    "tailscaled:Tailscale VPN"
)

for service_info in "${services[@]}"; do
    IFS=':' read -r service_name service_desc <<< "$service_info"
    
    if systemctl is-active --quiet "$service_name" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $service_desc ($service_name): Running"
    else
        echo -e "${RED}✗${NC} $service_desc ($service_name): Not Running"
    fi
done

# Check Docker containers
echo ""
echo "Docker Containers:"
if command_exists docker; then
    RUNNING_CONTAINERS=$(docker ps --format "{{.Names}}" 2>/dev/null | wc -l)
    TOTAL_CONTAINERS=$(docker ps -a --format "{{.Names}}" 2>/dev/null | wc -l)
    echo "Running: $RUNNING_CONTAINERS / $TOTAL_CONTAINERS"
    
    if [ "$RUNNING_CONTAINERS" -lt "$TOTAL_CONTAINERS" ]; then
        echo -e "${YELLOW}Some containers are not running${NC}"
        docker ps -a --filter "status=exited" --format "  - {{.Names}} ({{.Status}})" 2>/dev/null
    fi
else
    echo "Docker not available"
fi

echo ""
echo "--- DATABASE STATUS ---"
echo ""

# Check PostgreSQL connection
# Note: Configure ~/.pgpass for password-less authentication
# Format: hostname:port:database:username:password
# Or use environment variable: export PGPASSWORD=your_password
if command_exists psql; then
    # Try to use .pgpass or environment variable for authentication
    if psql -h 100.110.82.181 -p 5433 -U wolf -d wolf_logic -c "SELECT 1" >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} PostgreSQL: Connection successful"
        
        # Get memory count
        MEMORY_COUNT=$(psql -h 100.110.82.181 -p 5433 -U wolf -d wolf_logic -t -c "SELECT COUNT(*) FROM memories;" 2>/dev/null | tr -d ' ')
        if [ -n "$MEMORY_COUNT" ]; then
            echo "  Memories in database: $MEMORY_COUNT"
        fi
    else
        echo -e "${RED}✗${NC} PostgreSQL: Connection failed"
        echo "  Check if database is running and accessible"
        echo "  Ensure ~/.pgpass is configured or PGPASSWORD environment variable is set"
    fi
else
    echo "psql not found. Cannot check database."
fi

echo ""
echo "--- NETWORK STATUS ---"
echo ""

# Check Tailscale
if command_exists tailscale; then
    if tailscale status >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Tailscale: Connected"
        
        # Test ping to production server
        if timeout 2 tailscale ping 100.110.82.181 -c 1 >/dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} Server (100.110.82.181): Reachable"
        else
            echo -e "${RED}✗${NC} Server (100.110.82.181): Unreachable"
        fi
        
        # Test ping to MacBook
        if timeout 2 tailscale ping 100.110.82.245 -c 1 >/dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} MacBook (100.110.82.245): Reachable"
        else
            echo -e "${YELLOW}!${NC} MacBook (100.110.82.245): Unreachable"
        fi
    else
        echo -e "${RED}✗${NC} Tailscale: Not connected"
    fi
else
    echo "Tailscale not found"
fi

echo ""
echo "--- RECOMMENDATIONS ---"
echo ""

# Generate recommendations based on temperatures
if command_exists sensors; then
    AVG_TEMP=$(sensors | grep "Package id 0:" | awk '{print $4}' | sed 's/[+°C]//g' 2>/dev/null || echo "")
    if [ -n "$AVG_TEMP" ]; then
        if (( $(echo "$AVG_TEMP < $CRITICAL_TEMP" | bc -l) )); then
            echo -e "${RED}⚠ CRITICAL: Temperature below 10°C${NC}"
            echo "  → Consider controlled shutdown to protect hardware"
            echo "  → See: docs/COLD_WEATHER_OPERATIONS.md - Shutdown Procedure"
        elif (( $(echo "$AVG_TEMP < $WARNING_TEMP" | bc -l) )); then
            echo -e "${YELLOW}⚠ WARNING: Temperature below 15°C${NC}"
            echo "  → Increase monitoring frequency"
            echo "  → Verify heating is adequate"
            echo "  → Prepare for potential shutdown"
        elif (( $(echo "$AVG_TEMP < $SAFE_TEMP" | bc -l) )); then
            echo -e "${YELLOW}ℹ CAUTION: Temperature below 20°C${NC}"
            echo "  → Monitor temperature trends"
            echo "  → Normal operations can continue"
        else
            echo -e "${GREEN}✓ Temperature within safe operating range${NC}"
        fi
    fi
fi

echo ""
echo "========================================"
echo "For detailed cold weather procedures, see:"
echo "docs/COLD_WEATHER_OPERATIONS.md"
echo "========================================"
