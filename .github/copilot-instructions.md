# Copilot / AI Agent Instructions (project-specific)

Purpose: give AI coding agents exactly the local knowledge needed to be productive in this repo.

## Architecture (big picture)
- This project is built as a fleet of small, single-purpose agents (scripts under `writers/`) rather than one monolith
- Key agents:
  - `writers/ingest/ingest_agent.py` - File ingestion and chunking
  - `writers/retrieval/librarian.py` - Semantic search and memory retrieval
  - `writers/analysis/*` - Various analysis agents
  - `writers/vectorization/*` - Embedding processing
  - `scripty/` - Automatic session capture (stenographer)
- Typical data flow: client/file → ingestion agent → PostgreSQL / pgai (pgvector) → worker(s) embed/process → MCP / FastAPI orchestration for sequential workflows
- Agents are intended to be run as standalone processes (CLI or drop-zone file watcher) and should "just do one thing and exit"
- Fan-out is handled by workers and the DB queue

## Environment Setup & Dependencies

### Python Environment
- Python 3.9+ required
- Use the project's Python venv before running any agents:
  ```bash
  source ~/anaconda3/bin/activate messiah
  # OR create new venv:
  python -m venv venv && source venv/bin/activate
  pip install -r requirements.txt
  ```

### External Dependencies
- **PostgreSQL 16+** with pgvector and pgai extensions
  - Default connection: `localhost:5433`
  - Database: `wolf_logic`
  - Setup scripts: `scripts/setup_local_postgres.sql`
- **Ollama** - Local LLM and embedding service
  - Required models: `qwen3-embedding:4b`, `bge-large:latest`, `mxbai-embed-large:latest`
  - Sync models: `scripts/sync_ollama_models.sh`
- **FFmpeg** - Required for video/audio processing agents
- **Tailscale** - For production mesh networking (optional for local dev)

### Configuration Files
- Database credentials hardcoded in agents (see `PG_CONFIG` in `writers/ingest/ingest_agent.py`)
- API endpoints: `api.complexsimplicityai.com` (production), `localhost` for local dev
- MCP server: `mcp-gateway/` directory

## Developer Workflows & Commands

### Running Agents (CLI)
```bash
# Activate environment first
source ~/anaconda3/bin/activate messiah

# Ingest a file
python writers/ingest/ingest_agent.py /path/to/file.pdf

# Run librarian search
python writers/retrieval/librarian.py "search query"

# Start MCP gateway
cd mcp-gateway && python fastapi_server.py
```

### Common Commands
- **No automated build** - Python scripts run directly
- **No automated tests** - Manual validation of agent outputs
- **Outputs**: Check `output/` directory for generated files
- **Start full stack**: `scripts/start_wolf_stack.sh`

### Database Operations
- **Local setup**: `psql -f scripts/setup_local_postgres.sql`
- **Sync from production**: `scripts/sync_from_181.py`
- **DB clients**: DataGrip or DBeaver (setup scripts in `data/` directory)


## Project-Specific Patterns & Conventions

### Agent Design Principles
- **Single-responsibility**: Prefer adding a new script `writers/<category>/<name>_agent.py` over adding logic to existing agents
- **File paths, not content**: Don't load big documents into central processes — dispatch file paths to `ingest_agent` and let the agent chunk/embed/insert into DB
- **Synchronous CLI, async workers**: Keep agents small and synchronous at the CLI edge; offload heavy embedding to worker processes
- **Usage strings**: All CLI agents include usage strings (e.g., `Usage: python writers/ingest/ingest_agent.py <filepath>`)

### Import Patterns
- Agents often add `agents/` or `writers/` to `sys.path` for imports
- Example pattern:
  ```python
  import sys
  import os
  sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'agents'))
  ```
- Follow existing import style when creating new agents

### Prompts & Templates
- Prompts and extraction templates live in code as constants (e.g., `EXTRACT_PROMPT` in `writers/retrieval/librarian.py`)
- Reuse these constants rather than inventing new top-level prompts
- Keep prompts version-controlled with the agent code

