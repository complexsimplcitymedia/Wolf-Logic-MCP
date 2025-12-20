#!/bin/bash
# Librarian Access via Gemini CLI - Natural Language Database Queries
# Run this to start a Gemini session with PostgreSQL access to the Librarian

# Set PostgreSQL connection (Librarian - wolf_logic database)
export POSTGRES_HOST=100.110.82.181
export POSTGRES_PORT=5433
export POSTGRES_DATABASE=wolf_logic
export POSTGRES_USER=wolf
export POSTGRES_PASSWORD=wolflogic2024

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║         LIBRARIAN ACCESS - GEMINI CLI                     ║"
echo "║         Natural Language → PostgreSQL Queries             ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "Database: wolf_logic @ 100.110.82.181:5433"
echo "Total Memories: 97,017"
echo "Namespaces: scripty, wolf_story, ingested, wolf_hunt, etc."
echo ""
echo "Example queries:"
echo "  • List all tables in the database"
echo "  • Show me the 10 most recent memories from the scripty namespace"
echo "  • How many jobs are in the wolf_hunt namespace?"
echo "  • What are the column names in the memories table?"
echo "  • Execute: SELECT namespace, COUNT(*) FROM memories GROUP BY namespace"
echo ""
echo "Starting Gemini CLI with PostgreSQL extension..."
echo ""

# Launch Gemini CLI in interactive mode
gemini
