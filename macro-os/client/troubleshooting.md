# Troubleshooting Guide

## Quick Diagnosis

Run this first:

```bash
# Activate environment
conda activate client-memory

# Test everything
python ~/wolf-logic-client/scripts/test_connection.py
```

If tests pass, your setup is correct. If tests fail, use this guide.

---

## Problem: Local Database is Empty

**Symptom:** `SELECT COUNT(*) FROM memories;` returns 0

**Cause:** Sync never ran or failed

**Fix:**

```bash
# 1. Check if sync script exists
ls -la ~/wolf-logic-client/scripts/sync_from_librarian.sh

# 2. Run sync manually
~/wolf-logic-client/scripts/sync_from_librarian.sh

# 3. Check for errors
cat /var/log/wolf_sync.log | tail -20

# 4. Verify data was imported
psql -d wolf_logic_local -c "SELECT COUNT(*) FROM memories;"
```

**If sync script doesn't exist:** See [setup-guide.md](./setup-guide.md) Step 8

---

## Problem: Cannot Connect to Local PostgreSQL

**Symptom:** `psql: could not connect to server: Connection refused`

**Fix:**

```bash
# 1. Check if PostgreSQL is running
# Linux:
sudo systemctl status postgresql
# macOS:
brew services list | grep postgresql

# 2. Start PostgreSQL if stopped
# Linux:
sudo systemctl start postgresql
# macOS:
brew services start postgresql@16

# 3. Check PostgreSQL is listening on port 5432
ss -tlnp | grep 5432  # Linux
lsof -i :5432         # macOS

# 4. Verify database exists
psql -l | grep wolf_logic_local
```

**If database doesn't exist:**
```bash
# Linux:
sudo -u postgres createdb wolf_logic_local
# macOS:
createdb wolf_logic_local
```

---

## Problem: Cannot Connect to 181 (Hub)

**Symptom:** `pg_dump: could not connect to server: Connection refused` or timeout

**Fix:**

```bash
# 1. Check Tailscale is connected
tailscale status

# 2. Ping 181
ping -c 3 100.110.82.181

# 3. Test PostgreSQL port specifically
nc -zv 100.110.82.181 5433

# 4. If Tailscale is down
sudo tailscale up

# 5. If port is blocked, check firewall on 181
# (requires SSH access to 181)
ssh wolf@100.110.82.181 "sudo ufw status"
```

**Expected:** Port 5433 should be open. If not, firewall issue on 181.

---

## Problem: Sync Runs But No Data Imported

**Symptom:** Sync script exits successfully but local DB still empty

**Fix:**

```bash
# 1. Check the dump file
PGPASSWORD=wolflogic2024 pg_dump -h 100.110.82.181 -p 5433 -U wolf -d wolf_logic --data-only --table=memories > /tmp/test_dump.sql

# 2. Check dump file has content
wc -l /tmp/test_dump.sql
head -50 /tmp/test_dump.sql

# 3. If dump is empty, check source table on 181
PGPASSWORD=wolflogic2024 psql -h 100.110.82.181 -p 5433 -U wolf -d wolf_logic -c "SELECT COUNT(*) FROM memories;"

# 4. If source has data but dump is empty, check pg_dump version compatibility
pg_dump --version
```

**Common issue:** Schema mismatch between 181 and local. Re-import schema:

```bash
PGPASSWORD=wolflogic2024 pg_dump -h 100.110.82.181 -p 5433 -U wolf -d wolf_logic --schema-only --no-owner > /tmp/schema.sql
psql -d wolf_logic_local -c "DROP TABLE IF EXISTS memories CASCADE;"
psql -d wolf_logic_local < /tmp/schema.sql
```

---

## Problem: "relation memories does not exist"

**Symptom:** Query fails with `ERROR: relation "memories" does not exist`

**Cause:** Schema was never imported

**Fix:**

```bash
# Import schema from 181
PGPASSWORD=wolflogic2024 pg_dump -h 100.110.82.181 -p 5433 -U wolf -d wolf_logic --schema-only --no-owner > /tmp/schema.sql
psql -d wolf_logic_local < /tmp/schema.sql

# Verify table exists
psql -d wolf_logic_local -c "\d memories"
```

---

## Problem: "conda: command not found"

**Symptom:** Terminal doesn't recognize `conda`

**Fix:**

```bash
# 1. Check Miniconda is installed
ls ~/miniconda3/

# 2. Initialize conda for your shell
~/miniconda3/bin/conda init bash  # or zsh

# 3. Reload shell
source ~/.bashrc  # or ~/.zshrc

# 4. Verify
conda --version
```

---

## Problem: "No module named 'psycopg2'"

**Symptom:** Python import fails

**Fix:**

```bash
# 1. Verify correct environment is active
conda activate client-memory

# 2. Check psycopg2 is installed
conda list | grep psycopg2

# 3. If not installed, install it
conda install -c conda-forge psycopg2 -y

# 4. Test import
python -c "import psycopg2; print(psycopg2.__version__)"
```

---

## Problem: Sync Cron Not Running

**Symptom:** `/var/log/wolf_sync.log` not updating

**Fix:**

```bash
# 1. Check cron entry exists
crontab -l | grep wolf

# 2. If missing, add it
crontab -e
# Add: */5 * * * * ~/wolf-logic-client/scripts/sync_from_librarian.sh >> /var/log/wolf_sync.log 2>&1

# 3. Check cron service is running
# Linux:
sudo systemctl status cron
# macOS:
launchctl list | grep cron

# 4. Check script is executable
chmod +x ~/wolf-logic-client/scripts/sync_from_librarian.sh

# 5. Check log file is writable
sudo touch /var/log/wolf_sync.log
sudo chmod 666 /var/log/wolf_sync.log
```

