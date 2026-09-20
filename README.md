# okDriver Integrated CCTV Monitoring, Video Analytics and Real-Time Alert Platform

A working prototype built for the okDriver Full Stack Developer hiring
assignment: camera registry, recorded/simulated video, an analytics
ingestion API with watchlist correlation and real-time alerting, an
operational dashboard, GIS camera/movement visualization, and audit
logging.

> **Honesty note on scope.** This is a hiring-assignment prototype, not a
> production system. Section 10 ("Known limitations") lists exactly what is
> and isn't implemented — in particular, no real RTSP/ONVIF camera
> connection exists (see `docs/architecture.md` §3 and §6). The two bundled
> sample videos are synthetically generated placeholders, not real CCTV
> footage (see `data/sample/README.md` for why, and how to swap in real
> footage).

## 1. Features

- JWT auth, bcrypt password hashing, role-based authorization (admin /
  operator) enforced server-side on every protected endpoint
- Camera registry: add / edit / enable / disable / search / filter,
  simulated heartbeat + threshold-based health status (online / degraded /
  offline), broadcast on health change
- Camera source adapter abstraction (recorded, simulated; documented
  RTSP/ONVIF/vendor-API stubs for future integration)
- Interactive Leaflet camera map with status/alert-aware markers
- Analytics event ingestion API: validation, idempotency-key duplicate
  rejection, persistence, watchlist correlation, alert generation, WebSocket
  broadcast — all in one request (the assignment's recommended core
  demonstration flow)
- Watchlist management: CRUD, exact-match identifier normalization
  (documented rule, no fuzzy matching), enable/disable
- Real-time alerting over WebSocket with automatic frontend reconnect;
  alert lifecycle (new → acknowledged → resolved) with enforced valid
  transitions
- Entity/vehicle search with chronological movement history and a route
  drawn on the map from persisted detection events only
- Audit logging on all sensitive admin/operator actions, with an
  admin-only viewing UI
- Alembic migrations + reproducible seed script with synthetic
  demonstration data
- Architecture diagram (`docs/architecture-diagram.png`/`.svg`) and
  database ER diagram (`docs/database-schema-diagram.png`/`.svg`), both
  rendered from Graphviz `.dot` sources and embedded in `docs/architecture.md`
  / `docs/database-schema.md`
- 18 automated backend tests (auth, authorization, camera validation,
  duplicate-event handling, watchlist matching incl. identifier
  normalization, alert lifecycle, movement-history ordering) — all passing
- Docker Compose (MySQL + backend + frontend)

## 2. Technology stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic 2 |
| Database | MySQL 8.0 |
| Auth | JWT (python-jose) + bcrypt (passlib) |
| Real-time | FastAPI WebSocket |
| Frontend | React 18, Vite, React Router, Axios, Leaflet / react-leaflet |
| Infra | Docker, Docker Compose |
| Testing | Pytest (backend); SQLite used only in the test suite for speed/isolation — the real deployment always uses MySQL |

## 3. Prerequisites

- Docker and Docker Compose (recommended path), **or**
- Python 3.12 + pip, Node.js 20+, and a running MySQL 8.0 instance for a
  manual/local setup

## 4. Quick start (Docker Compose)

```bash
cp .env.example .env        # edit JWT_SECRET and DB passwords for anything beyond local demo use
docker compose up --build
```

This will:
1. Start MySQL and wait for it to be healthy.
2. Start the backend, which runs `alembic upgrade head`, then `seed.py`,
   then the API server.
3. Start the frontend (served on port 5173).

Open:
- Frontend: http://localhost:5173
- API docs (Swagger): http://localhost:8000/docs
- Health check: http://localhost:8000/health

**Demo credentials** (created by `seed.py`):
- Administrator: `admin` / `Admin@12345`
- Operator: `operator` / `Operator@12345`

Two sample videos ship in `data/sample/` and are wired up by the seed
script automatically — video playback works immediately with no extra
setup. See `data/sample/README.md` for what they are (synthetic
placeholders, clearly labeled) and how to swap in real footage.

## 5. Deploying to Render

`render.yaml` at the repo root is a Render Blueprint that provisions all
three services in one go:

- `okdriver-mysql` — MySQL 8.0 as a private service with a persistent disk
  (Render has no managed MySQL product, only Postgres, so this runs the
  official `mysql:8.0` image directly)
- `okdriver-backend` — built from `backend/Dockerfile`
- `okdriver-frontend` — built from `frontend/Dockerfile`

