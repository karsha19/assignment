# Scalability and Deployment Note

This prototype runs a handful of cameras on a single backend/DB instance.
This document explains the credible path from that prototype to the
~80,000-camera scale referenced by the assignment. Nothing here has been
load-tested; it is an architecture and sizing rationale, not a benchmark.

## 1. Architecture: central / regional / edge

At prototype scale, a single FastAPI instance handles everything. At scale,
video and metadata paths should split:

- **Edge** (per site/city cluster): lightweight gateways terminate RTSP/ONVIF
  from physical cameras, run first-pass health checks, and either forward
  frames to a regional AI inference cluster or run inference locally on
  edge GPUs for low-bandwidth sites. Edge nodes push only structured
  analytics events (not raw video) to the central platform, mirroring what
  `POST /api/v1/analytics/events` already accepts.
- **Regional**: aggregates edge output for a state/zone, runs
  heavier correlation (e.g. cross-camera re-identification within a region),
  and relays video on-demand (not continuously) to the central system.
- **Central**: the system this prototype models — camera registry,
  watchlist, alerting, dashboards, audit — but horizontally scaled (see
  below) and fed by regional aggregators instead of individual cameras
  directly.

This keeps the ~80,000-camera fan-in from ever hitting one API layer
directly; it always passes through edge/regional aggregation first.

## 2. Performance and horizontal scaling

- **Backend**: FastAPI is stateless per-request (JWT, no server-side
  session) except for the in-process WebSocket connection list, which is the
  one thing that does not horizontally scale as-is. At scale, replace the
  in-memory `ConnectionManager` with a pub/sub backbone (Redis Pub/Sub or
  Kafka) so any backend replica can broadcast to any connected dashboard
  client, and run multiple backend replicas behind a load balancer.
- **Load balancing**: standard L7 load balancer (e.g. an ALB/NGINX) in front
  of N backend replicas; sticky sessions are not required since auth is
  stateless.
- **Database**: MySQL read replicas for dashboard/reporting queries;
  writes (event ingestion, alerts) stay on the primary. Partition
  `analytics_events` by time (monthly/weekly) once volume is high, since
  queries are almost always time-bounded.
- **Connection pooling**: SQLAlchemy's pool is already configured
  (`pool_pre_ping`, `pool_recycle`); at scale, front the DB with PgBouncer-
  style pooling (or MySQL equivalent, e.g. ProxySQL) so many backend
  replicas don't each hold large native connection pools.
- **Caching**: camera registry and watchlist are read far more often than
  written — cache both in Redis with short TTL + explicit invalidation on
  writes, rather than hitting MySQL for every dashboard load.
- **Message queues**: event ingestion should decouple "accept and
  acknowledge" from "persist and correlate" — an inbound queue (Kafka /
  RabbitMQ) absorbs bursts and lets the matching/alerting stage scale
  independently of the HTTP ingestion layer.
- **Event deduplication**: the `idempotency_key` unique constraint used here
  is the same mechanism that should sit at the queue-consumer layer at
  scale (dedupe on consume, not just on DB insert, to avoid wasted
  processing).

## 3. Video infrastructure

- **Bandwidth**: 80,000 continuous RTSP streams is infeasible to centralize.
  Only send video centrally on-demand (operator opens a camera) or for
  short forensic windows around an alert; otherwise inference happens at
  the edge and only metadata travels centrally.
- **Low-bandwidth strategies**: adaptive bitrate at the edge gateway,
  event-triggered clip upload instead of continuous relay, and regional
  caching of recently-viewed streams.
- **RTSP ingestion**: edge gateways terminate RTSP from cameras; the central
  platform never speaks RTSP directly to 80,000 devices.
- **WebRTC/HLS relay**: for operator playback, edge/regional nodes transcode
  RTSP → HLS (for scale/simplicity) or WebRTC (for lower latency) and the
  central dashboard just embeds a player pointed at the relay URL — this
  prototype's `CameraSourceAdapter` abstraction is exactly the seam where
  that relay reference would be plugged in as `playback_reference`.
