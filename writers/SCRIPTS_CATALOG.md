# Writers Department - Script Catalog

## INGEST (File → pgai Pipeline)
- `ingest/ingest_agent.py` - Main ingestion agent (PDF, text files → chunked + vectorized → pgai)
- `ingest/ingest_agent_api.py` - API wrapper for ingestion endpoint
- `ingest/bulk_import.py` - Bulk data import operations

## ANALYSIS (Media Processing)
- `analysis/youtube_analyst.py` - YouTube coordinator (Editor - dispatches to specialists)
- `analysis/visual_agent.py` - Frame-by-frame visual analysis (Lighting Dept - Llama 3.2 Vision)
- `analysis/audio_agent.py` - Audio mood/energy analysis (Post-Sound Dept)
- `analysis/transcript_agent.py` - Captions/transcription extraction (Sound Dept)

## RETRIEVAL (Memory Access)
- `retrieval/librarian.py` - Semantic memory search (nomic-embed-text primary)
- `retrieval/librarian_fleet.py` - Parallel memory processing with embed fleet
- `retrieval/load_session_context.py` - Load relevant context for new sessions
- `retrieval/rank_memories.py` - Rank and score memories for relevance

## VECTORIZATION (Embedding Generation)
- `vectorization/process_verbatim.py` - Process and vectorize verbatim transcripts
- `vectorization/process_verbatim_optimized.py` - Optimized parallel version

## UTILITIES (System Operations)
- `utilities/context_monitor.py` - Monitor Claude context usage
- `utilities/session_manager.py` - Session lifecycle management
- `utilities/postgres_to_neo4j_etl.py` - ETL pipeline between databases

---
**Last Updated:** $(date)
**Total Scripts:** 16
