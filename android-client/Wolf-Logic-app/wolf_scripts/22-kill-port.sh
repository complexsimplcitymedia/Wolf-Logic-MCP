#!/bin/bash
# Kill process on port (pass port as arg)
PORT=${1:-3333}
fuser -k ${PORT}/tcp 2>/dev/null
echo "Killed processes on port $PORT"
