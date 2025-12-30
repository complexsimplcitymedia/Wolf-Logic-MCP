# Wolf Logic Memory Layer - Client Configuration

## Quick Start

You are a spoke. 100.110.82.181 is the hub. Data flows TO the hub, knowledge flows FROM the hub to your local PostgreSQL.

**The Rule:** Never write to your local DB. Never query 181 for reads. Sync pulls data down, you query local.

## 30-Second Setup

```bash
# 1. Install Miniconda3 (NOT Anaconda3)
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -b -p ~/miniconda3
eval "$(~/miniconda3/bin/conda shell.bash hook)"

# 2. Create client environment
conda create -n client-memory python=3.12 -y
conda activate client-memory
conda install -c conda-forge psycopg2 -y
pip install ollama requests pydantic

# 3. Install PostgreSQL and create local DB
sudo apt install postgresql postgresql-contrib -y
sudo -u postgres createdb wolf_logic_local

# 4. Initial sync from 181
PGPASSWORD=wolflogic2024 pg_dump -h 100.110.82.181 -p 5433 -U wolf -d wolf_logic --schema-only | psql -d wolf_logic_local
PGPASSWORD=wolflogic2024 pg_dump -h 100.110.82.181 -p 5433 -U wolf -d wolf_logic --data-only --table=memories | psql -d wolf_logic_local

# 5. Verify
psql -d wolf_logic_local -c "SELECT COUNT(*) FROM memories;"
```

## Documentation Index

| Document | Purpose |
|----------|---------|
| [architecture.md](./architecture.md) | Hub-and-spoke model, data flow, why this design |
| [setup-guide.md](./setup-guide.md) | Complete installation walkthrough |
| [environment.md](./environment.md) | Miniconda3 environment configuration |
| [query-patterns.md](./query-patterns.md) | How to query your local PostgreSQL |
| [troubleshooting.md](./troubleshooting.md) | Common issues and fixes |

## The Architecture in One Diagram

```
+------------------+       +------------------------+       +------------------+
|  YOUR CLIENT     |       |  100.110.82.181 (HUB)  |       |  OTHER CLIENTS   |
|  (SPOKE)         |       |  The Librarian         |       |  (SPOKES)        |
+------------------+       +------------------------+       +------------------+
        |                           ^                              |
        |  [SUBMIT DATA]            |                              |
        +-------------------------->|<-----------------------------+
                                    |
                      +-------------+-------------+
                      |                           |
                      v                           v
              +---------------+           +---------------+
              | PROCESSING    |           | VECTORIZATION |
              | qwen3:4b      |           | 2560 dims     |
              +---------------+           +---------------+
                      |                           |
                      +-------------+-------------+
                                    |
                                    v
                      +------------------------+
                      | CANONICAL STORAGE      |
                      | wolf_logic @ 5433      |
                      | 97,000+ memories       |
                      +------------------------+
                                    |
                      +-------------+-------------+
                      |                           |
                      v                           v
        +------------------+           +------------------+
        |  YOUR LOCAL DB   |           |  OTHER LOCAL DBs |
        |  (READ-ONLY)     |           |  (READ-ONLY)     |
        +------------------+           +------------------+
                |
                v
        [YOU QUERY HERE]
```

## Critical Rules

1. **Submit data TO 181** - Text intake, file ingestion, all writes go to the hub
2. **Sync FROM 181** - Your local DB is populated by sync scripts
3. **Query LOCAL** - All reads hit your local PostgreSQL, never 181
4. **Never write local** - Your local DB is a read-only replica

## Network Requirements

- **Tailscale connection** to 100.110.82.181
- **Port 5433** accessible (PostgreSQL on hub)
- **Port 8002** accessible (MCP intake API)
- **Port 11434** accessible (Ollama on hub, for submissions)

## Support

If your local DB is empty, run the sync. If sync fails, check Tailscale. If Tailscale is up but sync fails, check 181 is running. If all else fails, query 181 directly (temporary bypass only).

---

*This documentation is part of the Wolf Logic macro-os client configuration.*
