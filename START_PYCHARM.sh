#!/bin/bash
# Quick launcher for PyCharm with this project

echo "Opening Wolf-Ai-Enterprises in PyCharm..."
echo ""
echo "MANUAL STEPS:"
echo "1. Open PyCharm"
echo "2. File > Open > /mnt/Wolf-code/Wolf-Ai-Enterptises"
echo "3. Set Python Interpreter: messiah env (/home/thewolfwalksalone/anaconda3/envs/messiah/bin/python)"
echo ""
echo "DATABASE INTEGRATION:"
echo "4. View > Tool Windows > Database"
echo "5. Click '+' > Data Source > PostgreSQL"
echo "6. Configure:"
echo "   Host: localhost"
echo "   Port: 5433"
echo "   Database: wolf_logic"
echo "   User: wolf"
echo "   Password: wolflogic2024"
echo "7. Test Connection > Apply"
echo ""
echo "RUN FASTAPI SERVER:"
echo "8. Right-click api/fastapi_server.py > Run 'fastapi_server'"
echo "9. Server will start on http://localhost:8000"
echo "10. Open http://localhost:8000/docs for API interface"
echo ""
echo "Project path: /mnt/Wolf-code/Wolf-Ai-Enterptises"

# Try to launch PyCharm if available
if command -v pycharm &> /dev/null; then
    pycharm /mnt/Wolf-code/Wolf-Ai-Enterptises &
elif command -v charm &> /dev/null; then
    charm /mnt/Wolf-code/Wolf-Ai-Enterptises &
else
    echo ""
    echo "PyCharm not found in PATH. Open manually."
fi
