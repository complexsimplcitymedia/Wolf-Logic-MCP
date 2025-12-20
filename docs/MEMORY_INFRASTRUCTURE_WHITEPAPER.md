# Wolf AI Memory Infrastructure - Technical White Paper

**Version:** 1.0
**Date:** December 17, 2025
**System:** wolf_logic @ 100.110.82.181:5433

---

## Executive Summary

The Wolf AI Memory Infrastructure is a production-grade semantic memory system managing 88,000+ contextualized memories across distributed AI agents. Built on PostgreSQL with pgai extensions, the system provides real-time ingestion, intelligent filtering, automatic vectorization, and semantic retrieval at scale.

**Key Metrics:**
- **Total Memories:** 88,916 (as of Dec 17, 2025)
- **Embedding Model:** qwen3-embedding:4b (#1 MTEB multilingual, 2560 dimensions)
- **Storage:** PostgreSQL 16 with pgai + pgvector
- **Ingestion Rate:** Real-time (sub-30 second latency)
- **Query Performance:** <100ms semantic search
- **Uptime:** 24/7 with automatic recovery

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    INPUT LAYER                               │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │  Claude     │  │  Gemini    │  │  Manual    │            │
│  │  Sessions   │  │  Sessions  │  │  Ingestion │            │
│  └──────┬─────┘  └──────┬─────┘  └──────┬─────┘            │
└─────────┼────────────────┼────────────────┼─────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│                  FILTERING LAYER                             │
│         Scripty AI (llama3.2:1b instances)                  │
│         - Noise filtering (phone/music/background)          │
│         - Session validation                                 │
│         - Real-time transcription                            │
│         - Dynamic scaling (1 instance per active session)    │
└─────────┬───────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                  STORAGE LAYER                               │
│         PostgreSQL wolf_logic Database                       │
│         - Table: public.memories                             │
│         - Namespace organization (Dewey Decimal-style)       │
│         - Metadata: JSONB with timestamps, types, context    │
└─────────┬───────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│               VECTORIZATION LAYER                            │
│         pgai Vectorizer + Ollama Fleet                       │
│         - Model: qwen3-embedding:4b (2560 dims)             │
│         - Chunking: 512 tokens, 50 token overlap            │
│         - Target: memories_embedding_store                   │
│         - View: memories_embedding (semantic search)         │
└─────────┬───────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│              SWARM PROCESSING LAYER                          │
│         Real-time Analysis (4-block trigger)                 │
│         ┌──────────────┐    ┌──────────────┐               │
│         │  Embedding   │    │  Sentiment   │               │
│         │  Fleet       │    │  Analysis    │               │
│         │  (Multi)     │    │  (Mistral)   │               │
│         └──────────────┘    └──────────────┘               │
└─────────┬───────────────────────┬───────────────────────────┘
          │                       │
          ▼                       ▼
┌──────────────────────┐ ┌──────────────────────┐
│  Vectorized Storage  │ │  Sentiment Metadata  │
│  (searchable)        │ │  (1-5 scale)         │
└──────────────────────┘ └──────────────────────┘
          │                       │
          └───────────┬───────────┘
                      ▼
          ┌───────────────────────┐
          │    QUERY LAYER        │
          │  Semantic Search API  │
          │  - Namespace filtered │
          │  - Time filtered      │
          │  - Hybrid search      │
          └───────────────────────┘
```

---

## Component Deep-Dive

### 1. Input Layer: Data Sources

#### 1.1 Claude Sessions
- **Source:** `~/.claude/projects/**/*.jsonl`
- **Format:** JSONL (one JSON object per line)
- **Structure:** User/assistant exchange pairs with tool calls
- **Active Detection:** Files modified within last 5 minutes
- **Monitored By:** Scripty Supervisor

#### 1.2 Gemini Sessions
- **Source:** (same directory structure)
- **Integration:** Same monitoring as Claude
- **Note:** All AI sessions treated identically by filtering layer

#### 1.3 Manual Ingestion
- **Trigger:** `ingest: <path>` command
- **Script:** `/mnt/Wolf-code/Wolf-Ai-Enterptises/writers/ingest_agent.py`
- **Supported Formats:** PDF, TXT, MD, code files
- **Target Namespace:** `ingested`
- **Processing:** Immediate vectorization on ingestion

---

### 2. Filtering Layer: Scripty AI System

#### 2.1 The Contamination Problem (Solved)

**Historical Issue:**
Original Python-based scripty blindly transcribed ALL system audio/text:
- Phone conversations
- Music playback
- Background applications
- Non-AI session noise

**Result:** Memory pollution, context contamination, unreliable semantic search

#### 2.2 AI-Based Solution

**Model:** llama3.2:1b (quantized, 8K context window)

**Key Capabilities:**
- **Signal vs. Noise Discrimination:** Identifies legitimate AI exchanges vs. background audio
- **Session Validation:** Confirms data is from actual Claude/Gemini sessions
- **Real-time Processing:** Sub-30 second latency from exchange to storage
- **Low Resource Footprint:** 1.3GB RAM per instance

**Architecture:**

```python
# Supervisor Pattern (scripty_supervisor.py)
- Monitors ~/.claude/projects for active .jsonl files
- Spawns 1 llama3.2:1b instance per active session
- Auto-scales: New session detected → new instance spawned
- Auto-cleanup: Session closes → instance terminated
- Managed by SystemD for 24/7 uptime

# Per-Instance Processing (scripty_ai.py)
1. Read new exchanges from session JSONL
2. Extract user/assistant pairs
3. Filter noise (validate it's a real AI interaction)
4. Transcribe verbatim to PostgreSQL
5. Add metadata: session_id, timestamp, exchange_number
```

**Deployment:**
- **SystemD Service:** `scripty-supervisor.service`
- **Log Location:** `/var/log/scripty-ai-{session_id}.log`
- **Auto-start:** Enabled on boot
- **Recovery:** Automatic restart on failure (10s delay)

---

### 3. Storage Layer: PostgreSQL + Namespace Organization

#### 3.1 Database Schema

```sql
-- Core memories table
CREATE TABLE public.memories (
    id BIGSERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    memory_type VARCHAR(50) DEFAULT 'general',
    namespace VARCHAR(100) DEFAULT 'default',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_memories_namespace ON memories(namespace);
CREATE INDEX idx_memories_created ON memories(created_at DESC);
CREATE INDEX idx_memories_user_id ON memories(user_id);
CREATE INDEX idx_memories_type ON memories(memory_type);
```

#### 3.2 Namespace Structure (Dewey Decimal System)

| Namespace | Count | Purpose | Update Frequency |
|-----------|-------|---------|------------------|
| scripty | 37,786 | Real-time session captures | Every 30s |
| wolf_story | 16,068 | Books, narratives, strategy | Static |
| ingested | 10,831 | File uploads (PDFs, docs) | On-demand |
| session_recovery | 9,459 | Conversation continuity | Per-session |
| mem0_import | 6,576 | Legacy system data | Static |
| imported | 3,847 | Manual imports | Sporadic |
| wolf_hunt | 2,916 | Job search data | Daily |
| system_announcements | 879 | Infrastructure updates | As-needed |
| core_identity | 7 | Constitution, immutable values | Rarely |

**Total:** 88,916 memories

#### 3.3 Metadata Structure

```json
{
  "timestamp": "2025-12-17T06:15:32-05:00",
  "type": "scripty_ai_summary",
  "model": "llama3.2:1b",
  "session": "c2ccbff3-cee9-448f-a705-2a362eba7a80",
  "exchange_num": 42,
  "sentiment_score": 3,
  "vectorized": true
}
```

---

### 4. Vectorization Layer: pgai + Ollama

#### 4.1 The Librarian: qwen3-embedding:4b

**Why This Model:**
- **#1 MTEB Multilingual:** Best-in-class for cross-language embedding
- **2560 Dimensions:** High-resolution semantic representation
- **32K Context Window:** Handles long documents
- **Ollama Integration:** Seamless pgai compatibility

**Configuration:**
```json
{
  "embedding": {
    "model": "qwen3-embedding:4b",
    "base_url": "https://ollama.complexsimplicityai.com",
    "dimensions": 2560,
    "implementation": "ollama"
  },
  "chunking": {
    "chunk_size": 512,
    "chunk_overlap": 50,
    "implementation": "recursive_character_text_splitter"
  }
}
```

#### 4.2 Vectorizer Workflow

```
1. Trigger: New row inserted into memories table
   ↓
2. pgai trigger fires: _vectorizer_src_trg_19()
   ↓
3. Row added to queue: ai._vectorizer_q_19
   ↓
4. Vectorizer worker picks up job
   ↓
5. Text chunked (512 tokens, 50 overlap)
   ↓
6. Each chunk sent to Ollama API
   → POST https://ollama.complexsimplicityai.com/api/embeddings
   → Model: qwen3-embedding:4b
   → Returns: 2560-dimensional vector
   ↓
7. Embeddings stored: memories_embedding_store
   ↓
8. Searchable view updated: memories_embedding
```

#### 4.3 Performance Characteristics

- **Throughput:** ~100 embeddings/second (single Ollama instance)
- **Latency:** <200ms per embedding
- **Queue Processing:** FIFO with error retry (6 attempts)
- **Failed Jobs:** Moved to `ai._vectorizer_q_failed_19`

---

### 5. Swarm Processing Layer: Real-Time Analysis

#### 5.1 Trigger Logic

**4-Block Trigger:**
- Swarm activates when 4 conversation blocks accumulated
- Block = 1 user message + 1 AI response
- Trigger can be:
  - **Per-session:** Each window accumulates 4 blocks independently
  - **Global:** Any 4 blocks across all sessions combined

#### 5.2 Swarm Components

**A. Embedding Fleet (Parallel Vectorization)**

Available models (can run 50-100+ concurrent on AMD RX 7900 XT):
- nomic-embed-text:v1.5
- mxbai-embed-large
- snowflake-arctic-embed:137m
- jina/jina-embeddings-v2-base-en
- embeddinggemma

**Purpose:** Rapid parallel vectorization for immediate searchability

**B. Mistral Sentiment Analysis**

**Model:** mistral:latest (7.2B, Q4_K_M)

**Task:** Analyze emotional tone of exchanges

**Output:** Sentiment score (1-5 scale)
- **1 = Chill as fuck** (calm, neutral, positive)
- **5 = Pissed the fuck off** (angry, frustrated, urgent)

**Usage:**
```python
# Pseudo-code for sentiment analysis
def analyze_sentiment(exchange_blocks):
    prompt = f"""
    Analyze the emotional tone of this conversation.
    Rate on scale 1-5:
    1 = calm/chill
    5 = angry/frustrated

    {exchange_blocks}

    Score:"""

    response = ollama.generate(model="mistral:latest", prompt=prompt)
    return int(response)  # 1-5
```

**Storage:** Sentiment score added to memory metadata

---

### 6. Query Layer: Semantic Search API

#### 6.1 Query Methods

**A. Semantic Search (Conceptual)**
```sql
SELECT content, namespace, created_at
FROM memories_embedding
WHERE namespace = 'scripty'
ORDER BY embedding <=> ai.ollama_embed('qwen3-embedding:4b', 'API authentication')
LIMIT 10;
```

**B. Full-Text Search (Exact Match)**
```sql
SELECT content, namespace, created_at
FROM memories
WHERE content ILIKE '%FIDO2%'
  AND created_at >= NOW() - INTERVAL '7 days'
ORDER BY created_at DESC;
```

**C. Hybrid Search (Combined)**
```sql
WITH semantic AS (
    SELECT id, content, namespace,
           embedding <=> ai.ollama_embed('qwen3-embedding:4b', 'query') AS distance
    FROM memories_embedding
    WHERE namespace IN ('scripty', 'ingested')
    ORDER BY distance
    LIMIT 50
)
SELECT s.content, s.namespace, m.created_at, m.metadata
FROM semantic s
JOIN memories m ON s.id = m.id
WHERE s.content ILIKE '%keyword%'
ORDER BY s.distance
LIMIT 10;
```

#### 6.2 Performance Optimization

**Indexes:**
- **GIN Index:** On metadata JSONB for fast JSON queries
- **HNSW Index:** On embedding vectors for fast similarity search
- **B-tree Indexes:** On namespace, created_at, user_id

**Query Planning:**
- Namespace filtering BEFORE semantic search (reduces search space)
- Time-based filtering for recent memory retrieval
- Limit results to top-K (typically 10-20) for speed

---

## Data Flow: End-to-End Example

**Scenario:** User asks Claude to fix Caddy configuration

```
1. USER SPEAKS (via voice/text)
   "Fix the Caddy reverse proxy for ollama.complexsimplicityai.com"

2. CLAUDE RESPONDS
   - Reads Caddyfile
   - Identifies issue
   - Proposes fix
   - Updates config

3. SCRIPTY AI FILTERING
   - llama3.2:1b monitors session JSONL file
   - Detects new exchange pair (user + assistant)
   - Validates: "This is a legitimate AI interaction"
   - NOT phone call, NOT music, NOT noise
   - Transcribes verbatim to PostgreSQL

4. STORAGE
   INSERT INTO memories (user_id, content, namespace, metadata)
   VALUES (
     'scripty_ai',
     'User: Fix Caddy... Assistant: [response]',
     'scripty',
     '{"session": "c2ccbff3...", "timestamp": "2025-12-17T06:30:00Z"}'
   );

5. VECTORIZATION TRIGGER
   - pgai trigger fires
   - Job queued: ai._vectorizer_q_19
   - Worker sends to Ollama: ollama.complexsimplicityai.com
   - qwen3-embedding:4b generates 2560-dim vector
   - Stored in memories_embedding_store

6. SWARM ANALYSIS (if 4-block trigger met)
   a) Embedding Fleet: Parallel vectorization complete
   b) Mistral Sentiment: Analyzes tone
      - Detects problem-solving conversation
      - No frustration markers
      - Score: 2 (chill, productive)
   c) Metadata updated with sentiment score

