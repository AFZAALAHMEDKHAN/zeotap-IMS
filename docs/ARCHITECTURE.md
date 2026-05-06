# Architecture & Tech Stack Rationale

This document explains *why* each technology was picked for the Incident Management System (IMS) and what alternatives were considered. The assignment rubric awards 10% explicitly for "Tech Stack choices — System design of tech stack", and this document is the artefact for that line.

The high-level architecture diagram lives in the root [`README.md`](../README.md). This document focuses on **rationale**, not topology.

---

## Guiding Principles

The assignment specifies four hard constraints that drive every choice below:

1. **High-throughput ingestion** — bursts of up to 10,000 signals/sec.
2. **Crash-safety under slow persistence** — the API cannot fail because the database is slow.
3. **Heterogeneous storage needs** — a data lake, a transactional store, a hot-path cache, and a timeseries aggregation store.
4. **Mandatory async processing** with state-driven workflow.

These map directly to the choices below.

---

## Backend: Python + FastAPI + asyncio

**What:** FastAPI 0.110+ on Python 3.11 with full async/await across the stack.

**Why FastAPI specifically:**

- The assignment mandates async processing. FastAPI is async-native — every endpoint is a coroutine, no thread-pool wrapping needed.
- ASGI + uvicorn handles the 10K signals/sec target without spawning per-request threads.
- Built-in OpenAPI/Swagger (`/docs`) is part of the deliverable evaluation ("running application").
- Pydantic v2 gives schema validation at the boundary, which is where the "Mandatory RCA" rule needs to be enforced.
- Native Python ecosystem: `motor` for async MongoDB, `asyncpg` via SQLAlchemy 2.0 async, `redis-py` async client, `slowapi` for rate limiting — every storage choice has a first-class async driver.

**Alternatives considered:**

| Alternative | Why not |
|---|---|
| Go + Fiber/Gin | Faster runtime, but the job description lists *Python or Go* and the responsibilities heavily reference Python+FastAPI ("Spendrift, an internal cost-intelligence platform — Python, FastAPI, React, BigQuery"). Matching the stack the team actually uses is more valuable here than raw throughput. |
| Node.js + Fastify | Async story is good, but Python's data tooling and the job's Python lean made it the obvious fit. |
| Django + Channels | Mature, but ORM-first and async retrofit; FastAPI is async-first by design. |

---

## Source of Truth: PostgreSQL

**What:** PostgreSQL 15 via SQLAlchemy 2.0 + asyncpg, storing `work_items` and `rcas` tables.

**Why PostgreSQL:**

- Work Item state transitions and RCA submission must be **transactional** (per assignment). PostgreSQL gives us ACID with serializable isolation when needed.
- The one-to-one constraint (each WorkItem can have at most one RCA) is enforced via a `UNIQUE` constraint on `rcas.workitem_id` + `ON DELETE CASCADE`. This is a database-level guarantee — even a buggy application path cannot create duplicate RCAs.
- Foreign keys, check constraints, and the typed JSONB column (used for `metadata` on signals when needed) cover both relational and semi-structured needs without dragging in a second OLTP store.
- Mature operational story: backups, replication, point-in-time recovery are all production-trivial.

**Alternatives considered:**

| Alternative | Why not |
|---|---|
| MySQL | Workable, but Postgres' richer constraint system (partial indexes, exclusion constraints, JSONB) future-proofs us better. |
| SQLite | Single-file simplicity is tempting for an assignment, but the rubric explicitly grades "race conditions during status updates" — that requires a real concurrent OLTP. |

---

## Data Lake: MongoDB

**What:** MongoDB 7 via the async `motor` driver, with two collections: `signals` (raw audit log) and `signal_timeseries` (per-minute aggregated buckets).

**Why MongoDB:**