- **GPU requirements**: inference (ANPR/object/person detection) is the
  GPU-bound piece. At edge scale, that means many small inference nodes
  (e.g. Jetson-class or small GPU boxes) rather than one large central GPU
  cluster, to avoid the bandwidth problem above.

## 4. Storage

- **Hot storage**: last few days of video, on fast local/regional storage
  near the edge, for immediate operator review.
- **Warm storage**: recent weeks, object storage (e.g. S3-compatible),
  regional.
- **Cold storage**: long-term retention for compliance/evidence, lower-cost
  archival tiers with lifecycle policies.
- **Video vs. metadata**: metadata (`analytics_events`, `alerts`,
  `audit_logs`) is small and stays in the relational database indefinitely
  (subject to retention policy); video is large and follows the hot/warm/cold
  path above, referenced by URL/ID from metadata rather than stored inline.
- **Database scaling**: start with a single MySQL primary + replicas
  (current design); move to sharding by region/department only if a single
  primary's write throughput becomes the bottleneck — the schema's UUID
  keys and lack of cross-shard foreign-key assumptions make that migration
  feasible later without a redesign.

## 5. Reliability and operations

- **Health checks**: `/health` endpoint (present in this prototype); at
  scale, add readiness/liveness probes per service for orchestrator
  (Kubernetes) restarts.
- **Monitoring/logging**: structured logs shipped to a central aggregator;
  metrics (request latency, queue depth, alert-generation latency, camera
  health) exported to Prometheus/Grafana.
- **High availability**: multi-replica backend, MySQL primary/replica with
  automated failover, message queue cluster (not single-broker).
- **Disaster recovery**: automated MySQL backups with tested restore
  procedure; object storage cross-region replication for video; documented
  RTO/RPO targets per data class (metadata vs. video).
- **Failure handling**: ingestion should degrade gracefully — if the
  watchlist-matching stage is slow/down, events still persist and matching
  can catch up asynchronously rather than blocking ingestion entirely (a
  production evolution of the synchronous match-then-alert flow this
  prototype uses for demo simplicity).

## 6. Cybersecurity

- **Network segmentation**: edge/camera network isolated from the
  central management plane; only structured events and authenticated API
  calls cross that boundary.
- **Service authentication**: service-to-service calls (edge → central) use
  short-lived service credentials, not the same JWTs issued to human
  operators.
- **TLS**: everywhere in transit — edge-to-region, region-to-central,
  browser-to-backend.
- **Secrets management**: stream credentials, DB credentials, and JWT
  signing secrets live in a secrets manager (e.g. AWS Secrets Manager /
  HashiCorp Vault) and are injected as environment variables at deploy time
  — never committed, matching this prototype's `.env`-based configuration
  pattern.
- **Least privilege**: separate DB credentials for the ingestion path vs.
  the admin/reporting path if/when those become separate services.
- **Secure camera connectivity**: edge gateways authenticate to cameras
  using per-device credentials, not a shared password across the fleet.

## 7. Illustrative cost factors (not a quotation)

These are the variables that drive cost, not a priced estimate — actual
figures depend on cloud provider, region, and commercial negotiation:

| Deployment | Cameras | Dominant cost driver |
|---|---|---|
| Prototype (this repo) | 2–10 | Negligible — single small VM + managed MySQL |
| Medium | ~500–2,000 | Regional GPU inference nodes, warm object storage, a few backend replicas |
| Large (~80,000) | ~80,000 | Edge/regional GPU fleet (by far the largest line item), egress bandwidth for on-demand video, storage lifecycle management, and message-queue/DB infrastructure to absorb sustained event throughput |

Assumptions: inference stays at the edge/region (not centralized); video is
relayed on-demand rather than continuously centralized; metadata volume
(events/alerts) is the only thing that scales linearly with camera count on
the central database.
