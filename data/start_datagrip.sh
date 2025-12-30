#!/bin/bash
# Start DataGrip (Flatpak) with proper setup

echo "=== Starting DataGrip ==="
echo ""

# Kill any existing instances
flatpak kill com.jetbrains.DataGrip 2>/dev/null
sleep 1

# Clear lock files
rm -rf ~/.var/app/com.jetbrains.DataGrip/config/JetBrains/DataGrip2025.2/.lock 2>/dev/null

echo "Permissions configured:"
echo "  ✓ Network access"
echo "  ✓ Filesystem access (host, /tmp, /run/postgresql)"
echo ""

echo "Starting DataGrip..."
flatpak run com.jetbrains.DataGrip &

sleep 3

echo ""
echo "=== Connection Setup ==="
echo ""
echo "Once DataGrip opens:"
echo ""
echo "1. Click 'New' (+ icon) → Data Source → PostgreSQL"
echo ""
echo "2. Connection settings:"
echo "   Host: 127.0.0.1"
echo "   Port: 5433"
echo "   Database: wolf_logic"
echo "   User: wolf"
echo "   Password: wolflogic2024"
echo "   ✓ Save password"
echo ""
echo "3. Click 'Test Connection'"
echo "   - If driver missing, click 'Download'"
echo "   - Should see: 'Succeeded'"
echo ""
echo "4. Click 'Apply' → 'OK'"
echo ""
echo "5. Expand: wolf_logic → schemas → public → tables → memories"
echo "   Right-click → 'Open Query Console'"
echo "   Run: SELECT * FROM memories LIMIT 100;"
echo ""
echo "Database contains 30,403 records across 9 namespaces"
echo ""