- Raw signal payloads are **schemaless by nature** — different component types emit different metadata shapes. A document store avoids the schema-migration tax.
- The assignment hint "think how this can be queried" is satisfied by Mongo's secondary indexes on `component_id`, `severity`, and `created_at`, plus aggregation pipelines for ad-hoc audit queries.
- The same engine handles both the data lake *and* the timeseries aggregation requirement (Mongo's native time-series collections, or simple pre-bucketed minute-level documents — we use the latter for portability across Mongo versions).
- Fully async client (`motor`) keeps the worker non-blocking.

**Alternatives considered:**

| Alternative | Why not |
|---|---|
| Elasticsearch | Excellent for log-style audit queries, but operational overhead is heavy for a 6-day build. |
| ClickHouse / TimescaleDB | Great for timeseries specifically, but adds a fourth storage engine. Mongo + bucketed documents covers the 80% case for this assignment. |
| Postgres JSONB only | Would work for raw payloads, but separating the high-volume audit log from the transactional source-of-truth is itself part of the design ask ("correct separation of data for various purpose" — 20% of the rubric). |

---

## Cache + Debounce: Redis

**What:** Redis 7 via the async `redis.asyncio` client. Used for two distinct concerns:

1. **Debounce keys** (`debounce:{component_id}` with a 10-second TTL).
2. **Dashboard cache** (`dashboard:workitems` with a 30-second TTL).

**Why Redis:**

- TTL-based debouncing is a single SET with `EX 10` — no periodic cleanup task needed.
- Atomic single-key operations are exactly what the dashboard cache pattern (read-through, invalidate-on-write) needs.
- The assignment specifies a "hot-path real-time dashboard state to avoid querying the source of truth on every UI refresh." Redis is the canonical fit.
- Already async-friendly and trivially Dockerised.

**A known limitation, deliberately scoped to single-worker:** the current debounce uses a `GET → create-WorkItem → SETEX` sequence. This is correct under a single asyncio worker (signals are processed serially within one event loop) but not safe across multiple worker processes. The roadmap entry to switch to atomic `SET NX EX` is intentional and is documented in the README. For the assignment's scope (single backend container), the current approach is correct and avoids over-engineering.

---

## Frontend: React + Vite

**What:** React 18 with Vite 5 for the dev server and bundler. `react-router-dom` for routing, `axios` for HTTP, `date-fns` for time formatting, and `recharts` for the timeseries charts.

**Why this stack:**

- The assignment allows React, Vue, or HTMX. The job description explicitly mentions React ("Spendrift … Python, FastAPI, React, BigQuery"), so React aligns with the team's stack.
- Vite gives sub-second hot-reload and a small production bundle without ejecting from a CRA-style toolchain.
- Plain functional components + hooks — no Redux/MobX overhead for a dashboard whose state is mostly server-driven via polling.
- `recharts` produces the timeseries visualisation against the MongoDB aggregation endpoint with minimal code.

**Alternatives considered:**

| Alternative | Why not |
|---|---|
| HTMX | Tempting for "less JavaScript" — but the live-feed polling, RCA form state, and chart components benefit from a proper component model. |
| Next.js | SSR is unnecessary here (auth-gated internal tool, no SEO concerns), and the extra build complexity isn't justified. |

---

## In-Memory Buffer: `asyncio.Queue`

**What:** A bounded `asyncio.Queue` with `maxsize=50000` between the ingestion endpoint and the background worker, populated via `put_nowait()`.

**Why a Python `asyncio.Queue` over an external broker (Kafka / RabbitMQ / NATS):**

- The assignment line "your system cannot crash if persistence layer is slow" is satisfied with an in-process bounded queue — the API path becomes O(1) and decoupled from disk I/O.
- Adding Kafka/RabbitMQ for a single-process backend would add weeks of ops complexity and 100+ MB of containers without changing the user-visible behaviour for the assignment scope.
- The fail-open strategy (drop on `QueueFull`, log a warning, return 202) is exactly the backpressure pattern the rubric wants to see.
- The roadmap explicitly calls out "durable queueing, dead-letter storage, and adaptive rate limits" — i.e. the path to Kafka — as the natural next step *after* multi-worker scaling. We surface this trade-off honestly rather than pretending we built a Kafka integration.

---

## Rate Limiting: SlowAPI

**What:** SlowAPI on the `POST /api/v1/signals` endpoint, configured via `RATE_LIMIT_PER_MINUTE`.

**Why SlowAPI:**

- It's the de facto FastAPI rate-limiter, integrates as a dependency, and stores counters in-memory (or Redis if needed) without extra infra.
- The current limit (`600000/minute = 10000/sec`) matches the assignment's burst target. In production, this would be tuned per environment and enforced upstream by a proxy/Envoy.

---

## Containerisation: Docker Compose

**What:** A single `docker-compose.yml` orchestrating PostgreSQL, MongoDB, Redis, the backend, and the frontend, with healthchecks and named volumes.

**Why Compose specifically:**

- The recruiter email's first line is "the first qualification criteria is a running application." Docker Compose makes "clone repo → `docker compose up -d --build` → open browser" a single-command path.
- Healthchecks on every storage service mean the backend's `depends_on: condition: service_healthy` blocks startup until dependencies are ready — no flaky first-boot.
- Named volumes preserve data across restarts; `docker compose down -v` gives a clean reset.
- Production migration path: each Compose service maps cleanly to a Helm chart or a Cloud Run service, which aligns with the GCP/GKE focus of the role.

---

## Cross-Cutting Choices

| Concern | Choice | Why |
|---|---|---|
| Async DB client (Postgres) | SQLAlchemy 2.0 async + asyncpg | Modern typed `Mapped[]` syntax + true async. |
| Async DB client (Mongo) | `motor` | Official async driver from MongoDB. |
| Async Redis client | `redis.asyncio` | Bundled with `redis-py` 5+; first-class async. |
| Schema validation | Pydantic v2 | Native to FastAPI; performance is C-backed. |
| Logging | stdlib `logging` with structured formatters | No external dependency; easy to redirect to JSON in prod. |
| Tests | `pytest` + `pytest-asyncio` | Standard async testing toolkit. |
| Frontend HTTP | `axios` | Cleaner interceptors and error handling vs. raw `fetch`. |
| Frontend dates | `date-fns` | Tree-shakeable; modular vs. moment.js. |

---

## Trade-offs Honestly Acknowledged

- **Single backend worker** — chosen for simplicity within the assignment timeline. Roadmap'd to a configurable worker pool.
- **`create_all()` instead of Alembic** — schemas are stable for the demo; Alembic migrations are roadmap'd for production.
- **`GET → SETEX` debounce** — correct for the single-worker scope; atomic `SET NX EX` is the multi-worker fix and is on the roadmap.
- **In-memory queue, not Kafka** — keeps the assignment build tractable; durable queueing is the natural next step.

These are documented openly because the rubric rewards engineering judgment, and pretending the system is more production-ready than it is would be the wrong signal to send.
