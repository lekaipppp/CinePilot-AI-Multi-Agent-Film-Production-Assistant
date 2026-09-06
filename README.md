# CinePilot AI

CinePilot is a multi-agent film pre-production assistant. Paste or upload a
screenplay and six AI agents take it from raw script to a finished
pre-production package: scene breakdown, real-world filming location
candidates, a shoot schedule, a cost estimate, a risk register, and a
combined PDF report — each building on the previous agent's output.

## Architecture

Every agent is a Google ADK `LlmAgent` running on Gemini
(`model=settings.GEMINI_MODEL`, see `backend/app/config/settings.py`),
invoked through a `google.adk.runners.Runner` in its own
`backend/app/services/*_runner.py`. Pipeline order:

1. **Director** (`backend/app/agents/director_agent.py`) — parses the raw
   screenplay text into structured scenes: heading, interior/exterior,
   time of day, weather, characters, props, and shooting requirements.
   Weather is extracted from the screenplay text itself (e.g. "EXT. SALT
   FLATS - DAWN... wind howls") — there is no weather API in this project.
2. **Location** (`backend/app/agents/location_agent.py`) — does not search
   the web itself. `backend/app/api/v1/locations.py` first calls
   `search_location_candidates()` in `backend/app/services/parallel_search.py`
   (Parallel's Search API) to find real candidate venues per scene, then
   hands those results to the Location Agent, which ranks and scores them
   against the scene's requirements and the user's constraints. Results are
   then geocoded (`backend/app/services/geocoding.py`).
3. **Scheduler** (`backend/app/agents/scheduler_agent.py`) — groups scenes
   into shoot days, assigns call times, and flags scheduling conflicts
   (e.g. cast/crew/weather clashes) as constraints with a severity.
4. **Budget** (`backend/app/agents/budget_agent.py`) — estimates costs
   across five categories (locations, equipment, crew, transportation,
   contingency) against a target budget and currency.
5. **Risk** (`backend/app/agents/risk_agent.py`) — cross-references scenes,
   confirmed locations, the schedule, and the budget to surface risks
   across five fixed categories: Weather, Permits, Budget, Scheduling,
   Safety.
6. **Report** (`backend/app/agents/report_agent.py`) — synthesizes an
   executive summary and cross-cutting highlights from every agent that has
   run so far; the frontend then renders one combined document and exports
   it to PDF client-side.

Each agent's Pydantic `output_schema` is defined in `backend/app/schemas/`
(or alongside the agent for Director/Location) and validated on the way out
of the runner — the model can't return anything the schema doesn't allow.

## Tech stack

**Backend** — FastAPI, Google ADK (`google-adk`) + Gemini, the `parallel-web`
SDK for location search, `httpx` for outbound HTTP. `sqlalchemy`, `asyncpg`,
`alembic`, and `passlib`/`python-jose` are in `requirements.txt` for an
unfinished, disabled auth feature (see [Setup & run](#setup--run)) — no
database is required to run the app today.

**Frontend** — Next.js 16 (App Router), React 19, Tailwind CSS v4,
`react-leaflet`/Leaflet for the location map, `jspdf` + `html2canvas-pro`
for client-side PDF export, `pdfjs-dist` for client-side PDF text extraction
on script upload.

**Geocoding** — Nominatim (OpenStreetMap, free, no API key) is the primary
geocoder; Mapbox is an optional fallback used only when Nominatim fails to
resolve a query (`backend/app/services/geocoding.py`).

## Prerequisites

- **Python 3.13** — pinned in `.python-version` at the repo root.
- **Node.js** — TODO: no `engines` field in `frontend/package.json` and no
  `.nvmrc` in the repo, so the minimum supported version isn't pinned
  anywhere. Next.js 16 / React 19 need a reasonably recent LTS Node; verify
  against your local install rather than assuming.
- **API keys**:
  - `GOOGLE_API_KEY` (**required**) — Gemini API key, from
    [Google AI Studio](https://aistudio.google.com/app/apikey). Every agent
    call fails without it.
  - `PARALLEL_API_KEY` (**required** for location search) — from
    [Parallel](https://parallel.ai). Without it, `POST
    /api/v1/locations/search` fails with a 502; every other endpoint still
    works.
  - `MAPBOX_TOKEN` (optional) — from [Mapbox](https://www.mapbox.com).
    Falls back silently to Nominatim-only geocoding if unset.

See `backend/.env.example` for the full list with details.

## Setup & run

### Backend

Run from the **repo root** — `main.py`/`router.py` use absolute imports
(`from backend.app.api.router import api_router`) that only resolve when the
process starts there.

```bash
python3.13 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp backend/.env.example .env      # repo root, not backend/.env — python-dotenv
                                   # loads .env from the current working directory
# edit .env and fill in GOOGLE_API_KEY, PARALLEL_API_KEY, and (optionally) MAPBOX_TOKEN

uvicorn backend.app.main:app --reload --port 8000
```

The API is now at `http://localhost:8000`, routes under `/api/v1` (e.g.
`POST /api/v1/screenplay/analyze`).

**Database migrations**: not applicable. There's no `alembic.ini` or
`migrations/` directory in this repo — Alembic is listed in
`requirements.txt` but never configured, because the auth feature that would
need it (`backend/app/api/v1/auth.py`) is written but not wired into
`backend/app/api/router.py` (its import there is commented out). Nothing to
migrate; the app runs with no database.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local        # only needed if the backend isn't at
                                   # http://localhost:8000
npm run dev
```

The app is now at `http://localhost:3000`.

## Where Google Cloud and Parallel are used

**Gemini (Google Cloud / Google AI)** — every agent is a Google ADK
`LlmAgent` calling Gemini:

- `backend/app/agents/director_agent.py`, `location_agent.py`,
  `scheduler_agent.py`, `budget_agent.py`, `risk_agent.py`,
  `report_agent.py` — each defines an `LlmAgent(model=settings.GEMINI_MODEL, ...)`.
- `backend/app/services/{director,location,scheduler,budget,risk,report}_runner.py`
  — each wraps its agent in a `google.adk.runners.Runner` and drives it with
  `runner.run_async(...)`.
- `backend/app/config/settings.py` — `Settings.GEMINI_MODEL` (env-configurable
  model choice, read via `pydantic_settings.BaseSettings`).
- The Gemini API key itself (`GOOGLE_API_KEY`) is read directly by the
  underlying `google-genai` SDK, not by any code in this repo.
- Deployment target is Cloud Run: `Procfile` (repo root) runs
  `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`, with
  `.python-version` and `.gcloudignore` also at the repo root for the
  buildpack build.

**Parallel** — powers real-world location discovery:

- `backend/app/services/parallel_search.py` —
  `execute_parallel_search()` calls the Parallel SDK directly
  (`Parallel(api_key=...).search(...)`); `search_location_candidates()` is
  the async entrypoint that builds the query and calls it.
- `backend/app/api/v1/locations.py` — the `POST /locations/search` endpoint
  (`search_locations()`) calls `search_location_candidates()` first, then
  feeds its results into the Location Agent via `location_runner()`.

## License

MIT — see [`LICENSE`](LICENSE).
