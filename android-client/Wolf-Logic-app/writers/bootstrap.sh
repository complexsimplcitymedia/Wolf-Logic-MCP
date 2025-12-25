#!/data/data/com.termux/files/usr/bin/bash

# Wolf Bridge - Personal Intelligence Node Bootstrap
# Version: 1.0.0-beta
# This script initializes the local infrastructure required for the Wolf Bridge Mobile App.

set -e

# Terminal Colors
GREEN='\033[1;32m'
BLUE='\033[1;34m'
RED='\033[1;31m'
NC='\033[0m'

echo -e "${GREEN}[WOLF BRIDGE] Starting Infrastructure Deployment...${NC}"

# 1. Environment Preparation
echo -e "\n${BLUE}[1/4] Preparing Termux environment...${NC}"
pkg update -y && pkg upgrade -y
pkg install -y postgresql termux-services wget curl git ollama nodejs-lts

# 2. PostgreSQL 17 Initialization
echo -e "\n${BLUE}[2/4] Initializing Memory Core (PostgreSQL 17)...${NC}"
if [ ! -d "$PREFIX/var/lib/postgresql" ]; then
    initdb "$PREFIX/var/lib/postgresql"
    echo "Memory core initialized."
else
    echo "Memory core already exists."
fi

# Start services
sv-enable postgresql
sv-enable ollama

# Wait for DB
echo "Waking up database..."
until pg_isready -h localhost; do sleep 1; done

# Setup Wolf Database
echo "Configuring sovereign storage..."
psql -h localhost postgres -c "CREATE USER wolf WITH PASSWORD 'wolflogic2024';" || true
psql -h localhost postgres -c "CREATE DATABASE wolf_local OWNER wolf;" || true

# 3. Vector Engine Setup
echo -e "\n${BLUE}[3/4] Installing pgvector extension...${NC}"
# Attempting to compile pgvector if not in pkg
if ! psql -h localhost -d wolf_local -c "CREATE EXTENSION IF NOT EXISTS vector;" 2>/dev/null; then
    echo "Building vector extension from source..."
    pkg install -y build-essential clang make
    git clone --branch v0.8.0 https://github.com/pgvector/pgvector.git /tmp/pgvector
    cd /tmp/pgvector && make && make install
    psql -h localhost -d wolf_local -c "CREATE EXTENSION IF NOT EXISTS vector;"
fi

# 4. Cognitive Model Download (Nomic 768)
echo -e "\n${BLUE}[4/4] Loading Nomic Cognitive Engine (768-dim)...${NC}"
until curl -s http://localhost:11434/api/tags > /dev/null; do sleep 2; done
ollama pull nomic-embed-text

# 5. AI CLI & Bridge Installation
TARGET_DIR="$HOME/wolf-intelligence"
mkdir -p "$TARGET_DIR"
echo -e "\n${BLUE}[5/5] Deploying AI Communication Bridge (jspybridge)...${NC}"

cd "$TARGET_DIR"
git clone https://github.com/the-asura/jspybridge.git || echo "Bridge source already exists."
cd jspybridge/src/javascript/js/
npm install

echo -e "\n${BLUE}[6/6] Finalizing AI CLI infrastructure...${NC}"
# ... (rest of model selection logic) ...

echo -e "\n${GREEN}[SUCCESS] WOLF INTELLIGENCE NODE IS ONLINE.${NC}"
echo -e "Your local infrastructure is configured and bridged."
echo -e "You can now return to the app."
