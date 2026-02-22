# RateMaster — Job Spec Compliance Summary

Audit of the Senior Full-Stack Engineer job spec against the current implementation.

---

## Locked Stack ✅

| Requirement | Status |
|-------------|--------|
| Frontend: Next.js (TypeScript) App Router in `/frontend` | ✅ |
| Backend: FastAPI (Python 3.11) in `/backend` | ✅ |
| Database: PostgreSQL | ✅ |
| Redis (caching + background jobs) | ✅ |
| Auth: email/password + JWT | ✅ |
| Monolith with modular services | ✅ |
| OpenAPI single source of truth | ✅ |
| snake_case request/response end-to-end | ✅ |
| Standard error envelope for ALL non-2xx (including 422) | ✅ |

---

## Repo Rules ✅

| Requirement | Status |
|-------------|--------|
| Monorepo: only `/frontend` and `/backend` | ✅ |
| Frontend types from backend `/openapi.json` | ✅ `npm run generate:api` |
| No undocumented endpoints | ✅ |

---

## 1. Multi-Property / Portfolio

| Feature | Status | Notes |
|---------|--------|-------|
| Organization (portfolio owner) accounts | ✅ | |
| Multiple properties under org | ✅ | |
| Roles: Owner / GM / Analyst | ✅ | Backend: OrgMember, invite API. Frontend: Settings → Team & Roles invite UI. |
| Portfolio dashboard: 30/60/90 outlook | ✅ | |
| Alerts rollup | ✅ | |
| RateMaster value generated rollup | ✅ | |

---

## 2. Data Ingestion + Data Health

| Feature | Status | Notes |
|---------|--------|-------|
| CSV upload with column mapping + validation | ✅ | Auto-detect + optional manual mapping |
| Import history + snapshot metadata | ✅ | |
| Logical fields (stay_date, rooms, ADR, revenue, etc.) | ✅ | |
| Manual entry fallback | ✅ | POST /manual-data |
| Prior year upload (YoY) | ✅ | snapshot_type=prior_year |
| YoY trend curves (season/month, day-of-week) | ✅ | YoYCurve model, compute_yoy_curves |
| Lead-time patterns (if booking_date exists) | ✅ | |
| Data Health score per property | ✅ | 0–100 |
| Recommended fixes | ✅ | |
| Data Health influences Confidence | ✅ | base_conf uses data_health_score |
| snapshot_date tracked | ✅ | From earliest stay_date or Form param |

---

## 3. Dual Engines + Projections + Confidence + "Why"

| Feature | Status | Notes |
|---------|--------|-------|
| **Engine A** (0–30 days): BAR (Conservative/Balanced/Aggressive) | ✅ | |
| Delta vs current, occupancy projection, pickup, sellout | ✅ | Heuristic values; pickup/sellout are placeholders |
| ADR/RevPAR impact, Confidence (0–100), "Why" bullets | ✅ | |
| **Engine B** (31–365): Floor/Target/Stretch calendar | ✅ | |
| Longer-range occupancy + ADR forecast bands | ✅ | occupancy_forecast_low/high |
| YoY curves + seasonality + events | ✅ | PropertyEvent, get_event_multiplier |
| Feature layer separated from decision layer | ✅ | compute_features, store_features |
| Immutable run_id, reproducibility | ✅ | |
| DOW rules, blackout dates, guardrails | ✅ | min_bar, max_bar, max_daily_change_pct |

---

## 4. ML Foundations

| Feature | Status | Notes |
|---------|--------|-------|
| Predictor Interface (Engine A/B) | ✅ | HeuristicPredictor, heuristic models |
| Feature Store (versioned) | ✅ | FeatureStore model, store_features |
| Model Registry (global + property calibration) | ✅ | ModelRegistry, register_model, get_active_model |
| Training dataset builder | ✅ | build_training_dataset (features + outcomes) |
| Training jobs (Redis-backed) | ✅ | run_training_job, POST /jobs/training |
| Outcomes/actuals import for learning | ✅ | POST /outcomes/import |
| Confidence: data health + model uncertainty | ✅ | |
| "Why" from stored drivers | ✅ | why_bullets, why_drivers |
| Guardrails (min/max BAR, max daily change, DOW, blackout) | ✅ | |
| Fallback predictor / confidence threshold | ✅ | min_confidence_threshold → conservative |
| Scheduled training jobs | ✅ | run_training_jobs_scheduled on Celery beat (daily) |

---

## 5. Market Signals

