# RateMaster

Production-grade revenue/pricing recommendation SaaS for hotels. Dual engines (tactical + strategic), market signals, ML foundations, and portfolio management.

## Stack (Locked)

- **Frontend**: Next.js 14 (TypeScript) App Router in `/frontend`
- **Backend**: FastAPI (Python 3.11) in `/backend`
- **Database**: PostgreSQL
- **Cache/Jobs**: Redis + Celery
- **Auth**: Email/password + JWT

## Quick Start with Docker (Recommended)

### Prerequisites

- Docker and Docker Compose

### Run everything

```bash
# Copy env and set JWT_SECRET (required for production)
cp .env.example .env
# Edit .env: set JWT_SECRET, optionally ADMIN_EMAIL and ADMIN_PASSWORD

# Build and start all services
docker compose up --build -d

# App: http://localhost:30000
# API: http://localhost:30080
# OpenAPI: http://localhost:30080/docs
```

For VPS deployment, see [DEPLOYMENT.md](DEPLOYMENT.md).

### Services

| Service        | Port  | Description                    |
|----------------|-------|--------------------------------|
| frontend       | 30000 | Next.js app (proxies /api/v1 to backend) |
| backend        | 30080 | FastAPI + Alembic migrations on startup |
| postgres       | 5432  | PostgreSQL 16                 |
| redis          | 6379  | Redis 7                        |
| celery_worker  | —     | Background job worker (Engine A/B, YoY curves) |
| celery_beat    | —     | Scheduled tasks (market refresh, training) |

### Volumes

- **postgres_data** – Database persistence
- **uploads_data** – Organization logos and uploaded files

### Run migrations only (optional)

```bash
docker compose --profile migrate run --rm migrate
```

### Create admin user

Set `ADMIN_EMAIL` and `ADMIN_PASSWORD` in `.env` before first run, or run:

```bash
docker compose exec backend python -m scripts.create_admin
# Or: ADMIN_EMAIL=you@example.com ADMIN_PASSWORD=secret docker compose exec -e ADMIN_EMAIL -e ADMIN_PASSWORD backend python -m scripts.create_admin
```

### Stop

```bash
docker compose down
# With volumes: docker compose down -v
```

---

## Quick Start (Local Development)

### Prerequisites

- Node.js 18+
- Python 3.11+
- PostgreSQL 15+
- Redis 7+

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
cp .env.example .env     # Edit with your DB/Redis URLs
alembic upgrade head
uvicorn app.main:app --reload --port 30080
```

In a separate terminal for background jobs:

```bash
cd backend
celery -A celery_worker worker -l info
# On Windows, use --pool=solo to avoid multiprocessing errors:
# celery -A celery_worker worker -l info --pool=solo
```

Optional: run Celery beat for scheduled market refresh (configurable 5-60 min via `MARKET_REFRESH_MINUTES`):

```bash
celery -A celery_worker beat -l info
```

OpenAPI: http://localhost:30080/openapi.json

### Frontend

```bash
cd frontend
npm install
npm run generate:api     # Generate types from backend OpenAPI (backend must be running)
npm run dev
```

App: http://localhost:30000

### Create admin user

```bash
cd backend
python -m scripts.create_admin
# Or with custom email/password:
# ADMIN_EMAIL=you@example.com ADMIN_PASSWORD=secret python -m scripts.create_admin
```

### Environment

Create `frontend/.env.local` (copy from `.env.example`). Uses 5-digit ports (30080, 30000) to avoid Docker conflicts.

Create `backend/.env`:

```
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/ratemaster
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=your-secret-key-min-32-chars
MARKET_REFRESH_MINUTES=30
RATE_LIMIT_PER_MINUTE=120
API_CACHE_TTL_SECONDS=60
```

## Sample Hotel Data

Realistic test data for a 120-room hotel:

```bash
python scripts/generate_hotel_data.py
```

Creates in `fixtures/`:
- **hotel_current.csv** – 90 days (current)
- **hotel_prior_year.csv** – 365 days (prior year for YoY)
- **hotel_current_extended.csv** – 180 days (Engine B range)

Upload prior year first, then current. See `fixtures/README.md` for details.

---

## Architecture

- Monolith with modular services
- OpenAPI contract-first (single source of truth)
- snake_case request/response end-to-end
- Standard error envelope for all non-2xx responses

## Repo Structure

```
/frontend     Next.js App Router
/backend      FastAPI + SQLAlchemy + Redis
```

## Market Signals Options Memo

Before implementing market data sources, the engineer must deliver an options memo. See [backend/docs/MARKET_OPTIONS_MEMO.md](backend/docs/MARKET_OPTIONS_MEMO.md) for approaches, cost estimates, and recommendation.
