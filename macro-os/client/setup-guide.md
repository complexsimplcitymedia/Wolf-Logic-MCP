# Client Setup Guide

Complete setup for Wolf Logic memory layer client. Follow every step in order. Verify after each section before proceeding.

## Prerequisites

- Linux (Ubuntu 20.04+ or Debian 11+) or macOS 12+
- Tailscale connected to Wolf Logic network
- Access to 100.110.82.181 (verify: `ping 100.110.82.181`)
- 4GB+ RAM
- 10GB+ disk space

## Step 1: Install Miniconda3

**IMPORTANT:** Use Miniconda3, NOT Anaconda3. Miniconda is minimal and sufficient.

### Linux

```bash
# Download Miniconda3
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh

# Install silently to ~/miniconda3
bash /tmp/miniconda.sh -b -p ~/miniconda3

# Initialize conda for your shell
~/miniconda3/bin/conda init bash

# Reload shell
source ~/.bashrc

# Verify
conda --version
```

**Expected output:** `conda 24.x.x` (version 24 or higher)

### macOS

```bash
# Download Miniconda3 for Apple Silicon or Intel
# Apple Silicon (M1/M2/M3):
curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh

# Intel Mac:
# curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh

# Install
bash Miniconda3-latest-MacOSX-*.sh -b -p ~/miniconda3

# Initialize
~/miniconda3/bin/conda init zsh  # or bash if using bash

# Reload shell
source ~/.zshrc

# Verify
conda --version
```

### Verification Checkpoint

```bash
which conda
# Should output: /home/youruser/miniconda3/condabin/conda (Linux)
# or: /Users/youruser/miniconda3/condabin/conda (macOS)
```

If `conda` command not found, restart your terminal or run `source ~/.bashrc` (Linux) or `source ~/.zshrc` (macOS).

## Step 2: Create Client Environment

```bash
# Create environment with Python 3.12
conda create -n client-memory python=3.12 -y

# Activate environment
conda activate client-memory

# Verify Python version
python --version
# Expected: Python 3.12.x
```

### Install Required Packages

```bash
# PostgreSQL adapter (from conda-forge for binary compatibility)
conda install -c conda-forge psycopg2 -y

# Python packages via pip
pip install ollama requests pydantic

# Verify installations
python -c "import psycopg2; print('psycopg2:', psycopg2.__version__)"
python -c "import ollama; print('ollama: OK')"
python -c "import requests; print('requests: OK')"
python -c "import pydantic; print('pydantic:', pydantic.__version__)"
```

**All four imports should succeed without errors.**

## Step 3: Install PostgreSQL

### Linux (Ubuntu/Debian)

```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib -y

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Verify PostgreSQL is running
sudo systemctl status postgresql
# Look for "active (running)"
```

### macOS

```bash
# Install via Homebrew
brew install postgresql@16

# Start PostgreSQL service
brew services start postgresql@16

# Verify
brew services list | grep postgresql
# Should show "started"
```

### Verification Checkpoint

```bash
# Connect to PostgreSQL
psql -U postgres -c "SELECT version();"
# or on macOS: psql -c "SELECT version();"

# Should output PostgreSQL version info
```

## Step 4: Create Local Database

```bash
# Linux: Switch to postgres user
sudo -u postgres psql << 'EOF'
-- Create database
CREATE DATABASE wolf_logic_local;

-- Create user (optional, can use your system user)
CREATE USER wolf_client WITH PASSWORD 'localclient2024';
GRANT ALL PRIVILEGES ON DATABASE wolf_logic_local TO wolf_client;

-- Verify
\l wolf_logic_local
EOF

# macOS: Run directly (uses your system user)
psql << 'EOF'
CREATE DATABASE wolf_logic_local;
\l wolf_logic_local
EOF
```

**Expected:** Database `wolf_logic_local` appears in the list.

## Step 5: Import Schema from 181

This creates the table structure without data.

```bash
# Dump schema only from 181
PGPASSWORD=wolflogic2024 pg_dump \
  -h 100.110.82.181 \
  -p 5433 \
  -U wolf \
  -d wolf_logic \
  --schema-only \
  --no-owner \
  --no-privileges \
  > /tmp/wolf_logic_schema.sql

# Verify dump file exists and has content
ls -lh /tmp/wolf_logic_schema.sql
head -20 /tmp/wolf_logic_schema.sql

# Import schema to local database
# Linux:
sudo -u postgres psql -d wolf_logic_local < /tmp/wolf_logic_schema.sql

# macOS:
psql -d wolf_logic_local < /tmp/wolf_logic_schema.sql
```

