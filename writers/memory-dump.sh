#!/bin/bash
# Memory Dump Hook - Triggered by PreCompact
# Saves conversation history before context compaction

DUMP_DIR="/mnt/Wolf-code/Wolf-Ai-Enterptises/memory-dumps"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DUMP_FILE="$DUMP_DIR/conversation_${TIMESTAMP}.txt"

# Ensure dump directory exists
mkdir -p "$DUMP_DIR"

# Read conversation from stdin (Claude Code provides this via hook)
cat > "$DUMP_FILE"

# Log the dump
echo "[$(date)] Dumped conversation to $DUMP_FILE ($(wc -l < "$DUMP_FILE") lines)" >> "$DUMP_DIR/dump.log"

# Trigger librarian fleet to process
if [ -f "/mnt/Wolf-code/Wolf-Ai-Enterptises/writers/retrieval/librarian_fleet.py" ]; then
    nohup python3 /mnt/Wolf-code/Wolf-Ai-Enterptises/writers/retrieval/librarian_fleet.py >> "$DUMP_DIR/librarian.log" 2>&1 &
fi

exit 0