### Steps

1. Push this repo to GitHub (or GitLab).
2. In the Render dashboard: **New +** → **Blueprint**, select the repo.
   Render reads `render.yaml` and shows all three services to create.
3. Click **Apply**. Render provisions `okdriver-mysql` first, then builds
   and deploys `okdriver-backend` and `okdriver-frontend`.
4. Once all three are live, open the frontend's `*.onrender.com` URL and log
   in with the seeded demo credentials (`admin` / `Admin@12345`).

### How the pieces are wired together

- The backend's DB connection is assembled from `MYSQL_HOST` / `MYSQL_PORT`
  / `MYSQL_USER` / `MYSQL_PASSWORD` / `MYSQL_DATABASE`, not a single
  `DATABASE_URL` string — `render.yaml` fills these in via `fromService`,
  pulling the MySQL private service's host/port and its generated password
  directly, so no secret is typed or committed anywhere.
- The backend's `CORS_ORIGINS` and the frontend's `API_BASE_URL` /
  `WS_BASE_URL` are filled in the same way, from each other's `host`
  property. Render's `fromService.host` returns a bare hostname with no
  `https://`/`wss://` prefix; `app/core/config.py` (backend) and
  `docker-entrypoint.sh` (frontend) both auto-prepend the right scheme, so
  this works without manual dashboard edits after deploy.
- The frontend does **not** bake `API_BASE_URL`/`WS_BASE_URL` into the
  Vite build. `docker-entrypoint.sh` regenerates `dist/env.js` from real
  environment variables every time the container starts, and
  `src/services/api.js` / `src/hooks/useDashboardSocket.js` read
  `window.__ENV__` first, falling back to the Vite build-time env (used for
  local `npm run dev`) and then to `localhost:8000`. This means the same
  built frontend image works unchanged in Docker Compose and on Render.
- Both `okdriver-backend` and `okdriver-frontend` bind to the `PORT` env var
  Render injects automatically (`uvicorn --port ${PORT:-8000}` in the
  backend Dockerfile; `serve -l ${PORT:-5173}` via the entrypoint script in
  the frontend).

### Things to check/adjust before relying on this for anything beyond a demo

- `okdriver-mysql` is a private service with a persistent disk, which
  requires a paid Render plan — there is no free tier for this service
  type. Adjust `plan:`/`region:` in `render.yaml` as needed, or swap in an
  external managed MySQL provider (set `MYSQL_HOST`/`MYSQL_PORT`/etc., or a
  full `DATABASE_URL`, to point at it instead) and delete the
  `okdriver-mysql` service block.
- The two bundled sample videos are baked directly into the backend Docker
  image (`COPY data/sample /media/sample` in `backend/Dockerfile`, built
  with the repo root as context), so video playback works on Render too,
  with no extra setup;
  video playback will show the documented "no preview available" state
  until you add real files to the image or point `stream_reference` at an
  externally hosted URL.
- `JWT_SECRET` and the MySQL passwords are set via Render's
  `generateValue: true`, so they're randomly generated per-deploy and never
  appear in the repo — you don't need to (and shouldn't) hardcode them.
- Render's free-tier web services spin down on inactivity; expect the first
  request after idle time to be slow while the backend and frontend cold
  start.

## 6. Manual local setup (without Docker)
### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Point at a MySQL instance you control, e.g.:
export DATABASE_URL="mysql+pymysql://okdriver:okdriver_password@localhost:3306/okdriver"
export JWT_SECRET="a-long-random-secret"

