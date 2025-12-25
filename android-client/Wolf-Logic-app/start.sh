#!/bin/bash
# Complex Logic App Starter
# Frontend: port 8083
# Backend: port 8084

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║              🧠 COMPLEX LOGIC APP STARTER                    ║"
echo "╚═══════════════════════════════════════════════════════════╝"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Start backend in background
echo "🚀 Starting Backend API on port 2500..."
python3 backend.py &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"

sleep 2

# Start frontend
echo "🚀 Starting Frontend on port 3333..."
cd wolf-ui
npm start &
FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID"

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  Frontend:  http://localhost:8083                         ║"
echo "║  Backend:   http://localhost:8084                         ║"
echo "║  API Docs:  http://localhost:8084/api/health              ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "Press Ctrl+C to stop both services..."

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM
wait
