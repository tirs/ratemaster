# Deliverables / Acceptance Criteria ("Done Means") – Verification Report

**Date:** 2025-02-22  
**Status:** All 11 items verified

---

## 1. Signup/login → create org/property

| Check | Status | Evidence |
|-------|--------|----------|
| Signup flow | ✅ | `frontend/src/app/(auth)/signup/page.tsx`, `backend/app/api/routes/auth.py` |
| Login flow | ✅ | `frontend/src/app/(auth)/login/page.tsx`, JWT auth |
| Create org | ✅ | `POST /api/v1/organizations`, `frontend/src/app/dashboard/settings/page.tsx` |
| Create property | ✅ | `POST /api/v1/properties`, `frontend/src/app/dashboard/properties/page.tsx` |
| Smoke test | ✅ | `frontend/tests/smoke.spec.ts` – login → create org/property → upload → run → results |

---

## 2. Upload current CSV + prior-year data → data health score shown

| Check | Status | Evidence |
|-------|--------|----------|
| CSV upload (current) | ✅ | `frontend/src/app/dashboard/data/page.tsx`, `POST /api/v1/data-import/upload` |
| Prior-year upload | ✅ | Same data page – "Prior Year" upload section |
| Data health score | ✅ | `GET /api/v1/data-import/health-summary`, `data_health_score` in snapshot |
| Health badge on engines/forecast | ✅ | `engines/page.tsx`, `forecast/page.tsx` – badge when property selected |

---

## 3. Market signals ingested on schedule

| Check | Status | Evidence |
|-------|--------|----------|
| Market signals ingestion | ✅ | `backend/app/tasks/market_signals.py`, `ingest_market_signals` |
| Scheduled job | ✅ | `backend/app/celery_app.py` – `ingest-market-signals` in beat schedule |
| Configurable method | ✅ | Celery beat config, env-based |

---

## 4. Run Engine A & B as jobs → progress visible

| Check | Status | Evidence |
|-------|--------|----------|
| Engine A job | ✅ | `POST /api/v1/jobs/engine-a`, `backend/app/tasks/engine.py` – `run_engine_a` |
| Engine B job | ✅ | `POST /api/v1/jobs/engine-b`, `run_engine_b` |
| Job status / progress | ✅ | `GET /api/v1/jobs/{job_id}`, `status` field; frontend polls for progress |
| Engines page | ✅ | `frontend/src/app/dashboard/engines/page.tsx` – run buttons, job status display |

---

## 5. Results show rate suggestions, deltas, projections, confidence, why bullets

| Check | Status | Evidence |
|-------|--------|----------|
| Rate suggestions | ✅ | `suggested_bar`, `conservative_bar`, `balanced_bar`, `aggressive_bar` |
| Deltas | ✅ | `delta_dollars`, `delta_pct` on recommendations |
| Projections | ✅ | Engine A: `occupancy_projection`, `occupancy_projection_low/high`, `revpar_impact`; Engine B: `floor`, `target`, `stretch` |
| Confidence | ✅ | `confidence`, `confidence_level`, `sellout_probability` |
| Why bullets | ✅ | `why_bullets`, `why_drivers` on recommendations and engine runs |
| UI display | ✅ | `engines/page.tsx` – table with all fields, floor/target/stretch, occupancy range |

---

## 6. Applied vs not applied tracking works

| Check | Status | Evidence |
|-------|--------|----------|
| `applied` flag on recommendations | ✅ | `Recommendation.applied` in DB, `PATCH /api/v1/recommendations/{id}` |
| Applied filter on engines page | ✅ | `setAppliedFilter("all" \| "applied" \| "not_applied")` |
| Contribution summary | ✅ | `applied_count`, `recommendations_in_horizon` in `contributionSummary` |
| Avoided losses | ✅ | `GET /api/v1/contribution/avoided-losses`, "Applied vs Not Applied" section on contribution page |

---

## 7. Contribution dashboard shows lift vs baseline + estimated GOP lift

