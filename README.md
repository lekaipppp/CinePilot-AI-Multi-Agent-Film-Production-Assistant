
# CinePilot AI 🎬
### Multi-Agent Film Production Assistant

> A production-ready FastAPI backend that orchestrates a team of AI agents powered by **Gemini** and **LangGraph** to automate every stage of film pre-production — from script generation to location scouting, weather analysis, scheduling, and budgeting.

## Table of Contents

1. [Tech Stack](#tech-stack)
2. [Project Structure](#project-structure)
3. [Folder Responsibilities](#folder-responsibilities)
4. [Agent Pipeline](#agent-pipeline)
5. [API Endpoints](#api-endpoints)
6. [Setup & Running](#setup--running)
7. [Database Migrations](#database-migrations)
8. [Environment Variables](#environment-variables)
9. [Contributing](#contributing)


## Tech Stack

| Layer | Technology |
|---|---|
| Web Framework | FastAPI 0.115 |
| Runtime | Python 3.12 |
| ORM | SQLAlchemy 2.0 (async) |
| Database | PostgreSQL via Supabase |
| Migrations | Alembic |
| Validation | Pydantic v2 + pydantic-settings |
| AI Orchestration | LangGraph 0.2 |
| LLM | Google Gemini 1.5 Pro |
| Location Data | Google Maps + Google Places APIs |
| Weather Data | OpenWeather API |
| HTTP Client | httpx (async) |


## Project Structure

```
cinepilot-backend/
├── app/
│   ├── main.py                    # FastAPI app factory, lifespan, middleware
│   ├── deps.py                    # Shared FastAPI dependency callables
│   ├── exceptions.py              # Custom exception classes + handlers
│   │
│   ├── config/
│   │   └── settings.py            # Pydantic-settings: env vars & defaults
│   │
│   ├── api/
│   │   ├── router.py              # Top-level router (wires all v1 sub-routers)
│   │   └── v1/
│   │       ├── projects.py        # CRUD endpoints for projects
│   │       ├── scenes.py          # Scene management endpoints
│   │       └── agents.py          # Agent workflow trigger & status endpoints
│   │
│   ├── agents/
│   │   ├── script_writer_agent.py # Node: Generate film script draft
│   │   ├── scene_breakdown_agent.py # Node: Parse script into scenes
│   │   ├── location_scout_agent.py  # Node: Find filming locations
│   │   ├── weather_agent.py         # Node: Fetch weather per location
│   │   ├── scheduler_agent.py       # Node: Build shooting schedule
│   │   └── budget_agent.py          # Node: Estimate production budget
│   │
│   ├── services/
│   │   ├── project_service.py     # Business logic for projects
│   │   ├── agent_session_service.py # Persist & query agent sessions
│   │   ├── gemini_service.py      # Gemini API wrapper
│   │   └── location_service.py    # Google Maps + OpenWeather wrapper
│   │
│   ├── graph/
│   │   ├── state.py               # AgentState TypedDict (shared graph state)
│   │   └── graph.py               # LangGraph builder + compiled graph
│   │
│   ├── database/
│   │   ├── session.py             # Async engine, session factory, get_db()
│   │   └── repository.py          # Generic BaseRepository (CRUD pattern)
│   │
│   ├── models/
│   │   ├── base.py                # SQLAlchemy DeclarativeBase
│   │   ├── project.py             # Project ORM model
│   │   ├── scene.py               # Scene ORM model
│   │   └── agent_session.py       # AgentSession ORM model
│   │
│   ├── schemas/
│   │   ├── project.py             # ProjectCreate / ProjectRead / ProjectUpdate
│   │   ├── scene.py               # SceneCreate / SceneRead / SceneUpdate
│   │   ├── agent_session.py       # AgentRunRequest / AgentSessionRead
│   │   └── common.py              # Shared: PaginatedResponse, ErrorDetail
│   │
│   └── utils/
│       ├── logging.py             # Structured logger factory
│       ├── pagination.py          # Pagination param helpers
│       └── helpers.py             # UUID validation, slugify, etc.
│
├── alembic/                       # Database migration scripts
├── tests/
│   └── test_health.py             # Smoke test
├── .env.example                   # Environment variable template
├── alembic.ini                    # Alembic configuration
├── pyproject.toml                 # Pytest + Ruff configuration
├── requirements.txt               # Python dependencies
=======
# CinePilot-AI-Multi-Agent-Film-Production-Assistant
Multi-agent AI system that automates film pre-production — analyzes a screenplay to generate filming locations, shooting schedules, budget estimates, and risk analysis. Built with Gemini and Google Cloud Agent Builder for Agentic Cinema: The Blockbuster Hackathon.
# 🎬 CinePilot AI

> **An AI-powered multi-agent film production assistant that transforms screenplays into actionable production plans.**

![License](https://img.shields.io/badge/License-MIT-green)
![React](https://img.shields.io/badge/Frontend-React%20%2B%20Vite-61DAFB)
![Backend](https://img.shields.io/badge/Backend-Node.js-339933)
![AI](https://img.shields.io/badge/AI-Google%20Gemini-4285F4)
![Database](https://img.shields.io/badge/Database-Supabase-3ECF8E)

---

## 🌟 Overview

CinePilot AI is an intelligent multi-agent platform designed to assist filmmakers throughout the pre-production process. By leveraging Google's Gemini AI, specialized AI agents collaborate to analyze screenplays, generate shooting schedules, estimate budgets, identify production risks, and deliver a complete production strategy.

Whether you're an independent filmmaker or part of a production studio, CinePilot AI helps reduce planning time while improving production efficiency.

---

## 🚀 Features

- 📄 Upload screenplay files (.txt / .pdf)
- 🤖 Multi-Agent AI workflow
- 🎬 Automatic scene breakdown
- 📅 Intelligent shooting schedule generation
- 💰 Budget estimation
- ⚠️ Production risk analysis
- 📊 Interactive production dashboard
- ☁️ Cloud-based data storage with Supabase

---

## 🧠 AI Agent Workflow

```text
Upload Screenplay
        │
        ▼
Director Agent
        │
        ▼
Scene Breakdown
        │
 ┌──────┴─────────┐
 ▼                ▼
Scheduler      Budget
 Agent          Agent
        │
        ▼
Risk Agent
        │
        ▼
Producer Agent
        │
        ▼
Production Dashboard
```

---

## 🛠 Tech Stack

### Frontend
- React
- Vite
- Tailwind CSS

### Backend
- Node.js
- Express.js

### Artificial Intelligence
- Google Gemini API

### Database
- Supabase

### Deployment
- Vercel
- Render

### Version Control
- Git
- GitHub

---

## 📂 Project Structure

```text
CinePilot-AI
│
├── frontend
│   ├── src
│   ├── components
│   ├── pages
│   └── assets
│
├── backend
│   ├── routes
│   ├── controllers
│   ├── services
│   ├── middleware
│   └── utils
│
├── docs
│   ├── architecture
│   └── diagrams
│
>>>>>>> bacc3b92614d44e6d82a2105ddca91129355f36c
└── README.md
```

---

<<<<<<< HEAD
## Folder Responsibilities

### `app/config/`
Single source of truth for all configuration. [`settings.py`](app/config/settings.py) uses `pydantic-settings` so every value is type-checked and loaded from `.env` at startup. Nothing in the codebase reads `os.environ` directly.

### `app/api/`
**HTTP boundary only.** Routers receive requests, validate input via Pydantic schemas, call the appropriate service, and return responses. Zero business logic lives here. Versioning (`v1/`) is baked in from day one.

### `app/agents/`
Each file is a single **LangGraph node** — a pure async function `(AgentState) → AgentState`. Nodes are composable, testable in isolation, and contain only AI prompt logic. They never touch the database directly.

### `app/services/`
**Business logic layer.** Services own transactions, domain rules, and external API calls. They are the only layer that touches the database (via SQLAlchemy) or calls external services (Gemini, Maps, Weather). Routers depend on services; agents depend on services.

### `app/graph/`
Wires agent nodes into a **directed LangGraph workflow**. [`state.py`](app/graph/state.py) defines the shared `AgentState` TypedDict that flows between nodes. [`graph.py`](app/graph/graph.py) assembles the DAG and returns a compiled, reusable graph object.

### `app/database/`
Infrastructure plumbing: async SQLAlchemy engine, session factory, `get_db()` FastAPI dependency, and a generic `BaseRepository` to eliminate per-model CRUD boilerplate.

### `app/models/`
SQLAlchemy ORM models — the authoritative definition of the database schema. Models are imported by `main.py` lifespan so `metadata.create_all()` finds them.

### `app/schemas/`
Pydantic schemas that define the **API contract** (what the client sends and receives). Deliberately separate from ORM models to prevent accidental data leaks and to allow the API shape to evolve independently of the database.

### `app/utils/`
Stateless helper functions (logging, pagination, slugify, UUID checks) that are too small to be services but too reusable to inline everywhere.

---

## Agent Pipeline

```
Client Request (POST /api/v1/agents/run)
         │
         ▼
  LangGraph Graph (app/graph/graph.py)
         │
    ┌────┴────────────────────────────────────────┐
    │                                             │
    ▼                                             │
ScriptWriterAgent    ← Gemini: draft script       │
    ▼                                             │
SceneBreakdownAgent  ← Gemini: parse scenes       │
    ▼                                             │
LocationScoutAgent   ← Google Maps + Places       │
    ▼                                             │
WeatherAgent         ← OpenWeather API            │
    ▼                                             │
SchedulerAgent       ← Gemini: build schedule     │
    ▼                                             │
BudgetAgent          ← Gemini: estimate budget    │
    │                                             │
    └─────► AgentSession saved to PostgreSQL ─────┘
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness probe |
| `GET` | `/api/v1/projects/` | List projects |
| `POST` | `/api/v1/projects/` | Create project |
| `GET` | `/api/v1/projects/{id}` | Get project |
| `PATCH` | `/api/v1/projects/{id}` | Update project |
| `DELETE` | `/api/v1/projects/{id}` | Delete project |
| `GET` | `/api/v1/projects/{id}/scenes` | List scenes |
| `POST` | `/api/v1/projects/{id}/scenes` | Create scene |
| `PATCH` | `/api/v1/projects/{id}/scenes/{id}` | Update scene |
| `DELETE` | `/api/v1/projects/{id}/scenes/{id}` | Delete scene |
| `POST` | `/api/v1/agents/run` | Trigger agent workflow |
| `GET` | `/api/v1/agents/sessions/{id}` | Get agent session |
| `GET` | `/api/v1/agents/sessions` | List sessions by project |

Interactive docs → `http://localhost:8000/docs`

---

## Setup & Running

### 1 — Clone and create a virtual environment
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

### 2 — Install dependencies
```bash
pip install -r requirements.txt
```

### 3 — Configure environment
```bash
cp .env.example .env
# Open .env and fill in your API keys and DATABASE_URL
```

### 4 — Run database migrations
```bash
alembic upgrade head
```

### 5 — Start the development server
```bash
uvicorn app.main:app --reload --port 8000
```

---

## Database Migrations

```bash
# Generate a new migration after changing a model
alembic revision --autogenerate -m "describe your change"

# Apply migrations
alembic upgrade head

# Roll back one step
alembic downgrade -1
=======
## ⚙️ How It Works

1. Upload a screenplay.
2. The backend extracts the screenplay text.
3. The Director Agent analyzes scenes, characters, and locations.
4. The Scheduler Agent creates an optimized production schedule.
5. The Budget Agent estimates production costs.
6. The Risk Agent identifies conflicts and production challenges.
7. The Producer Agent combines all analyses into a complete production report.
8. Results are displayed on an interactive dashboard.

---

## 👥 Team

| Role | Responsibilities |
|------|------------------|
| Frontend Developer | UI/UX, Dashboard, API Integration |
| Backend Developer | APIs, Gemini Integration, Supabase |
| AI & Cloud Engineer | Prompt Engineering, Deployment, Documentation |

---

## 💡 Future Enhancements

- 🎥 AI Storyboard Generation
- 🌍 Multi-language screenplay support
- 🎭 Casting recommendation system
- ☁️ Real-time collaborative production planning
- 📈 Budget optimization suggestions
- 📱 Mobile application

---

## 📸 Screenshots

> Coming Soon

---

## 🎬 Demo

> Demo video will be added after deployment.

---

## 🚀 Getting Started

```

### Install frontend dependencies

```bash
cd frontend
npm install
npm run dev
```

### Install backend dependencies

```bash
cd backend
npm install
npm run dev
>>>>>>> bacc3b92614d44e6d82a2105ddca91129355f36c
```

## Environment Variables

See [`.env.example`](.env.example) for the full list. Key variables:

| Variable | Description |
|---|---|
| `DATABASE_URL` | Async PostgreSQL URL (`postgresql+asyncpg://...`) |
| `GEMINI_API_KEY` | Google Generative AI key |
| `GEMINI_MODEL` | Model name (default: `gemini-1.5-pro`) |
| `GOOGLE_MAPS_API_KEY` | Google Maps Geocoding key |
| `GOOGLE_PLACES_API_KEY` | Google Places Nearby Search key |
| `OPENWEATHER_API_KEY` | OpenWeather API key |
| `SECRET_KEY` | App secret for token signing |
| `DEBUG` | `true` enables SQL echo + DEBUG logs |


## Contributing

1. Create a feature branch: `git checkout -b feat/my-feature`
2. Make changes and run `pytest` to validate
3. Open a pull request with a clear description


*Built for the CinePilot AI Hackathon — powered by Gemini + LangGraph*
=======
## 🤝 Contributing

Contributions, feature requests, and suggestions are welcome.

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Open a Pull Request

## 📜 License

This project is licensed under the MIT License.

## ❤️ Acknowledgements

- Google Gemini
- Supabase
- React
- Vite
- Express.js
- Devpost
- Open Source Community

## ⭐ Support

If you like this project, consider giving it a **⭐ Star** on GitHub!
