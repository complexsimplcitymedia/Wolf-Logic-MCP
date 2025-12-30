# Repository Guidelines

## Project Structure & Module Organization
- Core backend lives in `backend.py` (Flask API on port 2500) and serves the built UI from `wolf-ui/build`.
- Frontend is in `wolf-ui/` (React + TypeScript). Static assets live under `public/` and feature styling under `src/*.css`.
- Operational scripts sit in `wolf_scripts/` (stack control, health checks, data movers) and are invoked by the UI and shell wrappers.
- Container orchestration is defined in `docker-compose.yml`; service units are in `wolf-logic-backend.service` and `wolf-logic-frontend.service`.
- Entry points for local operation and provisioning: `start-wolf.sh` (full stack), `start.sh`/`start-wolf.sh --status|--stop` helpers, and `bootstrap-wolf.sh` for host prep.

## Build, Test, and Development Commands
- Full stack: `./start-wolf.sh` to start, `./start-wolf.sh --status` to check, `./start-wolf.sh --stop` to halt.
- Backend only: `python3 backend.py` (serves API + built UI); export `FLASK_ENV=development` for verbose logs.
- Frontend dev server: `cd wolf-ui && npm start` (port 3333 via `react-scripts` with proxy to backend).
- Frontend build: `cd wolf-ui && npm run build` (outputs to `wolf-ui/build/` consumed by Flask/nginx).
- Frontend tests: `cd wolf-ui && npm test` (Jest via `react-scripts`, watch mode by default).

## Coding Style & Naming Conventions
- Python: follow PEP8, 4-space indents; prefer small, pure helpers; keep script paths relative to repo root unless the service requires absolute paths.
- React/TS: 2-space indents; components in PascalCase (`ControlPage.tsx`), hooks/utilities in camelCase; favor functional components with typed props.
- Use single quotes in JS/TS files to match current sources; keep imports ordered (core libs, third-party, local).
- Keep env/config values out of code; use script flags or env vars instead of hardcoding credentials.

## Testing Guidelines
- UI tests live beside components as `*.test.tsx`; cover routing, component rendering, and API edge cases (mock fetch/axios).
- For backend changes, add lightweight checks (e.g., `pytest` or ad-hoc `tests/` folder) that hit key endpoints; document any manual steps if automation is missing.
- Before opening a PR, run `npm test` (UI) and a quick smoke of the Flask API (`curl localhost:2500/health` if available).

## Commit & Pull Request Guidelines
- Commits: short, imperative subject lines; include scope when helpful (e.g., `ui: tighten memory page polling`, `backend: harden gpu metrics`).
- Pull requests: include a brief summary, testing notes (commands run), affected services/scripts, and screenshots/GIFs for UI changes.
- Mention config impacts (ports, service names, credentials) and link to any tracked issue or deployment note.

## Security & Configuration Tips
- Secrets in README are for local dev only; never re-check them in or echo them to logs. Prefer env vars for MariaDB/Neo4j/Postgres/API keys.
- Validate ports against `docker-compose.yml` and systemd unit files before changing them to avoid breaking the gateway/stack expectations.
