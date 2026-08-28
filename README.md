# event-gate

`event-gate` is a backend service for ingesting events from external systems, deduplicating them, applying correlation rules, and generating alerts.

## Features

- Event ingestion from external sources
- Idempotent event processing with Redis and a database unique constraint
- Batch ingestion of up to 500 events
- Event filtering and keyset pagination
- Redis-based rate limiting
- Configurable correlation rules
- Automatic alert generation for matched rules
- Alert status management
- Per-source event and alert statistics
- PostgreSQL and Redis health checks

## Tech Stack

- Python 3.12
- FastAPI
- Pydantic v2
- SQLAlchemy 2.0 async + asyncpg
- PostgreSQL 16
- Redis 7
- Alembic
- pytest + pytest-asyncio + httpx
- Ruff
- Docker Compose
- GitHub Actions

## Architecture

The application is split into three main layers:

- `api/` — HTTP endpoints, request validation, authentication, and dependencies
- `services/` — business logic such as event correlation and rate limiting
- `models/` — SQLAlchemy database models

The API layer calls the service layer, while services remain independent of FastAPI.

PostgreSQL stores persistent application data. Redis is used for rate limiting and idempotency caching.

## API

### Health

- `GET /health` — check PostgreSQL and Redis availability

### Sources

- `POST /api/v1/sources` — create a source
- `GET /api/v1/sources` — list sources

### Events

- `POST /api/v1/events` — ingest a single event
- `POST /api/v1/events/batch` — ingest up to 500 events
- `GET /api/v1/events` — list and filter events with keyset pagination

### Rules

- `POST /api/v1/rules` — create a correlation rule
- `GET /api/v1/rules` — list rules
- `PATCH /api/v1/rules/{id}` — update a rule

### Alerts

- `GET /api/v1/alerts` — list alerts with optional status filtering
- `PATCH /api/v1/alerts/{id}` — update alert status

### Statistics

- `GET /api/v1/stats/sources` — get per-source event and alert statistics

## Key Design Decisions

- Event duplicates are handled idempotently: repeated events return the existing event instead of producing a conflict.
- Redis stores idempotency keys with a 24-hour TTL, while `UNIQUE(source_id, external_id)` in PostgreSQL provides the final consistency guarantee.
- Database constraints protect against concurrent duplicate inserts instead of relying on a SELECT-before-INSERT check.
- Event ingestion and correlation are committed in the same database transaction.
- Batch ingestion uses PostgreSQL `ON CONFLICT DO NOTHING`.
- Event listing uses keyset pagination instead of offset pagination.
- Source statistics are implemented with raw SQL using CTEs, joins, and a window function.
- Foreign keys do not use cascade deletion because event and alert history should not disappear implicitly.

## Running Locally

### 1. Clone the repository

```bash
git clone https://github.com/Haruw09/event-gate.git
cd event-gate
```

### 2. Create the environment file

```bash
cp .env.example .env
```

### 3. Build and start the services

```bash
docker compose up -d --build
```

### 4. Apply database migrations

```bash
docker compose exec app alembic upgrade head
```

### 5. Check the application

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok"}
```

## Tests

Start the test PostgreSQL and Redis services:

```bash
docker compose up -d postgres_test redis_test
```

Apply migrations to the test database:

```bash
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/event_gate_test \
alembic upgrade head
```

Run the test suite:

```bash
python -m pytest
```

Run linting:

```bash
python -m ruff check .
```

The test suite covers health checks, source management, API-key authentication, event idempotency, batch ingestion, validation, rate limiting, and correlation with alert creation.

## CI

GitHub Actions runs automatically on every push and pull request.

The CI pipeline:

1. Starts PostgreSQL 16 and Redis 7 service containers
2. Installs Python dependencies
3. Applies Alembic migrations to a clean test database
4. Runs Ruff
5. Runs the pytest test suite

## Limitations and Further Work

- No message broker. Under higher ingestion load, a queue (e.g. Kafka)
  would decouple ingestion from correlation; correlation currently runs
  in the same transaction as ingestion.
- Rules are evaluated on ingestion only, so a rule whose window expires
  without new events will not fire until the next event arrives.
  A scheduled worker would close this gap.
- Authentication is a static per-source API key, sufficient for
  service-to-service use but not for user-facing access control.
- No metrics endpoint; observability is limited to structured logs.
- Alert delivery (webhook, email) is out of scope — alerts are stored
  and exposed via the API only.
