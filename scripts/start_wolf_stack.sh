#!/bin/bash
# Start Wolf Logic Production Stack
# MCP Server + REST API for web app access

echo "🐺 Starting Wolf Logic Production Stack..."
echo ""

# Check if messiah environment exists
if [ ! -d "$HOME/anaconda3/envs/messiah" ]; then
    echo "❌ Messiah environment not found"
    exit 1
fi

# Activate messiah
source ~/anaconda3/bin/activate messiah

# Check PostgreSQL connection
echo "🔍 Checking database connection..."
PGPASSWORD=wolflogic2024 psql -h 100.110.82.181 -p 5433 -U wolf -d wolf_logic -c "SELECT 'Connection OK' as status" -t | grep -q "Connection OK"

if [ $? -ne 0 ]; then
    echo "❌ Database not accessible at 100.110.82.181:5433"
    echo "   Run: ./scripts/configure_postgres_tailscale.sh (requires FIDO2)"
    exit 1
fi

echo "✓ Database connected"
echo ""

# Start MCP Server in background
echo "🚀 Starting MCP Server (AI Agent Access)..."
cd /mnt/Wolf-code/Wolf-Ai-Enterptises/mcp-servers
nohup python postgres_mcp.py > /tmp/wolf-mcp.log 2>&1 &
MCP_PID=$!
echo "   PID: $MCP_PID"
echo "   Logs: /tmp/wolf-mcp.log"
echo ""

# Start FastAPI Server in background
echo "🚀 Starting REST API (Web App Access)..."
cd /mnt/Wolf-code/Wolf-Ai-Enterptises/api
nohup uvicorn fastapi_server:app --host 0.0.0.0 --port 8000 > /tmp/wolf-api.log 2>&1 &
API_PID=$!
echo "   PID: $API_PID"
echo "   URL: http://100.110.82.181:8000"
echo "   Docs: http://100.110.82.181:8000/docs"
echo "   Logs: /tmp/wolf-api.log"
echo ""

# Wait for servers to start
sleep 3

# Check if servers are running
if ps -p $MCP_PID > /dev/null; then
    echo "✓ MCP Server running"
else
    echo "❌ MCP Server failed to start (check /tmp/wolf-mcp.log)"
fi

if ps -p $API_PID > /dev/null; then
    echo "✓ REST API running"
else
    echo "❌ REST API failed to start (check /tmp/wolf-api.log)"
fi

echo ""
echo "🐺 Wolf Logic Stack Status:"
echo "   - Database: 100.110.82.181:5433"
echo "   - REST API: http://100.110.82.181:8000"
echo "   - Wolf Hunt: http://100.110.82.181:8033"
echo "   - MCP Server: stdio (for AI agents)"
echo ""
echo "📖 API Documentation: /mnt/Wolf-code/Wolf-Ai-Enterptises/docs/GEMINI_WEB_APP_API.md"
echo ""
echo "To stop servers:"
echo "   kill $MCP_PID $API_PID"