---

## Problem: Stale Data (Sync Lag Too Long)

**Symptom:** Local data is hours/days behind 181

**Fix:**

```bash
# 1. Check last sync time
tail -5 /var/log/wolf_sync.log

# 2. Run manual sync
~/wolf-logic-client/scripts/sync_from_librarian.sh

# 3. Compare counts
echo "Local:"
psql -d wolf_logic_local -c "SELECT COUNT(*) FROM memories;"
echo "Hub:"
PGPASSWORD=wolflogic2024 psql -h 100.110.82.181 -p 5433 -U wolf -d wolf_logic -c "SELECT COUNT(*) FROM memories;"

# 4. If cron is failing, check cron logs
# Linux:
grep CRON /var/log/syslog | tail -20
# macOS:
log show --predicate 'process == "cron"' --last 1h
```

---

## Problem: "password authentication failed"

**Symptom:** Connection to 181 fails with auth error

**Fix:**

```bash
# 1. Verify password
echo $HUB_PG_PASSWORD  # Should be: wolflogic2024

# 2. Test with explicit password
PGPASSWORD=wolflogic2024 psql -h 100.110.82.181 -p 5433 -U wolf -d wolf_logic -c "SELECT 1;"

# 3. If still failing, credentials may have changed
# Contact Wolf or check 181 pg_hba.conf
```

---

## Problem: Slow Queries

**Symptom:** Queries take seconds instead of milliseconds

**Fix:**

```bash
# 1. Add indexes
psql -d wolf_logic_local << 'EOF'
CREATE INDEX IF NOT EXISTS idx_memories_namespace ON memories(namespace);
CREATE INDEX IF NOT EXISTS idx_memories_created_at ON memories(created_at);
CREATE INDEX IF NOT EXISTS idx_memories_ns_created ON memories(namespace, created_at DESC);
ANALYZE memories;
EOF

# 2. Check table size
psql -d wolf_logic_local -c "SELECT pg_size_pretty(pg_total_relation_size('memories'));"

# 3. Always use LIMIT in queries
# Bad: SELECT * FROM memories WHERE namespace = 'scripty';
# Good: SELECT * FROM memories WHERE namespace = 'scripty' LIMIT 100;
```

---

## Problem: Disk Space Full

**Symptom:** Sync or PostgreSQL operations fail with "No space left on device"

**Fix:**

```bash
# 1. Check disk usage
df -h

# 2. Clean conda cache
conda clean --all -y

# 3. Clean old sync files
rm -f /tmp/memories_sync_*.sql

# 4. Vacuum PostgreSQL
psql -d wolf_logic_local -c "VACUUM FULL;"

# 5. Check PostgreSQL data directory size
du -sh /var/lib/postgresql/*/main/  # Linux
du -sh /usr/local/var/postgresql*/  # macOS
```

---

## Emergency: Query 181 Directly

If your local DB is completely broken and you need data NOW:

```python
import psycopg2

# TEMPORARY - Direct hub connection
conn = psycopg2.connect(
    host="100.110.82.181",
    port=5433,
    dbname="wolf_logic",
    user="wolf",
    password="wolflogic2024"
)
cur = conn.cursor()
cur.execute("SELECT content, namespace FROM memories ORDER BY created_at DESC LIMIT 10;")
for row in cur.fetchall():
    print(row)
conn.close()
```

**This is a workaround.** Fix your local setup as soon as possible. Routine queries should never hit 181.

---

## Diagnostic Script

Save this for troubleshooting sessions:

```bash
#!/bin/bash
# diagnose.sh - Wolf Logic client diagnostics

echo "=== Wolf Logic Client Diagnostics ==="
echo ""

echo "1. Conda environment:"
conda info --envs | grep client-memory || echo "  MISSING: client-memory environment"
echo ""

echo "2. PostgreSQL status:"
systemctl is-active postgresql 2>/dev/null || brew services list 2>/dev/null | grep postgresql || echo "  Cannot determine PostgreSQL status"
echo ""

echo "3. Local database:"
psql -d wolf_logic_local -c "SELECT COUNT(*) as local_memories FROM memories;" 2>/dev/null || echo "  FAILED: Cannot query local database"
echo ""

echo "4. Tailscale status:"
tailscale status 2>/dev/null | head -5 || echo "  Tailscale not running or not installed"
echo ""

echo "5. Hub connectivity:"
nc -zv 100.110.82.181 5433 2>&1 | head -1 || echo "  Cannot reach 181:5433"
echo ""

echo "6. Hub database:"
PGPASSWORD=wolflogic2024 psql -h 100.110.82.181 -p 5433 -U wolf -d wolf_logic -c "SELECT COUNT(*) as hub_memories FROM memories;" 2>/dev/null || echo "  FAILED: Cannot query hub"
echo ""

echo "7. Last sync:"
tail -3 /var/log/wolf_sync.log 2>/dev/null || echo "  No sync log found"
echo ""

echo "8. Cron entry:"
crontab -l 2>/dev/null | grep wolf || echo "  No wolf sync cron entry"
echo ""

echo "=== End Diagnostics ==="
```

Run with: `bash diagnose.sh`