| Check | Status | Evidence |
|-------|--------|----------|
| Lift vs baseline | ✅ | `lift_vs_baseline`, `projected_lift_60d`, `projected_lift_90d`, `realized_from_actuals` |
| Estimated GOP lift | ✅ | `estimated_gop_lift`, GOP-related fields in contribution summary |
| Flow-through display | ✅ | `flow_through_pct` from API (no longer hardcoded 70%) |
| Contribution page | ✅ | `frontend/src/app/dashboard/contribution/page.tsx` – cards for lift, GOP, flow-through |

---

## 8. Export PDF + CSV works

| Check | Status | Evidence |
|-------|--------|----------|
| CSV export | ✅ | `GET /api/v1/exports/contribution.csv`, `exportCsv()` on contribution page |
| PDF export | ✅ | `GET /api/v1/exports/contribution.pdf`, `exportReportPdf()` |
| HTML export | ✅ | `GET /api/v1/exports/contribution.html` (bonus) |
| UI buttons | ✅ | Contribution page – "Export CSV", "Export PDF", "Export HTML" |

---

## 9. Frontend types generated from OpenAPI and remain in sync

| Check | Status | Evidence |
|-------|--------|----------|
| OpenAPI dump script | ✅ | `backend/scripts/dump_openapi.py` – dumps schema to `frontend/openapi.json` |
| Type generation | ✅ | `npm run generate:api` – `openapi-typescript ./openapi.json -o src/lib/api-client.generated.ts` |
| Generated types used | ✅ | `api-client.ts` imports `components` from `api-client.generated.ts` |
| Sync workflow | ✅ | Run `generate:api` after backend schema changes |

---

## 10. All errors use standard error envelope (including 422)

| Check | Status | Evidence |
|-------|--------|----------|
| Error envelope schema | ✅ | `ErrorEnvelope` in `app/schemas/errors.py`, `error_envelope_response()` |
| 422 validation handler | ✅ | `validation_exception_handler` in `app/main.py` – converts `RequestValidationError` to envelope |
| 401/404 handlers | ✅ | `test_401_error_envelope`, `test_404_error_envelope` in `test_auth.py` |
| 422 test | ✅ | `test_validation_error_envelope` in `test_auth.py` |
| OpenAPI 422 response | ✅ | `main.py` – `422: {"model": "ErrorEnvelope", "description": "Validation error"}` |

---

## 11. ML foundations exist: feature store + model registry + training job pipeline + model version tagging on predictions

| Check | Status | Evidence |
|-------|--------|----------|
| Feature store | ✅ | `app/models/feature_store.py`, `app/services/feature_store.py`, `FeatureStore` table; `compute_features`, `store_features`, `get_latest_features` |
| Model registry | ✅ | `app/models/model_registry.py`, `app/services/model_registry.py`, `ModelRegistry` table; `register_model`, `get_active_model`, `activate_model_version` |
| Training job pipeline | ✅ | `app/tasks/training.py` – `run_training_job`, `run_training_jobs_scheduled`; `POST /api/v1/jobs/training`; Celery beat `run-training-jobs` |
| Dataset builder | ✅ | `app/services/dataset_builder.py` – builds from `feature_store` + outcomes |
| Model version tagging on predictions | ✅ | `engine.py` – `outputs={"model_version": model_version}` on `EngineRun`; `model_version` from `get_active_model` or heuristic fallback |
| Tests | ✅ | `test_feature_store.py`, `test_model_registry.py`, `test_predictor.py` |

---

## Summary

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Signup/login → create org/property | ✅ |
| 2 | Upload CSV + prior-year → data health score | ✅ |
| 3 | Market signals on schedule | ✅ |
| 4 | Run Engine A & B as jobs, progress visible | ✅ |
| 5 | Results: suggestions, deltas, projections, confidence, why bullets | ✅ |
| 6 | Applied vs not applied tracking | ✅ |
| 7 | Contribution: lift vs baseline + GOP lift | ✅ |
| 8 | Export PDF + CSV | ✅ |
| 9 | Frontend types from OpenAPI, in sync | ✅ |
| 10 | Standard error envelope (incl. 422) | ✅ |
| 11 | ML foundations: feature store, registry, training, model version tagging | ✅ |

**All 11 deliverables verified.**
