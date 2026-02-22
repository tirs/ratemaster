# RateMaster – Job Spec Compliance

Audit against the Senior Full-Stack Engineer job posting requirements.

**See [SPEC_SUMMARY.md](SPEC_SUMMARY.md) for the full audit with gaps.**

## Locked Stack [OK]

| Requirement | Status |
|-------------|--------|
| Frontend: Next.js (TypeScript) App Router in `/frontend` | [OK] |
| Backend: FastAPI (Python 3.11) in `/backend` | [OK] |
| Database: PostgreSQL | [OK] |
| Redis (caching + background jobs) | [OK] |
| Auth: email/password + JWT | [OK] |
| Monolith with modular services | [OK] |
| OpenAPI single source of truth | [OK] |
| snake_case request/response end-to-end | [OK] |
| Standard error envelope for ALL non-2xx (including 422) | [OK] |

## Repo Rules [OK]

| Requirement | Status |
|-------------|--------|
| Monorepo: only `/frontend` and `/backend` | [OK] |
| Frontend types from backend `/openapi.json` | [OK] `npm run generate:api` |
| No undocumented endpoints | [OK] |

---

## 1. Multi-Property / Portfolio

| Feature | Status |
|---------|--------|
| Organization (portfolio owner) accounts | [OK] |
| Multiple properties under org | [OK] |
| Roles: Owner / GM / Analyst | [OK] Settings → Team & Roles invite UI |
| Portfolio dashboard: 30/60/90 outlook | [OK] |
| Alerts rollup | [OK] |
| RateMaster value generated rollup | [OK] |

---

## 2. Data Ingestion + Data Health [OK]

| Feature | Status |
|---------|--------|
| CSV upload with column mapping + validation | [OK] |
| Import history + snapshot metadata | [OK] |
| Logical fields: stay_date, rooms_available, ADR, revenue, etc. | [OK] |
| Manual entry fallback | [OK] |
| Prior year upload (YoY) | [OK] |
| YoY trend curves (season/month, day-of-week) | [OK] |
| Data Health score per property | [OK] |
| Recommended fixes | [OK] |
| Data Health influences Confidence | [OK] |

---

## 3. Dual Engines + Projections + Confidence + "Why" [OK]

| Feature | Status |
|---------|--------|
| **Engine A** (0–30 days): BAR (Conservative/Balanced/Aggressive) | [OK] |
| Delta vs current, occupancy projection, pickup, sellout | [OK] |
| ADR/RevPAR impact, Confidence (0–100), "Why" bullets | [OK] |
| **Engine B** (31–365): Floor/Target/Stretch calendar | [OK] |
| Longer-range occupancy + ADR forecast bands | [OK] |
| Feature layer separated from decision layer | [OK] |
| Immutable run_id, reproducibility | [OK] |

---

## 4. ML Foundations [OK]

| Feature | Status |
|---------|--------|
| Predictor Interface (Engine A/B) | [OK] HeuristicPredictor |
| Feature Store (versioned) | [OK] Populated by engines, used for training |
| Model Registry (global + property calibration) | [OK] Register, get active, version on predictions |
| Training dataset builder | [OK] build_training_dataset (features + outcomes) |
| Training jobs (Redis-backed) | [OK] run_training_job, POST /jobs/training |
| Scheduled training jobs | [OK] run_training_jobs_scheduled on Celery beat (daily) |
| Outcomes/actuals import for learning | [OK] POST /outcomes/import |
| Confidence: data health + model uncertainty | [OK] |
| "Why" from stored drivers | [OK] |
| Guardrails (min/max BAR, max daily change, etc.) | [OK] |
| Fallback predictor | [OK] |

---

## 5. Market Signals [OK]

