# Crowd-O-Holic — Real-Time Crowd Flow Optimisation & Safety Dashboard

> **Crowd-O-Holic** is a crowd-flow simulation and operational safety dashboard for exploring how people move through a venue, identifying potential congestion and bottlenecks, testing emergency scenarios, and evaluating alternative routes. The project combines a React + TypeScript dashboard with an optional FastAPI backend for simulation, metrics, risk analysis, routing, and AI-assisted scenario interpretation.

**Project status:** Prototype / decision-support demo. It currently includes a generated demo venue and simulated crowd agents. It should not be represented as a production emergency-management system or as live CCTV analytics unless a real camera/video ingestion and computer-vision pipeline is separately implemented and integrated.

---

## Contents

- [Overview](#overview)
- [Problem statement](#problem-statement)
- [Goals](#goals)
- [Key capabilities](#key-capabilities)
- [How it works](#how-it-works)
- [Architecture](#architecture)
- [Technology stack](#technology-stack)
- [Repository structure](#repository-structure)
- [Requirements](#requirements)
- [Run locally](#run-locally)
  - [Option A: Frontend demo mode](#option-a-frontend-demo-mode-no-backend-required)
  - [Option B: Frontend with FastAPI backend](#option-b-frontend-with-fastapi-backend)
- [Environment configuration](#environment-configuration)
- [API reference](#api-reference)
- [WebSocket updates](#websocket-updates)
- [Simulation and safety concepts](#simulation-and-safety-concepts)
- [AI provider configuration](#ai-provider-configuration)
- [Tests and code quality](#tests-and-code-quality)
- [Deployment guide](#deployment-guide)
- [Troubleshooting](#troubleshooting)
- [Limitations and responsible use](#limitations-and-responsible-use)
- [Roadmap ideas](#roadmap-ideas)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

Crowd-O-Holic presents a venue operations interface with a central crowd-flow map and supporting panels for operational controls, simulation metrics, safety alerts, bottleneck analysis, emergency scenarios, route alternatives, and AI-assisted analysis.

The repository contains two main applications:

1. **Frontend** — a browser-based dashboard built with React, TypeScript, and Vite. It includes a local mock/simulation engine so the interface can be explored without starting the backend.
2. **Backend** — a Python FastAPI application that owns the server-side simulation engine, venue graph, metrics and risk calculations, emergency state, dynamic routing, optional AI provider, REST endpoints, and WebSocket updates.

The backend creates a default simulation for the demo venue `venue-stadium-a` during startup. The frontend can either use its local mock engine or connect to the backend when the backend URLs are configured.

## Problem statement

Large venues such as stadiums, arenas, campuses, transit hubs, and event grounds can experience uneven crowd distribution. Narrow passages, gate closures, sudden incidents, or high arrival rates may cause queues and congestion. Operators need a way to explore crowd movement, notice developing risks, and compare response options before or during an operational exercise.

Crowd-O-Holic provides a **simulation-based decision-support interface** for exploring those situations. It is intended to help demonstrate the relationship between crowd density, venue capacity, bottlenecks, emergency events, and route selection.

## Goals

- Visualise crowd movement across a venue topology.
- Simulate crowd entry, movement, queuing, and exit.
- Surface crowd-density, capacity-utilisation, and risk indicators.
- Identify persistent bottlenecks and growing queues.
- Explore alternative routes when an edge becomes unavailable or congestion changes.
- Configure scenarios and simulation controls.
- Trigger and clear simulated emergency events.
- Provide AI-assisted interpretation of scenario descriptions and safety context when configured.
- Offer both a frontend-only demo path and a backend-connected path.

## Key capabilities

### Operations dashboard
- Configure and monitor views.
- Simulation run controls, including start, pause, resume, stop, reset, and speed control where supported by the active mode.
- Central venue map with agents and route overlays.
- Map-layer toggles and a camera-context panel.
- A timeline and operational status indicators.

### Crowd and venue visualisation
- A graph-based venue representation with nodes and edges.
- Simulated agents moving through the topology.
- Route segments and alternative route visualisation.
- Venue and node inspection through the dashboard's inspector panel.

### Metrics and safety monitoring
- Crowd-density and capacity-utilisation indicators.
- Risk-level presentation and safety alerts.
- Bottleneck analysis based on configured density, utilisation, queue-growth, and persistence thresholds.
- A timeline for following changes during a simulation.

### Routing and emergency exercises
- Alternative paths when route segments are disabled or become unsuitable.
- Routing costs that can account for baseline travel cost, congestion, risk, and capacity.
- Simulated emergency types accepted by the backend include `fire`, `medical`, `structural`, `security`, `crowd-crush`, and `gate-failure`.
- Emergency activation and clearing are exposed through the API and safety desk.

### AI-assisted analysis
- Natural-language scenario parsing through a provider interface.
- A mock AI provider for development and demonstrations without a Hugging Face token.
- An optional Hugging Face-backed provider configured using environment variables.
- AI safety/scenario panels in the dashboard.

> **Data note:** The included camera-context UI is not proof of a connected CCTV feed. The supplied project includes demo/simulation logic; real camera ingestion, person detection/tracking, calibration, and validation would need to be implemented and tested separately.

---

## How it works

At a high level, the system follows this flow:

1. A user configures or starts a scenario from the dashboard.
2. The frontend either runs its local mock engine or sends requests to the FastAPI backend.
3. In backend mode, the API creates or controls a simulation using the selected venue graph, scenario parameters, and deterministic seed.
4. The simulation engine updates agent movement and queue state over simulation ticks.
5. Metrics and safety logic calculate crowd indicators and identify potential risk conditions.
6. The routing logic evaluates paths using configured costs and can find alternatives when route edges are disabled or conditions change.
7. The backend exposes snapshots through REST and broadcasts updates over a WebSocket connection.
8. AI-assisted scenario parsing or analysis uses the configured AI provider; if provider mode is `auto` and no Hugging Face token is set, the backend selects the mock provider.

This is a simulation pipeline, not an automatic feed from physical cameras or venue sensors.

---

## Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                    Browser / Frontend                       │
│  React + TypeScript + Vite                                  │
│                                                             │
│  Operations controls | Venue map | Metrics | Safety desk    │
│  Scenario assistant  | Bottlenecks | Routes | Emergency UI  │
└──────────────────────────┬──────────────────────────────────┘
                           │
              ┌────────────┴─────────────┐
              │                          │
       Local demo mode              Backend mode
       mockEngine.ts                REST + WebSocket
                                         │
┌────────────────────────────────────────┴────────────────────┐
│                    FastAPI backend                           │
│                                                             │
│  API routes ─ Simulation service ─ Simulation engine        │
│                    │                 │                      │
│               Venue graph       Agent movement / queues     │
│                    │                 │                      │
│             Dynamic routing    Metrics and risk engine      │
│                                      │                      │
│                               Bottleneck detection           │
│                                                             │
│  AI provider interface: mock provider or Hugging Face       │
│  WebSocket connection manager and snapshot broadcaster      │
│  SQLite-compatible persistence configuration                │
└─────────────────────────────────────────────────────────────┘
```

### Frontend
- **React 18** for UI components.
- **TypeScript** for typed application code.
- **Vite** for development server and production builds.
- **Lucide React** for interface icons.
- **Tailwind CSS / PostCSS** configuration is present alongside custom CSS.
- `src/state/SimulationContext.tsx` coordinates shared simulation and connection state.
- `src/services/backendClient.ts` contains backend communication logic.
- `src/services/mockEngine.ts` contains frontend mock/simulation logic.

### Backend
- **FastAPI** provides REST endpoints and WebSocket support.
- **Pydantic / pydantic-settings** validate data and load configuration.
- **Uvicorn** runs the ASGI application.
- Simulation, graph, metrics, risk, emergency, routing, realtime, and AI logic are separated into modules under `backend/app/`.
- **SQLAlchemy + aiosqlite** are dependencies, and the default database URL is SQLite-compatible. The database configuration should be checked against the specific features enabled in the current branch before production use.
- **pytest + pytest-asyncio + httpx** support automated tests.

---

## Technology stack

| Area | Technologies |
|---|---|
| Frontend framework | React 18 |
| Language | TypeScript |
| Frontend tooling | Vite 5 |
| Styling | CSS, Tailwind CSS, PostCSS |
| Icons | Lucide React |
| Backend framework | FastAPI |
| Backend language | Python 3.11+ |
| API/data validation | Pydantic, pydantic-settings |
| ASGI server | Uvicorn |
| AI integration | Provider abstraction; optional Hugging Face Hub integration |
| Persistence dependencies | SQLAlchemy, aiosqlite, Alembic |
| Testing | pytest, pytest-asyncio, httpx |
| Realtime | WebSockets |

---

## Repository structure

```text
Crowd-O-Holic/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ai/             # AI scenario and safety panels
│   │   │   ├── emergency/      # Emergency controls and banner
│   │   │   ├── layout/         # Header and connection overlay
│   │   │   ├── metrics/        # Metrics panel and related helpers
│   │   │   ├── routing/        # Route panel
│   │   │   ├── safety/         # Alerts, bottlenecks, timeline
│   │   │   ├── scenario/       # Scenario and simulation controls
│   │   │   └── venue/          # Venue map, camera wall, inspector, layers
│   │   ├── data/               # Frontend venue/demo data
│   │   ├── services/
│   │   │   ├── backendClient.ts
│   │   │   └── mockEngine.ts
│   │   ├── state/              # Shared simulation context
│   │   ├── types/              # TypeScript types
│   │   ├── utils/              # Display and venue helpers
│   │   ├── App.tsx
│   │   ├── index.css
│   │   └── main.tsx
│   ├── .env.example
│   ├── package.json
│   ├── package-lock.json
│   └── vite.config.ts
│
├── backend/
│   ├── app/
│   │   ├── ai/                 # AI schemas, prompts, provider implementations
│   │   ├── api/
│   │   │   ├── routes/         # Health, venues, scenarios, simulations, emergency
│   │   │   └── websocket.py
│   │   ├── core/               # Settings, logging, exceptions
│   │   ├── db/                 # Database-related module
│   │   ├── emergency/          # Emergency-state logic
│   │   ├── graph/              # Venue graph nodes, edges, graph
│   │   ├── metrics/            # Metric calculations
│   │   ├── realtime/           # WebSocket manager, events, broadcaster
│   │   ├── risk/               # Risk thresholds, engine, bottleneck logic
│   │   ├── routing/             # Dynamic route selection
│   │   ├── seed/                # Demo venue seed data
│   │   ├── services/            # Venue, simulation, AI services
│   │   └── simulation/          # Agents, queues, movement, state, engine
│   ├── tests/                   # Automated backend tests
│   ├── pyproject.toml
│   ├── uv.lock
│   └── start.bat
│
├── start-backend.bat
└── README.md
```

---

## Requirements

Install these before running the project:

- **Git** (for cloning/version control).
- **Node.js** with npm (a current LTS release is recommended).
- **Python 3.11 or newer**.
- A terminal such as PowerShell, Windows Terminal, macOS Terminal, or a Linux shell.
- Optional: a Hugging Face token if you want to use the configured hosted AI provider.

No NVIDIA GPU is required for the standard frontend demo or the deterministic backend simulation. The optional hosted AI provider uses a remote service rather than requiring a local GPU.

---

## Run locally

### 1. Get the source code

Clone your repository (replace the URL with your actual GitHub repository URL):

```bash
git clone https://github.com/<YOUR-USERNAME>/Crowd-O-Holic.git
cd Crowd-O-Holic
```

If you downloaded a ZIP instead, extract it and open the extracted project root in VS Code. The root should contain both `frontend/` and `backend/`.

### Option A: Frontend demo mode (no backend required)

This is the quickest way to open the dashboard. The frontend `.env.example` explicitly supports running with empty backend URLs, allowing local mock/simulation mode.

**Terminal 1 — install frontend dependencies**

```bash
cd frontend
npm install
```

Create a local `.env` file from the example if one does not already exist.

**Windows PowerShell:**

```powershell
Copy-Item .env.example .env
```

**macOS / Linux:**

```bash
cp .env.example .env
```

Keep these values empty for local mock mode:

```dotenv
VITE_BACKEND_URL=
VITE_WS_URL=
```

Start the development server:

```bash
npm run dev
```

Open the local URL printed by Vite, usually `http://localhost:5173`.

To create a production frontend build:

```bash
npm run build
```

To preview the built frontend locally:

```bash
npm run preview
```

### Option B: Frontend with FastAPI backend

Use this mode to run the server-side simulation and API.

#### 1. Start the backend

Open a terminal at the project root.

**Windows PowerShell:**

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

If PowerShell blocks activation, you can avoid activation and call the environment's Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**macOS / Linux:**

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The backend should be available at:

- API root: `http://127.0.0.1:8000/`
- Health check: `http://127.0.0.1:8000/health`
- Interactive API docs: `http://127.0.0.1:8000/docs`
- WebSocket: `ws://127.0.0.1:8000/ws/simulations/default`

The app startup code prepares a default simulation for `venue-stadium-a`.

#### 2. Configure the frontend to use the backend

Open a **second terminal**:

```bash
cd frontend
npm install
```

Create or edit `frontend/.env`:

```dotenv
VITE_BACKEND_URL=http://127.0.0.1:8000
VITE_WS_URL=ws://127.0.0.1:8000
```

Then start the frontend:

```bash
npm run dev
```

Open the Vite URL, usually `http://localhost:5173`.

> Vite reads environment variables when its dev server starts. If you change `frontend/.env`, stop and restart `npm run dev`.

#### 3. Verify the backend

Open `http://127.0.0.1:8000/health`. A healthy response should resemble:

```json
{
  "status": "ok",
  "version": "0.1.0",
  "ai_mode": "mock"
}
```

The `ai_mode` value may differ if you configure another provider. You can also open `/docs` to inspect and try the available API routes.

---

## Environment configuration

### Frontend (`frontend/.env`)

| Variable | Purpose | Local example |
|---|---|---|
| `VITE_BACKEND_URL` | Base URL for the FastAPI HTTP API | `http://127.0.0.1:8000` |
| `VITE_WS_URL` | Base URL used to form WebSocket connections | `ws://127.0.0.1:8000` |

Leave both blank for the frontend-only mock mode, as described in `.env.example`.

Vite variables prefixed with `VITE_` are exposed to browser-side code. **Never put secrets or private API tokens in frontend environment variables.**

### Backend environment variables

The backend uses `pydantic-settings`. Settings may be provided through environment variables or a `.env` file loaded relative to the backend process's working directory.

| Variable | Default / example | Purpose |
|---|---|---|
| `APP_NAME` | `Crowd Flow Optimiser` | Application display name |
| `APP_VERSION` | `0.1.0` | API version |
| `DEBUG` | `false` | Debug setting |
| `LOG_LEVEL` | `INFO` | Logging level |
| `CORS_ORIGINS` | Localhost origins | Allowed browser origins; configure for your deployed frontend |
| `HF_TOKEN` | empty | Optional Hugging Face access token |
| `HF_MODEL` | `Qwen/Qwen2.5-7B-Instruct` | Model identifier for the Hugging Face provider |
| `AI_PROVIDER_MODE` | `auto` | `auto`, `huggingface`, or `mock` |
| `AI_TIMEOUT` | `30.0` | AI request timeout in seconds |
| `AI_COOLDOWN_SIM_MINUTES` | `5.0` | Minimum simulation-time interval between AI calls |
| `SIMULATION_TIMESTEP` | `1.0` | Real-time seconds per simulation tick |
| `MAX_SIMULATION_DURATION` | `300.0` | Maximum configured simulation duration in simulation minutes |
| `REALTIME_UPDATE_HZ` | `2.0` | Target update broadcast rate |
| `MAX_AGENTS_RENDERED` | `1400` | Frontend-rendering agent cap |
| `DATABASE_URL` | `sqlite+aiosqlite:///./crowd_sim.db` | Database connection URL |
| `PERSISTENCE_FREQUENCY` | `10` | Configured summary persistence interval in ticks |

The backend also defines environment-configurable thresholds for risk density, utilisation, bottleneck detection, routing costs, and route stability in `backend/app/core/config.py`. Review that file for the full set of supported names and defaults.

For local mock AI mode, set:

```dotenv
AI_PROVIDER_MODE=mock
```

For automatic provider selection, set:

```dotenv
AI_PROVIDER_MODE=auto
```

In `auto` mode, the current configuration selects Hugging Face when `HF_TOKEN` is present and the mock provider when it is absent. To request Hugging Face explicitly, set `AI_PROVIDER_MODE=huggingface` and configure a valid token. Hosted model availability, permissions, rate limits, and provider API behaviour can affect AI calls.

**Security:** Add `.env` files to `.gitignore`. Commit only placeholder examples such as `.env.example`. If a token was ever committed to a public repository, revoke/rotate it; deleting it from the latest commit alone may not remove it from Git history.

---

## API reference

The backend's interactive API documentation is available at `/docs` when the server is running. The following endpoints are defined in the supplied source.

### Health

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Returns service status, version, and effective AI mode |
| `GET` | `/` | Returns app name/version plus links to docs and health |

### Venues

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/venues` | List available venues |
| `GET` | `/api/venues/{venue_id}` | Get a venue graph in frontend-compatible form |

### Scenarios

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/scenarios/parse` | Parse a natural-language scenario using the configured AI provider |

Example request:

```json
{
  "text": "A gate is closed and arrivals increase near the main entrance"
}
```

The exact parsed fields depend on the `ScenarioParseResult` schema and provider implementation. Check `/docs` for the current response model.

### Simulations

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/simulations` | Create a simulation |
| `GET` | `/api/simulations` | List simulation IDs |
| `GET` | `/api/simulations/{simulation_id}` | Get simulation status and summary counters |
| `GET` | `/api/simulations/{simulation_id}/state` | Get a current snapshot of simulation state, metrics, and safety data |
| `POST` | `/api/simulations/{simulation_id}/start` | Start the simulation |
| `POST` | `/api/simulations/{simulation_id}/pause` | Pause the simulation |
| `POST` | `/api/simulations/{simulation_id}/resume` | Resume a paused simulation |
| `POST` | `/api/simulations/{simulation_id}/stop` | Stop the simulation |
| `POST` | `/api/simulations/{simulation_id}/reset` | Reset simulation state |
| `POST` | `/api/simulations/{simulation_id}/speed` | Change simulation speed multiplier |

Example create request:

```json
{
  "venue_id": "venue-stadium-a",
  "seed": 42
}
```

The API also accepts an optional `scenario` object and optional `simulation_id`. If `scenario` is omitted or null, the backend uses its default scenario.

Example speed request:

```json
{
  "multiplier": 2.0
}
```

Use `/docs` to confirm accepted request constraints and response schemas for the version you are running.

### Emergency exercises

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/simulations/{simulation_id}/emergency` | Trigger a simulated emergency at a venue node |
| `DELETE` | `/api/simulations/{simulation_id}/emergency` | Clear the active simulated emergency |

Example request:

```json
{
  "type": "fire",
  "node_id": "REPLACE_WITH_A_VALID_NODE_ID"
}
```

Use a node ID that exists in the selected venue graph. The supported emergency type strings documented in the backend route are `fire`, `medical`, `structural`, `security`, `crowd-crush`, and `gate-failure`.

### WebSocket

| Type | Endpoint | Purpose |
|---|---|---|
| WebSocket | `/ws/simulations/{simulation_id}` | Receives connection status and simulation update events; may also accept client control messages |

The WebSocket endpoint sends a connection event and an initial snapshot when a valid simulation connection is established. The `default` simulation ID has special handling for creating a default simulation if needed.

---

## WebSocket updates

Backend mode uses a WebSocket connection to stream simulation snapshots to the UI.

Local development URL:

```text
ws://127.0.0.1:8000/ws/simulations/default
```

For a deployed HTTPS site, the corresponding secure WebSocket scheme is normally `wss://`. Set the frontend's `VITE_WS_URL` to the backend's public base URL using the appropriate scheme, for example:

```dotenv
VITE_BACKEND_URL=https://your-backend.example.com
VITE_WS_URL=wss://your-backend.example.com
```

Replace the example hostname with the real backend URL. Ensure the hosting platform supports WebSockets and that its proxy/timeouts are configured appropriately.

---

## Simulation and safety concepts

The following concepts are implemented across the backend modules and configuration. Their output is intended for simulation and demonstration.

- **Venue graph:** Nodes and edges represent locations and connections through a venue.
- **Agents:** Synthetic entities represent people moving through the graph.
- **Queues and movement:** Simulation logic models movement and queuing at the venue level.
- **Density:** A crowding indicator used by the risk engine.
- **Utilisation:** A measure of how much of a configured capacity is being used.
- **Risk levels:** Configurable thresholds classify crowd conditions into severity levels.
- **Bottlenecks:** Detection considers density, utilisation, queue growth, and persistence across ticks.
- **Dynamic routing:** Candidate paths are evaluated using baseline, congestion, risk, and capacity weights.
- **Route stability:** Cooldown and minimum-improvement settings help avoid excessive route changes.
- **Emergency state:** A simulated incident can affect venue state and routing decisions.
- **Reproducibility:** Simulation creation accepts a seed, making repeatable scenarios possible when the underlying implementation remains deterministic.

Default backend risk thresholds include density values of `0.35`, `0.60`, `0.80`, and `0.90` for progressively more severe levels; utilisation thresholds include `0.50`, `0.70`, and `0.85`. These are configuration defaults for the prototype, **not validated public-safety standards**. Tune and validate all thresholds against appropriate domain expertise and venue-specific data before any real-world use.

---

## AI provider configuration

The backend defines an AI provider interface with mock and Hugging Face implementations.

### Mock mode

Mock mode is useful for local development, repeatable demos, and testing without external model credentials.

```dotenv
AI_PROVIDER_MODE=mock
```

### Hugging Face mode

To use the hosted provider:

1. Create or obtain a Hugging Face access token with the permissions required by the selected model/provider.
2. Store it in the backend environment as `HF_TOKEN`.
3. Set `HF_MODEL` if you want to use a different supported model identifier.
4. Configure `AI_PROVIDER_MODE=huggingface` or use `auto` to select the provider when a token is present.
5. Restart the backend and inspect its logs and `/health` response.

Do not place the token in `frontend/.env`, source code, screenshots, or a public repository. Hosted inference is subject to model availability, provider permissions, latency, and rate limits. The rest of the simulation should be tested independently of the AI provider.

---

## Tests and code quality

Run backend tests from the `backend/` directory with the virtual environment activated:

```bash
pytest
```

For more verbose output:

```bash
pytest -v
```

The repository includes tests for API behaviour, simulation behaviour, graph logic, risk calculations, and AI provider behaviour. Test outcomes depend on the installed dependencies and the current source state.

Frontend checks are available from the `frontend/` directory:

```bash
npm run typecheck
npm run lint
npm run build
```

These commands respectively check TypeScript types, run ESLint, and create a production build. Resolve reported errors before deploying.

---

## Deployment guide

The application is split into a static frontend and a long-running API backend. They can be deployed separately.

### Frontend deployment

Suitable static hosting options include Netlify, Vercel, or another static host that supports Vite builds.

Typical settings:

- **Base directory:** `frontend`
- **Build command:** `npm run build`
- **Publish/output directory:** `dist`
- **Environment variables:**
  - `VITE_BACKEND_URL=https://YOUR-BACKEND-DOMAIN`
  - `VITE_WS_URL=wss://YOUR-BACKEND-DOMAIN`

If you intend to use only the frontend mock mode, leave both backend URL variables empty.

After changing Vite environment variables on the hosting platform, trigger a new build because Vite embeds these values into the generated client bundle.

### Backend deployment

Suitable hosting options include Render or another Python ASGI host that supports persistent web services and WebSockets.

Typical setup:

- **Root directory:** `backend`
- **Build/install command:** `pip install -e .`
- **Start command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

Set backend environment variables in the host's dashboard rather than committing them. At minimum, configure:
- `CORS_ORIGINS` to allow the deployed frontend origin.
- `AI_PROVIDER_MODE` and `HF_TOKEN` as needed.
- `DATABASE_URL` if you want a database location other than the default.

**Important deployment checks:**
1. Verify the host's Python version is 3.11 or newer.
2. Confirm the service binds to the platform-provided `$PORT`.
3. Test `/health` and `/docs` after deployment.
4. Configure CORS to include the exact frontend origin. The default CORS list is for local development and will not automatically include a deployed domain.
5. Confirm WebSocket connections work end-to-end through the hosting proxy.
6. Check whether the host's filesystem is persistent before relying on a local SQLite file for durable storage.
7. Review logging, exception handling, resource limits, and authentication before making the API publicly accessible.
8. Run the backend tests and frontend build before each release.

### Deployment environment examples

Frontend:

```dotenv
VITE_BACKEND_URL=https://your-backend.example.com
VITE_WS_URL=wss://your-backend.example.com
```

Backend:

```dotenv
CORS_ORIGINS=["https://your-frontend.example.com"]
AI_PROVIDER_MODE=mock
```

These are examples only. Use your actual deployed hostnames. Confirm how your hosting provider expects list-valued environment variables such as `CORS_ORIGINS` to be formatted.

---

## Troubleshooting

### Frontend cannot connect to backend
- Confirm the backend process is running and `/health` responds.
- Confirm `VITE_BACKEND_URL` uses the correct HTTP(S) base URL.
- Confirm `VITE_WS_URL` uses `ws://` locally or `wss://` for a secure deployed site.
- Restart Vite after editing the frontend `.env`.
- Check browser developer tools for CORS, HTTP, or WebSocket errors.

### CORS errors
- Add the exact frontend origin to the backend `CORS_ORIGINS` setting.
- Include the correct scheme and hostname; a different port counts as a different origin.
- Restart the backend after changing its environment.

### Backend fails to start
- Check that Python 3.11+ is installed.
- Ensure the terminal is in the `backend/` directory when running `uvicorn app.main:app`.
- Activate the intended virtual environment and install dependencies with `pip install -e .`.
- Read the first traceback error; later errors may be consequences of the first failure.

### AI calls fail
- Set `AI_PROVIDER_MODE=mock` to isolate the rest of the application from hosted AI availability.
- If using Hugging Face, verify `HF_TOKEN`, model access, network availability, and provider rate limits.
- Inspect backend logs for the actual provider error.

### Browser shows a blank page or stale UI
- Check the browser console.
- Run `npm run typecheck`, `npm run lint`, and `npm run build`.
- Confirm you opened the Vite URL printed in the terminal.
- Restart the development server after environment changes.

### Port is already in use
- Stop the process using port `5173` or `8000`, or choose a different port and update the frontend URLs accordingly.

### Frontend looks live but data is simulated
That is expected in mock/demo mode. The presence of moving agents, camera-context panels, or real-time UI updates does not by itself mean that physical CCTV or live venue sensors are connected.

---

## Limitations and responsible use

Crowd-O-Holic is a prototype for learning, simulation, and demonstration. It should not be the sole basis for evacuation, crowd-control, security, medical, or other emergency decisions.

Current repository scope includes a demo venue, synthetic/simulated agents, simulation metrics, routing, risk indicators, and optional AI-assisted interpretation. It does not establish that the project currently includes:
- Live CCTV stream ingestion.
- Computer-vision person detection or tracking.
- Camera calibration or conversion from pixels to real-world density.
- A validated model of pedestrian behaviour for a specific venue.
- Validated thresholds or certification for public-safety use.
- A production-grade alert delivery, authentication, audit, or access-control system.

Before real deployment, work with qualified crowd-safety professionals and venue operators; validate the simulation using measured venue geometry and observed data; assess false positives and false negatives; secure the API; test failure modes; and ensure operators can override system recommendations. Do not present simulated values as actual observed crowd counts.

---

## Roadmap ideas

Potential future extensions (not claims about current functionality):

- Integrate authorised CCTV/video sources or prerecorded footage.
- Add a computer-vision pipeline for detection and tracking, with privacy-aware processing.
- Calibrate camera views to estimate real-world density and flow.
- Support venue-specific floor plans, gates, capacities, and pedestrian connections.
- Compare predicted metrics against labelled or observed crowd data.
- Add authenticated operator roles, audit logs, and controlled emergency workflows.
- Add automated integration tests for REST and WebSocket behaviour.
- Add deployment health checks, monitoring, and documented backup/recovery procedures.
- Improve accessibility, responsive layouts, and operator usability.
- Add exportable scenario reports and replayable simulation sessions.

## Contributing

Contributions, bug reports, and improvement ideas are welcome.

Suggested workflow:

1. Fork the repository.
2. Create a feature branch.
3. Make a focused change and document any configuration updates.
4. Run backend tests and frontend checks.
5. Open a pull request with a clear description, screenshots where useful, and test results.

Please do not include API tokens, `.env` files, private CCTV footage, personal data, or other sensitive information in commits or issue attachments.

## License

No license file was present in the supplied project archive. Until a license is added, assume that standard copyright applies and that reuse, modification, and redistribution are not automatically granted. Add an appropriate `LICENSE` file if you want to define open-source permissions.

---

## Acknowledgements

Built as a software prototype exploring crowd-flow simulation, venue operations visualisation, risk indicators, dynamic routing, and AI-assisted scenario analysis.
