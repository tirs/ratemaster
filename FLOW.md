# RateMaster - Flow and Implementation Instructions

This document describes the end-to-end flow and implementation status per the job spec.

## Stack (Locked)

| Layer    | Tech                    | Location   |
|----------|-------------------------|------------|
| Frontend | Next.js 14 (TypeScript) | `/frontend`|
| Backend  | FastAPI (Python 3.11)   | `/backend` |
| Database | PostgreSQL              | —          |
| Cache    | Redis                   | —          |
| Auth     | Email/password + JWT    | —          |

- **Architecture**: Monolith with modular services
- **OpenAPI**: Single source of truth at `/openapi.json`
- **Naming**: `snake_case` request/response end-to-end
- **Errors**: Standard envelope for all non-2xx (including 422)

---

## End-to-End Flow (Done Means)

### 1. Signup/Login → Create Org/Property [OK]

**Flow:**
1. User signs up or logs in → receives JWT
2. User creates organization (portfolio)
3. User adds properties under org

**Implementation:**
- `POST /api/v1/auth/signup`, `POST /api/v1/auth/login`
- `POST /api/v1/organizations`, `GET /api/v1/organizations`
- `POST /api/v1/organizations/properties`, `GET /api/v1/organizations/properties`
- Frontend: `/login`, `/signup`, `/dashboard`, `/dashboard/properties`

### 2. Upload Current CSV + Prior-Year Data → Data Health [OK] (Current only)

**Flow:**
1. User selects property
2. Uploads CSV (current or prior year)
3. Column mapping (auto-detect or manual)
4. Validation runs → Data Health score shown

**Implementation:**
- `POST /api/v1/data/import` (multipart: `property_id`, `snapshot_type`, `file`)
- Supports: `stay_date`, `rooms_available`, `total_rooms`, `rooms_sold`, `adr`, `total_rate`, `revenue`
- Data Health score 0–100 (gaps, errors, row count)
- Frontend: `/dashboard/data` (UI scaffold; file upload wiring in progress)

### 3. Market Signals Ingested on Schedule [PLANNED]

**Planned:**
- Pluggable Market Data Adapter
- Configurable refresh cadence (5–60 min)
- Redis-backed scheduler
- Options memo required before implementation

### 4. Run Engine A & B as Jobs → Progress Visible [PLANNED]

**Planned:**
- Redis/Celery background jobs
- Job status endpoints + UI progress
- Engine A: 0–30 days (tactical)
- Engine B: 31–365 days (strategic)

### 5. Results: Rate Suggestions, Deltas, Projections, Confidence, Why [PLANNED]

**Planned:**
- Per-stay-date outputs
- Confidence 0–100 + High/Med/Low
- “Why” reasoning bullets from drivers

### 6. Applied vs Not Applied Tracking [PLANNED]

**Planned:**
- Audit trail per recommendation
- Applied/not-applied flag
- Feeds attribution

### 7. Contribution Dashboard: Lift vs Baseline + GOP Lift [PLANNED]

**Planned:**
- Projected incremental revenue
- Realized MTD (if actuals imported)
- Flow-through % → estimated GOP lift

### 8. Export PDF + CSV [PLANNED]

**Planned:**
- Monthly performance + contribution report
- CSV for finance
- Baseline definition + audit refs

### 9. Frontend Types from OpenAPI [OK]

**Implementation:**
- `npm run generate:api` fetches `http://localhost:8000/openapi.json` → `src/lib/api-client.ts`
- Manual types in place until backend runs; regenerate for full sync

### 10. Standard Error Envelope (Including 422) [OK]

**Implementation:**
- All non-2xx return `{ success: false, error, error_code?, detail? }`
- 422 validation errors use `detail` array with `loc`, `msg`, `type`

### 11. ML Foundations [PLANNED]

**Planned:**
- Feature Store + training dataset builder
- Model Registry (global + property calibration)
- Predictor interface
- Training job pipeline
- Model version on predictions

---

## UI Theme: Glass

- **Style**: Glassmorphism (frosted glass)
- **Technique**: `backdrop-filter: blur()`, semi-transparent backgrounds, subtle borders
- **Colors**: Dark base (`slate-950`), cyan/violet/emerald accents
- **Components**: `.glass-card`, `.glass-input`, `.glass-button`, `.glass-button-primary`

---

## Quick Start

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env: DATABASE_URL, REDIS_URL, JWT_SECRET
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run generate:api   # After backend is running
npm run dev
```

### Environment

- `DATABASE_URL`: PostgreSQL connection string (use `+asyncpg` for async)
- `REDIS_URL`: Redis connection string
- `JWT_SECRET`: Min 32 chars for production

---

## Repo Structure

```
/frontend
  /src
    /app          # App Router pages
    /contexts     # Auth context
    /lib          # API client
/backend
  /app
    /api/routes  # Auth, orgs, data import
    /models      # SQLAlchemy models
    /schemas     # Pydantic (OpenAPI)
    /services    # Business logic
  /alembic       # Migrations
```

---

## Next Milestones

1. **Data upload UI** — Wire file input to `POST /data/import`, show health score
2. **Redis + jobs** — Celery/RQ for ingestion, engine runs, market refresh
3. **Engine A/B** — Predictor interface, feature store, heuristic predictors
4. **Market adapter** — Options memo → implementation
5. **ML foundations** — Feature store, model registry, training pipeline