| Feature | Status | Notes |
|---------|--------|-------|
| Pluggable Market Data Adapter | ✅ | MarketDataAdapter interface, ManualEntryAdapter |
| Market snapshot storage | ✅ | MarketSnapshot model |
| Refresh cadence configurable (5–60 min) | ✅ | Celery beat, MARKET_REFRESH_MINUTES |
| Customer-provided / CSV upload | ✅ | POST /market/import-csv |
| Options memo | ✅ | backend/docs/MARKET_OPTIONS_MEMO.md |
| Caching, rate limiting | ✅ | Redis cache, SlowAPI |
| Market snapshot triggers Engine A re-runs | ✅ | create_market_snapshot, import_csv, refresh_all_market_signals trigger run_engine_a |

---

## 6. Dashboards

| Feature | Status | Notes |
|---------|--------|-------|
| Per-property: forecasts, rate calendar, why drivers | ✅ | Engines page |
| Portfolio: rollups, alerts, opportunities | ✅ | |
| Contribution: projected/realized lift, top wins | ✅ | |
| Baseline methodology shown | ✅ | Exports, contribution page |
| 30/60/90 occupancy/ADR/RevPAR/pickup forecasts | ✅ | GET /portfolio/forecast, dedicated Forecast dashboard page |

---

## 7. A/B/C/D Features

| Feature | Status | Notes |
|---------|--------|-------|
| **A.** Audit trail, applied vs not applied | ✅ | Recommendation.applied, mark applied, filter/select all |
| **B.** Alerts + Task Inbox | ✅ | sellout_risk, market_undercutting, pickup_deviation, confidence_issue auto-generated in Engine A |
| **C.** PDF + CSV exports | ✅ | contribution.pdf, contribution.html, contribution.csv |
| **D.** Data integrity (Data Health) | ✅ | |

---

## 8. Profit Tracking + Billing

| Feature | Status | Notes |
|---------|--------|-------|
| Base fee + revenue share % | ✅ | |
| Effective dates (contract_effective_from/to) | ✅ | Invoice filters realized_lift by contract_effective_from/to |
| Monthly invoice-ready output | ✅ | GET /billing/invoice |
| YoY reporting | ✅ | GET /billing/yoy |
| Revenue share on revenue or GOP (configurable) | ✅ | revenue_share_on_gop |

---

## 9. Flow-Through (GOP)

| Feature | Status | Notes |
|---------|--------|-------|
| Configurable flow-through % per property | ✅ | |
| Revenue → GOP conversion | ✅ | |
| Contribution shows revenue lift + estimated GOP lift | ✅ | |
| Revenue share on revenue or GOP (configurable) | ✅ | |

---

## Non-Negotiable Engineering

| Requirement | Status |
|-------------|--------|
| OpenAPI contract-first | ✅ |
| Error envelope all non-2xx | ✅ |
| Redis-backed background jobs | ✅ |
| Job status endpoints + UI progress | ✅ |
| Backend unit + integration tests | ✅ |
| Frontend smoke tests | ✅ |

---

## End-to-End Flow (Done Means)

| Step | Status |
|------|--------|
| 1. Signup/login → create org/property | ✅ |
| 2. Upload current + prior-year CSV → data health | ✅ |
| 3. Market signals on schedule | ✅ |
| 4. Run Engine A & B → progress visible | ✅ |
| 5. Results: rate suggestions, deltas, confidence, why | ✅ |
| 6. Applied vs not applied tracking | ✅ |
| 7. Contribution dashboard + GOP lift | ✅ |
| 8. Export PDF + CSV + HTML | ✅ |
| 9. Frontend types from OpenAPI | ✅ |
| 10. All errors use envelope | ✅ |
| 11. ML foundations (feature store, registry, training) | ✅ |

---

## Gaps / Not Yet Implemented

All previously identified gaps have been closed:

1. **Roles UI** — ✅ Settings → Team & Roles: invite GM/Analyst, list members.
2. **Alert generation** — ✅ sellout_risk, market_undercutting, pickup_deviation, confidence_issue in Engine A.
3. **Market snapshot → Engine A re-runs** — ✅ create_market_snapshot, import_csv, refresh_all_market_signals trigger run_engine_a.
4. **Effective dates in billing** — ✅ Invoice filters by contract_effective_from/to.
5. **Scheduled training jobs** — ✅ run_training_jobs_scheduled on Celery beat (daily).
6. **Dedicated forecast dashboard** — ✅ /dashboard/forecast with 30/60/90 occupancy, ADR, RevPAR, pickup.

---

## Extras (Beyond Spec)

- **Docker** — Full docker-compose (postgres, redis, backend, frontend, celery_worker, celery_beat).
- **Training page** — In-app documentation with tabbed navigation.
- **HTML report export** — In addition to PDF.
- **Sample CSV data** — sample-data/ for testing.
- **Property events** — Engine B event multipliers (e.g. conferences).