### Verification Checkpoint

```bash
# Check tables exist
psql -d wolf_logic_local -c "\dt"
# Should show: memories table (at minimum)

psql -d wolf_logic_local -c "\d memories"
# Should show: id, content, namespace, created_at columns
```

## Step 6: Initial Data Sync

```bash
# Dump memories data from 181
PGPASSWORD=wolflogic2024 pg_dump \
  -h 100.110.82.181 \
  -p 5433 \
  -U wolf \
  -d wolf_logic \
  --data-only \
  --table=memories \
  > /tmp/memories_data.sql

# Check file size (should be several MB with 97k+ rows)
ls -lh /tmp/memories_data.sql

# Import data to local database
# Linux:
sudo -u postgres psql -d wolf_logic_local < /tmp/memories_data.sql

# macOS:
psql -d wolf_logic_local < /tmp/memories_data.sql
```

### Verification Checkpoint

```bash
# Count local memories
psql -d wolf_logic_local -c "SELECT COUNT(*) FROM memories;"
# Expected: 97,000+ rows

# Check namespace distribution
psql -d wolf_logic_local -c "SELECT namespace, COUNT(*) FROM memories GROUP BY namespace ORDER BY COUNT(*) DESC LIMIT 10;"
# Should show scripty, wolf_story, ingested, etc.
```

## Step 7: Configure Environment Variables

Create a configuration file for your client scripts.

```bash
# Create config directory
mkdir -p ~/.config/wolf-logic

# Create environment file
cat > ~/.config/wolf-logic/env << 'EOF'
# Wolf Logic Client Configuration

# Local PostgreSQL
export LOCAL_PG_HOST="localhost"
export LOCAL_PG_PORT="5432"
export LOCAL_PG_DB="wolf_logic_local"
export LOCAL_PG_USER="wolf_client"  # or your system user
export LOCAL_PG_PASSWORD="localclient2024"

# Hub (181) - for submissions only
export HUB_PG_HOST="100.110.82.181"
export HUB_PG_PORT="5433"
export HUB_PG_DB="wolf_logic"
export HUB_PG_USER="wolf"
export HUB_PG_PASSWORD="wolflogic2024"

# MCP Intake API
export MCP_INTAKE_URL="http://100.110.82.181:8002"
EOF

# Load in your shell profile
echo 'source ~/.config/wolf-logic/env' >> ~/.bashrc  # or ~/.zshrc on macOS
source ~/.config/wolf-logic/env
```

## Step 8: Create Sync Script

```bash
# Create scripts directory
mkdir -p ~/wolf-logic-client/scripts

# Create sync script
cat > ~/wolf-logic-client/scripts/sync_from_librarian.sh << 'EOF'
#!/bin/bash
# Sync memories from 181 to local PostgreSQL

set -e

# Configuration
HUB_HOST="100.110.82.181"
HUB_PORT="5433"
HUB_DB="wolf_logic"
HUB_USER="wolf"
HUB_PASS="wolflogic2024"

LOCAL_DB="wolf_logic_local"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DUMP_FILE="/tmp/memories_sync_${TIMESTAMP}.sql"
LOG_FILE="/var/log/wolf_sync.log"

echo "[$(date)] Starting sync..." | tee -a "$LOG_FILE"

# Dump from 181
PGPASSWORD=$HUB_PASS pg_dump \
  -h "$HUB_HOST" \
  -p "$HUB_PORT" \
  -U "$HUB_USER" \
  -d "$HUB_DB" \
  --data-only \
  --table=memories \
  --on-conflict-do-nothing \
  > "$DUMP_FILE" 2>> "$LOG_FILE"

if [ ! -s "$DUMP_FILE" ]; then
  echo "[$(date)] ERROR: Dump file is empty" | tee -a "$LOG_FILE"
  exit 1
fi

# Import to local
psql -d "$LOCAL_DB" < "$DUMP_FILE" >> "$LOG_FILE" 2>&1

# Cleanup
rm -f "$DUMP_FILE"

# Report
COUNT=$(psql -d "$LOCAL_DB" -t -c "SELECT COUNT(*) FROM memories;")
echo "[$(date)] Sync complete. Local memories: $COUNT" | tee -a "$LOG_FILE"
EOF

# Make executable
chmod +x ~/wolf-logic-client/scripts/sync_from_librarian.sh

# Create log file
sudo touch /var/log/wolf_sync.log
sudo chmod 666 /var/log/wolf_sync.log
```

