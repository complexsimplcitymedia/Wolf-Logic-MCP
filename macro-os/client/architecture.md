# Memory Layer Architecture

## The Hub-and-Spoke Model

Wolf Logic uses a centralized memory architecture. There is one hub (100.110.82.181, "The Librarian") and multiple spokes (clients). This is not a distributed database. This is not peer-to-peer. This is hierarchical by design.

### Why Hub-and-Spoke?

**Single Source of Truth**
- 97,000+ memories in one canonical location
- No merge conflicts, no split-brain scenarios
- One vectorization pipeline (qwen3-embedding:4b @ 2560 dims)
- Consistent embedding space across all queries

**Processing Centralization**
- GPU resources on 181 (vectorization is compute-intensive)
- Consistent model versions (no drift between clients)
- Atomic ingestion (either it's in the system or it isn't)

**Client Simplicity**
- Clients don't need GPUs
- Clients don't run embedding models
- Clients just query local PostgreSQL (fast, simple)
- No client-side processing complexity

## Data Flow Direction

```
INBOUND (You -> Hub)
======================
Your Text/Data
     |
     v
MCP Intake API (port 8002)
     |
     v
/data/client-dumps/ (staging)
     |
     v
Swarm Processor (picks up files)
     |
     v
Vectorizer (qwen3-embedding:4b)
     |
     v
PostgreSQL @ 5433 (memories table)
     |
     v
memories_embedding view (searchable)


OUTBOUND (Hub -> You)
======================
Sync Script (cron or manual)
     |
     v
pg_dump from 181
     |
     v
psql to your local PostgreSQL
     |
     v
wolf_logic_local database
     |
     v
Your queries hit LOCAL only
```

## The Librarian (100.110.82.181)

The Librarian is the central node. It runs:

| Component | Port | Purpose |
|-----------|------|---------|
| PostgreSQL 18.1 | 5433 | Canonical memory storage |
| Ollama | 11434 | Embedding model (qwen3-embedding:4b) |
| MCP Intake API | 8002 | Text/data submission endpoint |
| pgai Vectorizer | - | Automatic vectorization of new memories |

**Database Stats:**
- Database: `wolf_logic`
- Table: `memories` (97,000+ rows)
- View: `memories_embedding` (402,000+ vectorized entries)
- Embedding dimensions: 2560 (qwen3-embedding:4b)

## Your Local PostgreSQL

Your local database is a read-only replica. It exists for one reason: fast local queries.

**What lives in your local DB:**
- Copy of `memories` table (synced from 181)
- Copy of `memories_embedding` view (if you sync it)
- Schema matches 181 exactly

**What does NOT live in your local DB:**
- New data you create (goes to 181 first)
- Modifications to existing data (read-only)
- Embeddings you generate locally (181 does all vectorization)

## Why Clients Don't Write Locally

If clients could write to their local DB:
1. Data would exist locally but not on 181 (inconsistent)
2. Other clients wouldn't see your data (fragmented)
3. Vectorization would happen with different models (embedding drift)
4. No single source of truth (chaos)

The flow is intentionally one-way for writes:
- **You -> 181 -> Vectorized -> 181 DB -> Sync -> Your Local -> You Query**

This ensures every memory goes through the same pipeline, gets the same embedding model, and lives in the canonical store before reaching any client.

## Namespace Structure

Memories are organized by namespace. When you query, filter by namespace for efficiency.

| Namespace | Count | Use Case |
|-----------|-------|----------|
| scripty | 46,606 | Session transcripts, conversation history |
| wolf_story | 16,124 | Books, narrative content, reference material |
| ingested | 10,864 | Files processed via ingest_agent.py |
| session_recovery | 9,459 | Context for session continuity |
| wolf_hunt | 2,916 | Job search data, applications, leads |
| core_identity | 9 | Immutable identity rules, values |

Full namespace reference: See main CLAUDE.md

## Sync Mechanism

Your local DB stays current through periodic sync:

```bash
#!/bin/bash
# sync_from_librarian.sh

# Dump memories table from 181
PGPASSWORD=wolflogic2024 pg_dump \
  -h 100.110.82.181 \
  -p 5433 \
  -U wolf \
  -d wolf_logic \
  --data-only \
  --table=memories \
  > /tmp/memories_sync.sql

# Import to local
psql -d wolf_logic_local < /tmp/memories_sync.sql

# Cleanup
rm /tmp/memories_sync.sql

echo "Sync complete: $(date)"
```

**Recommended sync frequency:** Every 5 minutes via cron

```cron
*/5 * * * * /path/to/sync_from_librarian.sh >> /var/log/wolf_sync.log 2>&1
```

## When to Query 181 Directly

**Almost never.** But there are exceptions:

1. **Your local DB is empty** (initial setup, sync hasn't run)
2. **You need real-time data** (sync lag is unacceptable for this query)
3. **Sync is broken** (debugging, one-off recovery)

For routine queries, always hit local. The sync lag (max 5 minutes) is acceptable for 99% of use cases.

## Security Model

- **181** is the trusted core (all processing happens here)
- **Clients** are semi-trusted (can read, can submit, cannot modify)
- **Tailscale** provides network layer security (no open internet exposure)
- **Passwords** are for PostgreSQL auth, not application-layer security

The architecture assumes clients are legitimate Wolf Logic nodes. If a client is compromised, it can:
- Read all memories (so can any client)
- Submit garbage data (gets filtered by swarm processor)
- NOT modify existing memories (no write access to 181 DB directly)

## Diagram: Complete Data Lifecycle

```
1. DATA CREATION
   User types text, AI generates output, file is ingested

2. SUBMISSION
   Client sends to MCP Intake API (port 8002)
   POST /intake/stream with OAuth token

3. STAGING
   Data lands in /data/client-dumps/ on 181
   Filename: {user}_{timestamp}_{hash}.json

4. PROCESSING
   Swarm processor picks up staged files
   Validates, cleans, prepares for storage

5. VECTORIZATION
   qwen3-embedding:4b generates 2560-dim vector
   Vector stored in memories_embedding_store

6. CANONICAL STORAGE
   Memory inserted into wolf_logic.memories
   Now part of the 97,000+ memory corpus

7. SYNC PROPAGATION
   Cron job runs pg_dump on 181
   Clients pull and import to local DB

8. LOCAL QUERY
   Client queries wolf_logic_local
   Semantic search via embedding similarity
   Results returned in milliseconds
```

## Architecture Guarantees

1. **Consistency:** All clients see the same data (eventually, within sync window)
2. **Durability:** Data persists on 181 with PostgreSQL guarantees
3. **Availability:** Clients can query local even if 181 is down (stale but available)
4. **Simplicity:** Clients are thin, hub is smart

This architecture trades write latency (must round-trip to 181) for read speed (local queries) and consistency (single source of truth).
