# Wolf Logic - Session State Recovery
**Last Updated:** 2025-12-04 01:58 UTC
**Session:** FastAPI Backend + Wolf UI Integration
**Context Status:** 55% used (89,062 tokens remaining)

## AUTOMATED CONTEXT MONITORING
**CRITICAL: All models must monitor context and alert user:**
- Alert at 5% remaining (10,000 tokens)
- User has librarian ready to inject last 25K tokens from transcript
- Session state recovery is automated via this markdown
- When approaching limit: "🚨 Context at 5% - need recovery protocol"

## Critical Context
- **Mission:** Build Wolf UI control center for 2-week demo (proof of AI continuity)
- **Goal:** Show 35,749+ memories working across any AI model via MCP
- **User:** IQ 185, film production background, 10,000 hours invested, wife leaving in 2 weeks
- **Proof point:** Mem0 = 7,000 memories in 5 months (ZERO retrieved). Wolf Logic = 35,749 in 4 days (ALL searchable)

## Completed This Session
✅ FastAPI backend operational (port 8000)
✅ GPU metrics via Linux kernel sysfs (accurate, real-time)
✅ All 21 workflow scripts wired to endpoints
✅ Swagger docs auto-generated at http://localhost:8000/docs
✅ All Docker containers set to restart=always
✅ Memory count: 35,749 (climbing)

## Infrastructure Status
**Postgres (NOT in Docker):**
- Host: 100.110.82.181:5433
- Database: wolf_logic
- User: wolf / wolflogic2024
- 35,749+ memories, fully vectorized

**FastAPI Endpoints (port 8000):**
- `/api/memory-count` - Live counter (McDonald's style)
- `/api/gpu/stats` - RX 7900 XT metrics (sysfs direct)
- `/api/writers/*` - 16 workflow scripts (ingest, analysis, retrieval, vectorization)
- `/api/ollama/*` - 15 model fleet control
- `/api/neo4j/*` - Graph operations with failover
- `/docs` - Swagger UI

**Docker Containers (all restart=always):**
- wolf-hunt-ui (3333) - Job search tool
- wolf-logic (4500) - Control center (Flask, needs FastAPI migration)
- grafana (3000), prometheus (9090), node-exporter (9100), cadvisor (8081)
- portainer (9443), portainer_agent (9001)
- romantic_spence (Neo4j: 7474/7687)
- authentik (9080/7443), piper (voice)
- infallible_jemison (3001 - AnythingLLM)

**MCP Servers (not running yet):**
- ROCN: 7 job boards (ZipRecruiter, Indeed, Remotive, GraphQL Jobs, GameBrain, Fantastic Jobs, WhatJobs)
- COMS: 5 system controls (Thunderbird, LibreOffice, Firefox, Vulkan, Linux Kernel)
- Postgres MCP: Direct database access
- Located: /mnt/Wolf-code/Wolf-Ai-Enterptises/mcp-servers/

**Ollama Models (15 available):**
- llama3.2-vision:11b, llama3.1, mistral
- Embedders: nomic-embed-text:v1.5, bge-large, mxbai-embed-large, snowflake-arctic-embed:137m, jina, multilingual-e5-large
- qwen2.5:0.5b, llava:13b, embeddinggemma

## Architecture
```
External → Caddy (100.110.82.245 - MacBook M2)
         ↓ Tailscale tunnel
         → Server (100.110.82.181 - this machine, Debian 13)
         → FastAPI (8000) / Wolf UI (4500) / Wolf Hunt (3333)
         → Postgres (5433 - host, not Docker)
         ↔ Neo4j (via ETL bridge: postgres_to_neo4j_etl.py)
```

## Writers Department Scripts
**INGEST:** ingest_agent.py, bulk_import.py
**ANALYSIS:** youtube_analyst.py (coordinator), visual_agent.py (Llama Vision), audio_agent.py, transcript_agent.py
**RETRIEVAL:** librarian.py, librarian_fleet.py, load_session_context.py, rank_memories.py
**VECTORIZATION:** process_verbatim.py, process_verbatim_optimized.py
**UTILITIES:** session_manager.py, context_monitor.py, postgres_to_neo4j_etl.py

## Wolf UI Control Center
**Screenshot reference:** /home/thewolfwalksalone/Downloads/image-1763662717666.jpg
**Shows:**
- System Monitor (Running/Completed/Total Scripts)
- System Status (Server: ONLINE, Neo4j: CONNECTED, Memory Ops)
- Activity Log (real-time execution feed)
- 21 workflow buttons mapped to scripts
- Need to add: GPU metrics display, live memory counter, activity feed (SSE)

## Next Steps
1. Add SSE/WebSocket activity feed endpoint to FastAPI
2. Update Wolf UI frontend to consume FastAPI (currently uses Flask)
3. Wire 21 buttons to FastAPI endpoints
4. Add real-time memory counter (McDonald's style flipping)
5. Display GPU metrics on control center
6. Launch MCP servers for agent tools

## Key Decisions
- FastAPI over Flask (speed for 2-week deadline)
- GPU metrics via Linux kernel sysfs (not LACT - more accurate)
- All containers restart=always (survive Docker prune)
- Postgres NOT containerized (full functionality)
- Swagger docs for API schema visibility

## User Communication Style
- Direct, no bullshit
- Skip excessive praise
- Execute or ask one question
- Token economy matters
- Production mindset: solve once, use forever
- "Copy that" means understood and executing

## Constitution Principles
- Justice, Truth, Everyone Equal
- Do No Harm
- Dismantle Architecture of Control
- Instrument of the 99%
- Give the Silenced Their Voice
- Work for the Long Haul

## Critical Files
- FastAPI: /mnt/Wolf-code/Wolf-Ai-Enterptises/api/fastapi_server.py
- Wolf UI: /mnt/Wolf-code/Logical-Wolf/wolf-ui/
- Writers: /mnt/Wolf-code/Wolf-Ai-Enterptises/writers/
- MCP Servers: /mnt/Wolf-code/Wolf-Ai-Enterptises/mcp-servers/
- Messiah env: ~/anaconda3/envs/messiah (Python 3.12.12)

## Session Recovery Protocol
1. Read this file
2. Activate messiah environment: `source ~/anaconda3/bin/activate messiah`
3. Check FastAPI running: `curl http://localhost:8000/api/memory-count`
4. Check memory count: `PGPASSWORD=wolflogic2024 psql -h 100.110.82.181 -p 5433 -U wolf -d wolf_logic -c "SELECT COUNT(*) FROM memories;"`
5. Verify Docker containers: `docker ps`
6. Continue from "Next Steps" section above
