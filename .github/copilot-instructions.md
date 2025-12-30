# Copilot / AI Agent Instructions (project-specific)

Purpose: give AI coding agents exactly the local knowledge needed to be productive in this repo.

- Architecture (big picture):
  - This project is built as a fleet of small, single-purpose agents (scripts under `writers/`) rather than one monolith. Example agents: `writers/ingest_agent.py`, `writers/visual_agent.py`, `writers/audio_agent.py`, `writers/transcript_agent.py`, `writers/librarian.py`, `writers/youtube_analyst.py`.
  - Typical data flow: client/file → ingestion agent → PostgreSQL / pgai (pgvector) → worker(s) embed/process → MCP / FastAPI orchestration for sequential workflows. See data notes in `data/memory-dumps/*` for rationale and design discussions.
  - Agents are intended to be run as standalone processes (CLI or drop-zone file watcher) and should "just do one thing and exit" — fan-out is handled by workers and the DB queue.

- Developer workflows & commands (concrete examples found in repo notes):
  - Use the project's Python venv before running agents; example from project notes:

    source ~/anaconda3/bin/activate messiah && python writers/ingest_agent.py /path/to/file.pdf

  - YouTube/FFmpeg: some agents (YouTube analyst) require `ffmpeg` installed on the host.
  - Logs, outputs and reports appear under `output/logs` and `output/reports`.

- Project-specific patterns and conventions (do not improvise):
  - Single-responsibility agents: prefer adding a new script `writers/<name>_agent.py` over stuffing logic into a central server.
  - Don’t load big documents into central processes — dispatch file paths to `ingest_agent` and let the agent chunk/embed/insert into DB (see `writers/ingest_agent.py`).
  - Agents often add `agents/` or `writers/` to `sys.path` for imports (see `writers/youtube_analyst.py` "Add agents directory to path"). Follow existing import style.
  - Prompts and extraction templates live in code (example: `EXTRACT_PROMPT` in `writers/librarian.py`) — reuse these constants rather than inventing new top-level prompts.

- Integration points & external dependencies to be aware of:
  - PostgreSQL + pgvector / pgai: primary memory store and embedding queue. Many design notes reference inserting to DB and letting workers embed asynchronously.
  - Ollama and local LLM endpoints are mentioned in notes — agents expect to call model APIs (watch for blocking behaviour; prefer async/queued designs).
  - FastAPI-based MCP/gateway: sequential orchestration is implemented as a small API layer (search for `mcp/` references in `data/memory-dumps`).

- Code style & small implementation rules observed:
  - Keep agents small and synchronous at the CLI edge; offload heavy embedding to worker processes.
  - CLI usage strings are included in agents (e.g., `Usage: python writers/ingest_agent.py <filepath>`). Preserve these usage patterns.
  - When modifying ingestion or memory logic, update both the agent script and the DB worker assumptions (the codebase separates "dispatch" from "embedder").

- Where to look first (quick map for an agent):
  - `writers/` — primary agent scripts and example usage.
  - `data/memory-dumps/` — design notes and operational decisions (why agents are decoupled, concurrency notes).
  - `output/logs/` and `output/reports/` — runtime evidence for debugging.
  - `lib/` — utility scripts and helper shells (e.g., `protect_claude.sh`).

- If you need to change behavior, prefer this sequence:
  1. Read the agent script in `writers/` you will modify.
 2. Search `data/memory-dumps/*` for notes about intended behaviour (concurrency, DB queues, worker contracts).
 3. Run the agent locally with the referenced venv and CLI usage.
 4. Update any DB/worker contract or prompt constant alongside the agent change.

If anything above is unclear or missing (integration tokens, exact FastAPI entrypoint paths, or preferred venv name/location), tell me which area to expand and I will update this file.
