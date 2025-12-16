#!/bin/bash
# DataGrip Crash Troubleshooting

echo "=== DataGrip Crash Recovery ==="
echo ""
echo "1. Clear all lock files and caches:"
rm -rf ~/.config/JetBrains/DataGrip2025.2/.lock
rm -rf ~/.cache/JetBrains/DataGrip2025.2/tmp/*
rm -rf ~/.local/share/JetBrains/DataGrip2025.2/tmp/*
find /tmp -name "*DataGrip*" -delete 2>/dev/null
echo "   ✓ Cleared"

echo ""
echo "2. Kill any stuck processes:"
pkill -9 -f "datagrip" 2>/dev/null
pkill -9 -f "DataGrip" 2>/dev/null
echo "   ✓ Killed"

echo ""
echo "3. Check if DataGrip is a Flatpak:"
flatpak list | grep -i jetbrains || echo "   Not installed via Flatpak"

echo ""
echo "4. Alternative: Use psql command line directly:"
echo "   PGPASSWORD=wolflogic2024 psql -h 127.0.0.1 -p 5433 -U wolf -d wolf_logic"
echo ""

echo "5. Alternative: Use web-based pgAdmin:"
echo "   docker run -p 5050:80 -e 'PGADMIN_DEFAULT_EMAIL=wolf@localhost' -e 'PGADMIN_DEFAULT_PASSWORD=wolflogic2024' -d dpage/pgadmin4"
echo "   Then open: http://localhost:5050"
echo ""

echo "6. If DataGrip keeps crashing, reinstall:"
echo "   - Download fresh from: https://www.jetbrains.com/datagrip/download/"
echo "   - Or use snap: sudo snap install datagrip --classic"
echo ""