## Step 9: Set Up Cron for Auto-Sync

```bash
# Open crontab editor
crontab -e

# Add this line (sync every 5 minutes):
*/5 * * * * ~/wolf-logic-client/scripts/sync_from_librarian.sh >> /var/log/wolf_sync.log 2>&1
```

### Verify Cron Entry

```bash
crontab -l | grep wolf
# Should show the sync script entry
```

## Step 10: Test Connection Script

Create a test script to verify everything works.

```bash
cat > ~/wolf-logic-client/scripts/test_connection.py << 'EOF'
#!/usr/bin/env python3
"""Test Wolf Logic client configuration."""

import psycopg2
import os
import sys

def test_local_connection():
    """Test local PostgreSQL connection."""
    print("Testing local PostgreSQL...")
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            dbname="wolf_logic_local",
            user=os.environ.get("LOCAL_PG_USER", os.environ.get("USER")),
            password=os.environ.get("LOCAL_PG_PASSWORD", "")
        )
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM memories;")
        count = cur.fetchone()[0]
        print(f"  SUCCESS: {count} memories in local database")
        conn.close()
        return True
    except Exception as e:
        print(f"  FAILED: {e}")
        return False

def test_hub_connection():
    """Test connection to 181 (for sync verification)."""
    print("Testing hub connection (181)...")
    try:
        conn = psycopg2.connect(
            host="100.110.82.181",
            port=5433,
            dbname="wolf_logic",
            user="wolf",
            password="wolflogic2024"
        )
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM memories;")
        count = cur.fetchone()[0]
        print(f"  SUCCESS: {count} memories on hub")
        conn.close()
        return True
    except Exception as e:
        print(f"  FAILED: {e}")
        return False

def test_namespace_query():
    """Test namespace query on local DB."""
    print("Testing namespace query...")
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            dbname="wolf_logic_local",
            user=os.environ.get("LOCAL_PG_USER", os.environ.get("USER")),
            password=os.environ.get("LOCAL_PG_PASSWORD", "")
        )
        cur = conn.cursor()
        cur.execute("""
            SELECT namespace, COUNT(*)
            FROM memories
            GROUP BY namespace
            ORDER BY COUNT(*) DESC
            LIMIT 5;
        """)
        results = cur.fetchall()
        print("  Top namespaces:")
        for ns, count in results:
            print(f"    {ns}: {count}")
        conn.close()
        return True
    except Exception as e:
        print(f"  FAILED: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Wolf Logic Client Connection Test")
    print("=" * 50)

    local_ok = test_local_connection()
    hub_ok = test_hub_connection()
    query_ok = test_namespace_query()

    print("=" * 50)
    if local_ok and hub_ok and query_ok:
        print("All tests passed. Client is ready.")
        sys.exit(0)
    else:
        print("Some tests failed. Check configuration.")
        sys.exit(1)
EOF

chmod +x ~/wolf-logic-client/scripts/test_connection.py
```

### Run Test

```bash
conda activate client-memory
python ~/wolf-logic-client/scripts/test_connection.py
```

**Expected output:**
```
==================================================
Wolf Logic Client Connection Test
==================================================
Testing local PostgreSQL...
  SUCCESS: 97XXX memories in local database
Testing hub connection (181)...
  SUCCESS: 97XXX memories on hub
Testing namespace query...
  Top namespaces:
    scripty: 46XXX
    wolf_story: 16XXX
    ingested: 10XXX
==================================================
All tests passed. Client is ready.
```

## Setup Complete

You now have:
1. Miniconda3 with `client-memory` environment
2. Local PostgreSQL with `wolf_logic_local` database
3. Initial data synced from 181
4. Cron job for automatic sync every 5 minutes
5. Test script to verify configuration

**Next steps:**
- Read [query-patterns.md](./query-patterns.md) to learn how to query your local database
- Read [architecture.md](./architecture.md) to understand why this design exists
- If issues arise, see [troubleshooting.md](./troubleshooting.md)