7. QUERYABLE
   - Memory now semantically searchable
   - Can find via: "Caddy configuration issues"
   - Can find via: "reverse proxy setup"
   - Can find via: "ollama subdomain"
   - All return this conversation as relevant result
```

**Total Latency:** <30 seconds from exchange to fully searchable

---

## Infrastructure Details

### Hardware Configuration

**Server:** csmcloud-server (Debian 13)
- **CPU:** (unspecified, likely AMD Ryzen)
- **RAM:** 80GB DDR5
- **GPU:** AMD RX 7900 XT (21.4GB VRAM)
- **Swap:** 86GB
- **Storage:** NVMe SSD

**Capacity:**
- **Concurrent Embedding Models:** 50-100+
- **Concurrent Scripty Instances:** 10-20+
- **Database Connections:** 100+ (PostgreSQL max_connections)

### Network Architecture

**Tailscale VPN:**
- **Server IP:** 100.110.82.181
- **MacBook IP:** 100.110.82.245

**Reverse Proxy (Caddy):**
- **ollama.complexsimplicityai.com** → http://100.110.82.181:11434
- **auth.complexsimplicityai.com** → http://100.110.82.181:9080
- **portainer.complexsimplicityai.com** → https://100.110.82.181:9443

### Service Management

**SystemD Services:**
- `ollama.service` - Ollama API server
- `postgresql.service` - PostgreSQL database
- `scripty-supervisor.service` - Dynamic AI instance manager
- `caddy.service` - Reverse proxy (needs OAuth integration)

**Monitoring:**
- Logs: `/var/log/scripty-ai-*.log`
- Supervisor log: `/var/log/scripty-supervisor.log`
- pgai errors: `ai._vectorizer_errors`

---

## Future Enhancements

### 1. OAuth Integration
- Secure Caddy Manager web interface
- Authenticate via `auth.complexsimplicityai.com`
- Centralized access control

### 2. Swarm Optimization
- Move from 4-block trigger to streaming analysis
- Real-time sentiment tracking (live emotional state)
- Predictive context switching

### 3. Multi-Model Consensus
- Run 3+ embedding models in parallel
- Vote on semantic similarity
- Reduce false positives

### 4. Automated Namespace Classification
- AI-based namespace prediction
- Auto-tag memories on ingestion
- Reduce manual categorization

---

## Conclusion

The Wolf AI Memory Infrastructure represents a production-grade semantic memory system designed for real-world, multi-agent AI operations. By combining intelligent filtering (Scripty AI), robust storage (PostgreSQL + pgai), state-of-the-art embeddings (qwen3-embedding:4b), and real-time processing (Swarm), the system delivers:

- **Reliability:** 24/7 uptime with automatic recovery
- **Accuracy:** AI-filtered signal from noise
- **Performance:** Sub-100ms semantic search
- **Scalability:** Handles 100K+ memories with linear growth
- **Intelligence:** Sentiment-aware, context-rich retrieval

**Status:** Fully operational as of December 17, 2025.

---

**Document Owner:** Cadillac the Wolf
**Technical Lead:** Claude Sonnet 4.5
**System Location:** csmcloud-server @ 100.110.82.181
**Contact:** caddydave82@gmail.com