### Code Organization
```
writers/
├── ingest/          # File ingestion and processing
├── retrieval/       # Search and memory retrieval (librarian)
├── analysis/        # Analysis agents
├── vectorization/   # Embedding processing
├── utilities/       # Helper scripts
└── recruitment/     # Job-related agents
```

## Integration Points & External Dependencies

### Database Layer
- **PostgreSQL + pgvector + pgai**: Primary memory store and embedding queue
- Agents insert to DB, workers embed asynchronously
- Connection details in `PG_CONFIG` dictionaries within agent files
- Default port: `5433` (non-standard to avoid conflicts)

### Ollama & LLM Endpoints
- Local Ollama instance required for embeddings
- Agents expect to call model APIs via `ollama` Python library
- Watch for blocking behavior; prefer async/queued designs
- Multiple embedding models used in parallel (see `EMBED_FLEET` in `writers/ingest/ingest_agent.py`)

### MCP/Gateway Layer
- **FastAPI-based MCP/gateway**: Sequential orchestration implemented as small API layer
- Located in `mcp-gateway/` directory
- Handles MCP protocol communication with Claude and other AI clients

## Code Style & Implementation Rules

### General Principles
- Keep agents small and focused
- Offload heavy processing to worker processes
- CLI usage strings are mandatory in all agents
- When modifying ingestion or memory logic, update both agent script and DB worker assumptions
- Codebase separates "dispatch" from "embedder" concerns

### Error Handling
- Agents should fail gracefully and log errors
- Use thread-safe printing for concurrent operations (see `safe_print()` in `writers/ingest/ingest_agent.py`)
- Output files and error messages go to `output/` directory or stdout

### Database Operations
- Use connection pooling for concurrent operations
- Thread-safe DB operations when using ThreadPoolExecutor
- Namespace isolation for different data categories (e.g., `scripty`, `wolf_story`, `ingested`)

## Testing & Validation

### Current State
- **No automated test suite** - Manual validation of agent outputs
- Test files exist but are not part of CI/CD: `test_websocket.py`, `voice/test_client.py`
- Validation is primarily done by:
  1. Running agent with sample input
  2. Checking output files in `output/` directory
  3. Verifying database inserts via psql or DB client

### How to Validate Changes
1. Run the modified agent with test data
2. Check output files in `output/` directory for results
3. Query database to verify correct data insertion
4. Test integration with dependent agents/services

## Where to Look First

### Quick Navigation Map
- **`writers/`** - Primary agent scripts and example usage
- **`output/`** - Runtime output files for debugging
- **`lib/`** - Utility scripts and helper shells (e.g., `protect_claude.sh`)
- **`scripts/`** - Setup and operational scripts
- **`mcp-gateway/`** - MCP server implementation
- **`data/`** - Database dumps, session summaries, system announcements

### If You Need to Change Behavior

Follow this sequence:
1. **Read the agent script** in `writers/` you will modify
2. **Check for dependencies** - what other agents or services does it interact with?
3. **Run the agent locally** with the referenced venv and CLI usage
4. **Update related components**:
   - Agent script logic
   - DB schema if needed
   - Worker contracts if embedding logic changes
   - Prompt constants if LLM interactions change
5. **Test end-to-end** - verify the full data flow works

## Troubleshooting

### Common Issues

**"Connection refused" on PostgreSQL**
- Check if PostgreSQL is running: `pg_isready -h localhost -p 5433`
- Verify port 5433 is not in use by another service
- Check Tailscale is running if accessing remote DB

**"Model not found" from Ollama**
- List available models: `ollama list`
- Pull required model: `ollama pull qwen3-embedding:4b`
- Run sync script: `scripts/sync_ollama_models.sh`

**Agent crashes with import errors**
- Verify virtual environment is activated
- Install requirements: `pip install -r requirements.txt`
- Check sys.path modifications in agent script

**Database schema mismatch**
- Re-run setup script: `psql -h localhost -p 5433 -U wolf -d wolf_logic -f scripts/setup_local_postgres.sql`
- Check for migration scripts in `data/` or `deployment/`

### Getting Help
If anything above is unclear or missing (integration tokens, exact FastAPI entrypoint paths, or preferred venv name/location), ask for clarification and this file will be updated.
