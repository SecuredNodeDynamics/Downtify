# AGENTS.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Stack and runtime
- Backend: Python FastAPI app (`main.py`, `downtify/`), managed with `uv`.
- Frontend: Vue 3 + Vite app (`frontend/`).
- Core media tooling expected on PATH for backend behavior: `ffmpeg`, `yt-dlp`.
- Default deployment/runtime is containerized (`Dockerfile`, `docker-compose.yml`), but local split frontend/backend development is supported.

## Development commands
Run from repository root unless noted.

### Install dependencies
```bash
uv sync
npm install --prefix frontend
```

### Run locally (recommended dev loop)
Terminal 1 (backend):
```bash
uv run python main.py
```

Terminal 2 (frontend with HMR):
```bash
npm run dev --prefix frontend
```

### Run app via Makefile helper
```bash
make run
```

### Tests
All tests:
```bash
make test
```
or explicitly:
```bash
npm run test --prefix frontend
uv run pytest -x -s -v
```

Single backend test:
```bash
uv run pytest tests/test_downloader.py::test_existing_filename_finds_file_in_root
```

Single frontend test file:
```bash
npm run test --prefix frontend -- src/__tests__/i18n.test.js
```

### Lint/format
Lint:
```bash
make lint
```

Format:
```bash
make format
```

Equivalent direct commands used by CI/Makefile:
```bash
uv run ruff check .
uv run ruff check . --diff
prettier --check frontend/src/.
```

### Build
Frontend production build:
```bash
npm run build --prefix frontend
```

Containerized local run:
```bash
make up
make down
```

## High-level architecture

### Request flow (big picture)
1. Frontend calls backend through `frontend/src/model/api.js` (Axios + WebSocket).
2. FastAPI routes in `downtify/api.py` orchestrate URL resolution, queueing, downloads, metadata scans, monitor operations, and settings.
3. Music resolution pipeline:
   - `downtify/spotify.py`: parse Spotify URLs and scrape Spotify embed/open endpoints for metadata (no Spotify API credentials).
   - `downtify/providers.py`: search/match YouTube Music (`ytmusicapi`) and normalize candidate tracks/albums.
   - `downtify/downloader.py`: download/convert/tag audio using `yt-dlp` + `ffmpeg` + `mutagen`.
4. Progress and async status updates are pushed to clients over `/api/ws`.

### Backend composition
- `main.py`:
  - Builds the FastAPI app, mounts SPA assets, configures CORS/logging.
  - Initializes shared state in `downtify.api.state` (settings, downloader, DB handles, semaphores).
  - Starts the playlist monitor loop on startup (`monitor_loop` from `downtify/monitor.py`).
- `downtify/api.py`:
  - Central API surface and in-memory app state (download jobs, scan status, active WebSocket clients).
  - Handles settings persistence (`/data/settings.json`) and runtime updates of downloader behavior.
  - Exposes operational endpoints: download queue/history, metadata repair scans, artist image scans, Jellyfin reconciliation/refresh, health/update checks.
- `downtify/monitor.py`:
  - SQLite-backed monitor state (`/data/downtify_monitor.db`) and periodic playlist checks.
  - Detects new playlist tracks and invokes downloader + optional M3U regeneration.
- `downtify/history.py` (used from API/main):
  - Download history persistence (`/data/download_history.db`) and retry bookkeeping.

### Frontend structure
- Router (`frontend/src/router/index.js`) maps top-level views: search/download/list/monitor/player/health/metadata.
- `frontend/src/model/api.js` is the backend contract layer (REST methods + singleton WebSocket session).
- `App.vue` renders global shell concerns (`StarField`, `Footer`, `Settings`) and route transitions.
- Feature-heavy pages are concentrated in `frontend/src/views/`, especially:
  - `Metadata.vue` for metadata repair, artist image workflows, and Jellyfin tools.
  - `Monitor.vue` for playlist watch management.

### Data and storage boundaries
- Audio output defaults to `/downloads` (overridable by settings/env).
- App settings and operational DBs live under `/data`.
- Built frontend assets served by backend from `frontend/dist`.
- Most long-running operations are async/background tasks surfaced via polling endpoints + WebSocket events.

## Existing assistant/tooling rules found in repo
- `.claude/settings.json` sets language to English.
