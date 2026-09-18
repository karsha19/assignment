# Completion Report

## Implemented features

- Authentication (JWT + bcrypt), role-based authorization enforced
  server-side on every protected route
- Camera registry: full CRUD, enable/disable, search/filter, simulated
  heartbeat with threshold-based health status and WebSocket broadcast on
  change
- Camera source adapter abstraction with working recorded/simulated
  adapters and documented stubs for RTSP/ONVIF/vendor API
- Interactive camera map (Leaflet) with status- and alert-aware markers
- Analytics event ingestion API implementing the full validate → persist →
  correlate → alert → broadcast pipeline, with idempotency-key duplicate
  rejection
- Watchlist CRUD with documented exact-match identifier normalization
- Real-time alerting over WebSocket with reconnect-with-backoff on the
  frontend; alert lifecycle (new/acknowledged/resolved) with enforced valid
  transitions
- Entity/vehicle search with chronological movement history and route
  visualization on the map, built strictly from persisted detection events
- Audit logging on sensitive actions with an admin-only viewing UI
- Operational dashboard: summary statistics, camera grid with video
  preview, active alerts panel with acknowledge/resolve, live recent-activity
  feed driven by the WebSocket
- Alembic migration (full schema) + reproducible, idempotent seed script
- Docker Compose orchestration (MySQL, backend, frontend)
- 18 automated backend tests, all passing

## Tested workflows

Verified via the automated test suite (`backend/tests/`) and manual
exercise of the running application (SQLite-backed for automated tests;
application code is database-agnostic through SQLAlchemy and targets MySQL
in the real deployment):

- Login success/failure, token-protected routes
- Admin-only camera creation rejected for operator role; enforced server-side
- Duplicate camera code rejected; invalid coordinates rejected
- Disabled camera cannot have events ingested against it
- Camera search/filter by code
- Identifier normalization matches formatting variants (spacing, hyphens,
  case) against a watchlist record
- Non-matching detections do not create alerts
- Disabled watchlist records do not trigger alerts
- Duplicate `idempotency_key` events rejected with 409
- ANPR events without an identifier rejected with 422
- Alert lifecycle: acknowledge → resolve, invalid re-acknowledge rejected
- Movement history returned in chronological order regardless of insertion
  order

Manually exercised (frontend built successfully with `npm run build`;
backend boots and serves `/docs`; seed script runs cleanly against a fresh
schema): login flow, camera registry page, camera detail/video page,
camera map, watchlist page, alerts center, entity search with map + timeline,
audit page.

## Known limitations

See `README.md` §10 for the full list. In short: no real RTSP/ONVIF/vendor
camera connections (documented stubs only, by design — not claimed as
working); no bundled sample video files (instructions provided instead);
synchronous (not queue-decoupled) watchlist matching; single-process
WebSocket manager; no rate limiting; no CI/CD; diagrams are Mermaid rather
than exported image files; no screen-recorded demo video is included in
this repository, since recording an authentic walkthrough requires a live
run by whoever submits the assignment.

## Optional features implemented

- Docker Compose
- Automated tests (backend)
- Role-specific views (admin-only Audit History nav item and route)

## Optional features not implemented

ONVIF discovery/mock adapter beyond the stub, RTSP→WebRTC/HLS gateway,
cross-camera re-identification, ANPR duplicate suppression beyond
idempotency-key dedup, camera heartbeat as a truly external service (the
simulator is internal to the backend), low-bandwidth edge gateway,
CI/CD, Prometheus/Grafana, Redis/Kafka event architecture, multi-department
tenancy.

## Setup instructions

See `README.md` §4 (Docker Compose - recommended), §5 (Render), or §6 (manual local
setup).

## Demo instructions

1. `docker compose up --build` (after `cp .env.example .env`).
2. Log in as `admin` / `Admin@12345`.
3. Camera Registry already has two seeded cameras (C001, C002); optionally
   add a third to demonstrate the Add Camera flow live.
4. Camera Map shows both markers.
5. Open a camera's detail page — video will play if sample MP4s were added
   per `data/sample/README.md`, otherwise a documented "no preview" state
   shows instead.
6. Use `docs/api-workflows.md` step 4 to POST a new matching analytics
   event via `/docs` (Swagger UI) while the Dashboard or Alerts Center is
   open in another tab — the alert appears immediately without a refresh.
7. Acknowledge/resolve the alert from either the Dashboard or Alerts Center.
8. Go to Entity Search, search `GJ01XX0001` (the seeded watchlisted plate)
   to see chronological movement history and the route on the map.
9. Log in as `admin` again (or stay logged in) and open Audit History to see
   the logged actions from the steps above.

## Suggested future improvements

See `README.md` §13.