alembic upgrade head
python seed.py
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env   # adjust VITE_API_BASE_URL / VITE_WS_BASE_URL if needed
npm run dev
```

## 7. Environment variables

See `.env.example` at the repo root (Docker Compose) and
`frontend/.env.example` (local frontend dev). Key backend variables:

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | SQLAlchemy connection string (MySQL) |
| `JWT_SECRET` | Signing secret for access tokens — **must** be changed from the default before any non-local use |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime |
| `CORS_ORIGINS` | Comma-separated allowed frontend origins |
| `HEARTBEAT_OFFLINE_SECONDS` / `HEARTBEAT_DEGRADED_SECONDS` | Thresholds for the simulated heartbeat monitor |

## 8. Database setup, migrations, seed data

```bash
cd backend
alembic upgrade head   # creates all tables (see docs/database-schema.md)
python seed.py         # idempotent; safe to re-run
```

## 9. Running tests

```bash
cd backend
pip install -r requirements.txt
python -m pytest tests/ -v
```

18 tests currently pass, covering authentication, authorization boundaries,
camera CRUD/validation, duplicate-event rejection, watchlist matching
(including identifier normalization), alert lifecycle transitions, and
movement-history ordering.

## 10. Known limitations

- **No live RTSP/ONVIF/vendor-API camera support.** Only recorded-MP4 and
  simulated sources are functional; the other three are adapter stubs that
  raise `NotImplementedError` by design (see `docs/architecture.md`).
- **Bundled sample videos are synthetic, not real footage.** The two clips
  in `data/sample/` are generated placeholders (moving boxes standing in
  for vehicles, camera label and timestamp burned in) — they exercise the
  full playback pipeline but are clearly not real CCTV footage. See
  `data/sample/README.md` for why, and how to swap in real footage before
  a final submission.
- **Synchronous match-then-alert flow.** Watchlist correlation happens
  inline within the ingestion request for demo simplicity; `docs/scalability.md`
  §5 describes how this decouples at scale via a queue.
- **Single-process WebSocket manager** — connections are tracked in-memory,
  which is correct for one backend replica (as deployed here) but would need
  a pub/sub backbone (Redis/Kafka) to fan out across multiple replicas; see
  `docs/scalability.md` §2.
- **No rate limiting implemented** in this prototype (documented as a gap,
  not silently omitted) — see the "Security notes" below.
- **No CI/CD pipeline** configured.
- **The 3–5 minute screen-recorded demo video is not included in this
  repository** — recording it requires an actual run-through by whoever
  submits this assignment.

## 11. Security notes

- Passwords are bcrypt-hashed; never stored or logged in plaintext.
- No secrets are committed — `.env.example` contains placeholders only;
  real `.env` files are gitignored.
- Every protected endpoint checks the caller's role server-side; the
  frontend hiding a button is never the only protection.
- Stream references are stored as plain strings for this prototype and are
  never echoed with embedded credentials because none are used (sample
  files only) — a production system would resolve credentials from a
  secrets manager at adapter-connect time, not store them on the camera
  record.
- CORS is restricted to `CORS_ORIGINS`.
- SQL injection is prevented structurally: all queries go through
  SQLAlchemy's ORM/parameter binding, no raw string-interpolated SQL exists
  anywhere in the codebase.
- Rate limiting is **not** implemented — flagged as a limitation above
  rather than left silently absent.
- TLS termination is a deployment-time concern (reverse proxy / load
  balancer in front of the containers); see `docs/scalability.md` §6.

## 12. Project structure

```
backend/
  app/
    main.py            FastAPI app, router registration, static media mount
    core/               config, security (JWT/bcrypt/RBAC)
    api/v1/             route modules (auth, cameras, watchlist, analytics, alerts, entities, audit, ws)
    models/             SQLAlchemy models
    schemas/             Pydantic request/response schemas
    services/            matching, audit, heartbeat monitor
    websocket/           connection manager
    adapters/             camera source adapter abstraction
    db/                   session/engine/Base
  tests/                 pytest suite
  migrations/             Alembic env + versions
  seed.py
  requirements.txt
  Dockerfile

frontend/
  src/
    components/           Badge, Toast
    pages/                 Login, Dashboard, Cameras, Camera detail, Map, Watchlist, Alerts, Entity search, Audit
    layouts/                AppLayout (nav/sidebar)
    services/                api.js (axios client, runtime-aware base URL)
    hooks/                    useDashboardSocket (WebSocket + reconnect, runtime-aware base URL)
    context/                   AuthContext
  public/env.js             local-dev default runtime config (overwritten at container start)
  docker-entrypoint.sh       regenerates env.js from real env vars at container start
  Dockerfile

docs/
  architecture.md
  architecture-diagram.png / .svg / .dot
  scalability.md
  database-schema.md
  database-schema-diagram.png / .svg / .dot
  api-workflows.md

data/sample/               where sample MP4s go (see README.md there)
docker-compose.yml
render.yaml                 Render Blueprint (MySQL + backend + frontend)
.env.example
```

## 13. Future improvements

- Replace synchronous watchlist matching with a queue-backed worker.
- Replace the in-memory WebSocket manager with Redis Pub/Sub for
  multi-replica deployments.
- Implement a real RTSP → HLS/WebRTC relay adapter.
- Add rate limiting on ingestion and auth endpoints.
- Add frontend automated tests for the critical workflows.
- Add Prometheus/Grafana observability.