| Feature | Status |
|---------|--------|
| MarketDataAdapter (pluggable) | [OK] Interface + ManualEntryAdapter |
| Market snapshot storage | [OK] Model |
| Refresh cadence configurable | [OK] Celery beat every 30 min |
| Customer-provided / CSV upload | [OK] POST /market/import-csv |
| Options memo (2–3 approaches) | [OK] backend/docs/MARKET_OPTIONS_MEMO.md, README |
| Caching, rate limiting | [OK] Redis cache on portfolio, SlowAPI rate limit |
| Market snapshot → Engine A re-runs | [OK] create, import, refresh trigger run_engine_a |

---

## 6. Dashboards [OK]

| Feature | Status |
|---------|--------|
| Per-property: forecasts, rate calendar, why drivers | [OK] |
| Portfolio: rollups, alerts, opportunities | [OK] |
| Contribution: projected/realized lift, top wins | [OK] |
| Forecast dashboard: 30/60/90 occupancy, ADR, RevPAR, pickup | [OK] /dashboard/forecast |
| Baseline methodology shown | [OK] |

---

## 7. A/B/C/D Features

| Feature | Status |
|---------|--------|
| **A.** Audit trail, applied vs not applied | [OK] |
| **B.** Alerts + Task Inbox | [OK] sellout_risk, market_undercutting, pickup_deviation, confidence_issue |
| **C.** PDF + CSV exports | [OK] |
| **D.** Data integrity (Data Health) | [OK] |

---

## 8. Profit Tracking + Billing

| Feature | Status |
|---------|--------|
| Base fee + revenue share % | [OK] |
| Effective dates | [OK] Invoice filters by contract_effective_from/to |
| Monthly invoice output | [OK] |
| YoY reporting | [OK] |

---

## 9. Flow-Through (GOP) [OK]

| Feature | Status |
|---------|--------|
| Configurable flow-through % per property | [OK] |
| Revenue → GOP conversion | [OK] |
| Revenue share on revenue or GOP (configurable) | [OK] |

---

## Non-Negotiable Engineering [OK]

| Requirement | Status |
|-------------|--------|
| OpenAPI contract-first | [OK] |
| Error envelope all non-2xx | [OK] |
| Redis-backed background jobs | [OK] |
| Job status endpoints + UI progress | [OK] |
| Backend unit + integration tests | [OK] 23 tests |
| Frontend smoke tests | [OK] Smoke + happy path E2E |

---

## End-to-End Flow [OK]

1. Signup/login → create org/property | [OK]
2. Upload current + prior-year CSV → data health | [OK]
3. Market signals on schedule | [OK] Configurable 5-60 min
4. Run Engine A & B → progress visible | [OK]
5. Results: rate suggestions, deltas, confidence, why | [OK]
6. Applied vs not applied tracking | [OK]
7. Contribution dashboard + GOP lift | [OK]
8. Export PDF + CSV | [OK]
9. Frontend types from OpenAPI | [OK]
10. All errors use envelope | [OK]
11. ML foundations (feature store, registry, training) | [OK] |

---

## Implemented (Completed)

1. **Feature Store** – Populated by engines, queried for training
2. **Model Registry** – Register versions, get active, tag predictions
3. **Training Pipeline** – Dataset builder, run_training_job, POST /jobs/training
4. **Market Signals** – ManualEntryAdapter, CSV import, Celery beat refresh
5. **Test Coverage** – Feature store, predictor, model registry, API engines/market, import preview, data import, frontend smoke + happy path
6. **Column mapping** – User-configurable, auto-detect, POST /data/import/preview
7. **snapshot_date** – Populated from earliest stay_date or Form param
8. **Lead-time patterns** – YoY curves by lead_time bucket when booking_date in CSV
9. **Redis caching** – Portfolio outlook, value-rollup cached
10. **Rate limiting** – SlowAPI 120/min (configurable)
11. **Market cadence** – MARKET_REFRESH_MINUTES 5-60
12. **Events in Engine B** – PropertyEvent model, GET/POST/DELETE /properties/{id}/events
