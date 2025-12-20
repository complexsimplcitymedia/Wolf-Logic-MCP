# LIBRARIAN ACCESS VIA GEMINI CLI

**What Was Missed**: Gemini CLI has PostgreSQL extensions that enable natural language database queries.

**What This Means**: You can now talk to the Librarian in plain English instead of writing SQL.

---

## Setup Complete

✅ **Gemini CLI installed** (`/home/thewolfwalksalone/.nvm/versions/node/v24.11.1/bin/gemini`)
✅ **PostgreSQL extension installed** (v0.1.5)
✅ **Database configured** (wolf_logic @ 100.110.82.181:5433)
✅ **Environment variables set** (`~/.bashrc`)

---

## How to Access the Librarian

### Quick Start
```bash
cd /mnt/Wolf-code/Wolf-Ai-Enterptises
./librarian-gemini-setup.sh
```

This launches Gemini CLI with full access to wolf_logic database (97,017 memories).

### Manual Start
```bash
# Set environment variables
export POSTGRES_HOST=100.110.82.181
export POSTGRES_PORT=5433
export POSTGRES_DATABASE=wolf_logic
export POSTGRES_USER=wolf
export POSTGRES_PASSWORD=wolflogic2024

# Launch Gemini
gemini
```

---

## Natural Language Queries

Instead of writing SQL, just ask:

**Example 1: Schema exploration**
```
You: List all tables in the database
Gemini: [Connects to PostgreSQL, shows: memories, memories_embedding, etc.]
```

**Example 2: Data exploration**
```
You: Show me the 10 most recent memories from the scripty namespace
Gemini: [Runs: SELECT * FROM memories WHERE namespace='scripty' ORDER BY created_at DESC LIMIT 10]
```

**Example 3: Aggregations**
```
You: How many memories are in each namespace?
Gemini: [Runs: SELECT namespace, COUNT(*) FROM memories GROUP BY namespace]
```

**Example 4: Complex queries**
```
You: Find all job applications from December that mention "remote"
Gemini: [Constructs query with WHERE, LIKE, date filters]
```

**Example 5: Direct SQL (if you want)**
```
You: Execute this query: SELECT content FROM memories_embedding WHERE namespace='core_identity' LIMIT 5
Gemini: [Runs exact SQL, returns results]
```

---

## What This Unlocks

### Before (Manual SQL)
```sql
PGPASSWORD=wolflogic2024 psql -h 100.110.82.181 -p 5433 -U wolf -d wolf_logic -c \
  "SELECT content, namespace, created_at FROM memories WHERE content ILIKE '%investor pitch%' ORDER BY created_at DESC LIMIT 10;"
```

### After (Natural Language)
```
You: Show me everything about investor pitches from the last week
Gemini: [Constructs query, executes, formats results]
```

---

## Available Tools

The PostgreSQL extension provides:

1. **list_tables** - Show all tables in wolf_logic database
2. **execute_sql** - Run any SQL query (SELECT, INSERT, UPDATE, etc.)
3. **get_query_plan** - Analyze query performance (EXPLAIN)
4. **list_active_queries** - See what's running right now
5. **list_tables_missing_unique_indexes** - Performance optimization hints
6. **list_table_fragmentation** - Database health checks

---

## Database Details

**Connection**:
- Host: 100.110.82.181 (Tailscale)
- Port: 5433
- Database: wolf_logic
- User: wolf
- Password: wolflogic2024

**Current Stats**:
- **Total Memories**: 97,017
- **Namespaces**:
  - scripty: 45,761 (15 days active)
  - wolf_story: 16,124 (5 days active)
  - ingested: 10,831 (6 days active)
  - session_recovery: 9,459 (3 days)
  - wolf_hunt: 2,916 (2 days)
  - mem0_import: 6,576 (45 days - legacy)
  - imported: 3,847
  - system_announcements: 933
  - stenographer: 502
  - wolf_logic: 25

**Tables**:
- `memories` - All memory content with metadata
- `memories_embedding` - Vectorized memories (2560 dims, qwen3-embedding:4b)
- `candidates` - Job search candidates
- `job_applications` - Application tracking
- `scraped_jobs` - Wolf Hunt job data

---

## Integration Opportunities

### 1. MCP Gateway + Gemini
Connect Wolf Memory Gateway API (port 5001) to Gemini CLI for AI-powered memory queries from web interface.

### 2. Voice Assistant + Librarian
"Alexa, ask the Librarian what Wolf said about equity yesterday"
→ Gemini CLI query → PostgreSQL → spoken response

### 3. Wolf Hunt + Gemini
Natural language job search:
"Find all remote developer jobs posted in the last 3 days"
→ Gemini constructs query → Returns 2,916 jobs

### 4. Real-Time Stenographer Checks
"What did I discuss in the last hour?"
→ Gemini queries scripty namespace → Returns recent conversation

---

## Why This Was Missed

**MySQL extension exists** → https://github.com/gemini-cli-extensions/mysql
**PostgreSQL extension exists** → https://github.com/gemini-cli-extensions/postgres
**Gemini CLI already installed** → Wolf had it but didn't connect to PostgreSQL

**The gap**: Natural language access to 97,017 memories was one `gemini extensions install` away.

**Now fixed**: Librarian is accessible via conversational queries.

---

## References

- [Gemini CLI PostgreSQL Extension](https://github.com/gemini-cli-extensions/postgres)
- [Cloud SQL PostgreSQL Extension](https://github.com/gemini-cli-extensions/cloud-sql-postgresql)
- [Gemini CLI for PostgreSQL (Google Cloud Blog)](https://cloud.google.com/blog/products/databases/gemini-cli-for-postgresql-in-action)
- [Gemini CLI Extensions for Data Cloud](https://cloud.google.com/blog/products/databases/gemini-cli-extensions-for-google-data-cloud)

---

**Wolf**: You now have conversational access to the Librarian. No more memorizing SQL syntax. Just ask.
