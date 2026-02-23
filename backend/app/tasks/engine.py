"""Engine run tasks - Engine A (tactical) and Engine B (strategic)."""
import uuid
from datetime import date, timedelta

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, Session

from app.celery_app import celery_app
from app.config import settings
from app.models.base import Base
from app.models.data_import import DataSnapshot, DataSnapshotRow
from app.services.feature_store import (
    compute_features,
    get_latest_market_snapshot,
    store_features,
)
from app.services.predictor import (
    PredictionInput,
    get_predictor_for_property,
)
from app.services.yoy_curves import get_yoy_multiplier
from app.services.property_events import get_event_multiplier
from app.services.model_registry import get_active_model, register_model
from app.models.alert import Alert

# Sync engine for Celery (tasks run in sync context)
sync_engine = create_engine(
    settings.database_url.replace("+asyncpg", ""),
    echo=False,
)
SyncSession = sessionmaker(sync_engine, autocommit=False, autoflush=False)


def get_sync_session() -> Session:
    return SyncSession()


def _create_engine_a_alerts(
    db: Session,
    org_id: str,
    property_id: str,
    recommendations: list[dict],
    min_conf: int | None,
    data_health_score: int | None,
) -> None:
    """Create sellout risk, market undercutting, pickup deviation, confidence alerts."""
    data_health = data_health_score or 50

    sellout_risk_count = 0
    market_undercut_count = 0
    pickup_dev_count = 0

    for rec in recommendations:
        sellout_prob = rec.get("sellout_probability") or 0
        sellout_eff = rec.get("sellout_efficiency") or 1.0
        if sellout_prob >= 80 or sellout_eff < 0.7:
            sellout_risk_count += 1
        compset_avg = rec.get("compset_avg")
        if compset_avg is not None and rec.get("suggested_bar"):
            if float(rec["suggested_bar"]) < float(compset_avg) * 0.95:
                market_undercut_count += 1
        pickup = rec.get("pickup_projection") or 0
        if pickup < 0 or pickup > 30:
            pickup_dev_count += 1

    if sellout_risk_count > 0:
        db.add(Alert(
            organization_id=org_id,
            property_id=property_id,
            alert_type="sellout_risk",
            severity="warning",
            title="Sellout risk detected",
            message=f"{sellout_risk_count} dates with high sellout probability or low efficiency",
            payload={"count": sellout_risk_count},
        ))
    compset_any = next((r.get("compset_avg") for r in recommendations if r.get("compset_avg") is not None), None)
    if market_undercut_count > 0 and compset_any is not None:
        db.add(Alert(
            organization_id=org_id,
            property_id=property_id,
            alert_type="market_undercutting",
            severity="warning",
            title="Market undercutting",
            message=f"{market_undercut_count} dates below compset avg (${float(compset_any):.0f})",
            payload={"count": market_undercut_count, "compset_avg": float(compset_any)},
        ))
    if pickup_dev_count > 0:
        db.add(Alert(
            organization_id=org_id,
            property_id=property_id,
            alert_type="pickup_deviation",
            severity="info",
            title="Pickup deviation",
            message=f"{pickup_dev_count} dates with pickup projection outside expected range",
            payload={"count": pickup_dev_count},
        ))
    if data_health < 50 or (min_conf and data_health < min_conf):
        db.add(Alert(
            organization_id=org_id,
            property_id=property_id,
            alert_type="confidence_issue",
            severity="warning",
            title="Low data confidence",
            message=f"Data health score {data_health} below threshold",
            payload={"data_health_score": data_health, "min_threshold": min_conf},
        ))


def _compute_derived_projections(
    features: dict,
    days_until_stay: int,
) -> dict:
    """
    Derive occupancy range, pickup, sellout_probability, sellout_efficiency
    from features (no placeholders).
    """
    hist_occ = features.get("historical_occupancy")
    data_health = features.get("data_health_score") or 50
    rooms_avail = features.get("rooms_available")
    rooms_sold = features.get("rooms_sold")

    # Occupancy projection: midpoint from historical, range ±8 (wider if no data)
    occ_mid = float(hist_occ) if hist_occ is not None else 70.0
    band = 10.0 if hist_occ is None else 8.0
    occ_low = max(0.0, round(occ_mid - band, 2))
    occ_high = min(100.0, round(occ_mid + band, 2))
    occupancy_projection = round(occ_mid, 2)
    occupancy_projection_low = occ_low
    occupancy_projection_high = occ_high

    # Pickup: expected additional rooms to sell. Based on rooms remaining and lead time.
    # Pickup rate: 5% base + up to 15% for longer lead (30d out ~20%, 7d out ~8%)
    if rooms_avail is not None and rooms_sold is not None:
        rooms_remaining = max(0, rooms_avail - rooms_sold)
        pickup_rate = 0.05 + min(0.15, days_until_stay / 200.0)  # 0.05-0.20
        pickup = min(rooms_remaining * pickup_rate, 25.0)
    else:
        pickup = 10.0 if days_until_stay > 14 else 5.0  # heuristic when no room data
    pickup_projection = round(pickup, 2)

    # Sellout probability: higher when occupancy already high
    sellout_probability = round(40.0 + min(hist_occ or 70.0, 80.0) * 0.5, 2)
    sellout_probability = min(95.0, sellout_probability)

    # Sellout efficiency: 0.8-1.0 from data_health (higher health = higher efficiency)
    sellout_efficiency = round(0.8 + (data_health / 100.0) * 0.2, 2)
    sellout_efficiency = min(1.0, sellout_efficiency)

    return {
        "occupancy_projection": occupancy_projection,
        "occupancy_projection_low": occupancy_projection_low,
        "occupancy_projection_high": occupancy_projection_high,
        "pickup_projection": pickup_projection,
        "sellout_probability": sellout_probability,
        "sellout_efficiency": sellout_efficiency,
    }


def _ensure_heuristic_model(db: Session, model_name: str, desc: str) -> str:
    """Ensure heuristic model is registered; return version."""
    reg = get_active_model(db, model_name, property_id=None)
    if reg:
        return reg.version
    reg = register_model(
        db, model_name, "v1.0.0",
        property_id=None,
        metadata_={"type": "heuristic", "description": desc},
        set_active=True,
    )
    db.flush()
    return reg.version


@celery_app.task(bind=True)
def run_engine_a(self, property_id: str) -> dict:
    """
    Engine A - Tactical (0-30 days).
    Heuristic predictor: uses latest snapshot data for BAR suggestions.
    """
    run_id = str(uuid.uuid4())
    self.update_state(state="PROGRESS", meta={"run_id": run_id, "step": "loading_data"})

    db = get_sync_session()
    try:
        snapshot_result = db.execute(
            select(DataSnapshot).where(
                DataSnapshot.property_id == property_id,
                DataSnapshot.snapshot_type == "current",
            ).order_by(DataSnapshot.created_at.desc()).limit(1)
        )
        snapshot = snapshot_result.scalar_one_or_none()
        if not snapshot:
            return {"run_id": run_id, "status": "no_data", "recommendations": []}

        rows_result = db.execute(
            select(DataSnapshotRow).where(
                DataSnapshotRow.snapshot_id == snapshot.id
            )
        )
        rows = rows_result.scalars().all()

        adr_avg = float(
            sum((float(r.adr) if r.adr else 0) for r in rows if r.adr)
            / max(1, sum(1 for r in rows if r.adr))
        ) if any(r.adr for r in rows) else 100.0

        today = date.today()
        horizon = today + timedelta(days=30)
        recommendations = []

        self.update_state(state="PROGRESS", meta={"run_id": run_id, "step": "computing"})

        from app.models.organization import Property
        from app.models.engine import EngineRun, Recommendation

        prop_result = db.execute(select(Property).where(Property.id == property_id))
        prop = prop_result.scalar_one_or_none()
        min_bar = float(prop.min_bar) if prop and prop.min_bar else None
        max_bar = float(prop.max_bar) if prop and prop.max_bar else None
        max_daily_pct = float(prop.max_daily_change_pct) if prop and prop.max_daily_change_pct else None
        blackout = set(prop.blackout_dates or []) if prop else set()
        dow_rules = prop.dow_rules or {} if prop else {}
        min_conf = prop.min_confidence_threshold if prop else None

        predictor = get_predictor_for_property(db, property_id)
        reg = get_active_model(db, "engine_a_heuristic", property_id=property_id)
        if not reg:
            reg = get_active_model(db, "engine_a_heuristic", property_id=None)
        model_version = reg.version if reg else _ensure_heuristic_model(
            db, "engine_a_heuristic", "2% lift from historical ADR"
        )
        first_market_snap = None

        for d in range(31):
            stay_d = today + timedelta(days=d)
            if stay_d > horizon:
                break
            stay_str = stay_d.isoformat()
            if stay_str in blackout:
                continue
            market_snap, market_signal_val = get_latest_market_snapshot(
                db, property_id, stay_date=stay_str
            )
            if market_snap and first_market_snap is None:
                first_market_snap = market_snap

            row_for_date = next((r for r in rows if r.stay_date == stay_str), None)
            current_bar = float(row_for_date.adr) if row_for_date and row_for_date.adr else float(adr_avg)

            features = compute_features(
                db, property_id, run_id, stay_str, snapshot, rows, market_signal_val
            )
            store_features(db, property_id, run_id, stay_str, features)

            inp = PredictionInput(
                property_id=property_id,
                stay_date=stay_str,
                historical_adr=features.get("historical_adr"),
                historical_occupancy=features.get("historical_occupancy"),
                data_health_score=features.get("data_health_score"),
                market_signal=market_signal_val,
                features=features,
                market_snapshot_at=market_snap.snapshot_at if market_snap else None,
            )
            out = predictor.predict(inp)
            balanced = out.suggested_bar
            conservative = round(balanced * 0.99, 2)
            aggressive = round(balanced * 1.02, 2)

            if min_bar is not None:
                conservative = max(conservative, min_bar)
                balanced = max(balanced, min_bar)
                aggressive = max(aggressive, min_bar)
            if max_bar is not None:
                conservative = min(conservative, max_bar)
                balanced = min(balanced, max_bar)
                aggressive = min(aggressive, max_bar)
            if max_daily_pct is not None and current_bar:
                max_delta = current_bar * (max_daily_pct / 100)
                if conservative - current_bar > max_delta:
                    conservative = round(current_bar + max_delta, 2)
                if balanced - current_bar > max_delta:
                    balanced = round(current_bar + max_delta, 2)
                if aggressive - current_bar > max_delta:
                    aggressive = round(current_bar + max_delta, 2)

            dow_mult = 1.0
            dow_key = str(stay_d.weekday())
            if dow_key in dow_rules and isinstance(dow_rules[dow_key], (int, float)):
                dow_mult = float(dow_rules[dow_key])
            elif "weekend_premium_pct" in dow_rules and stay_d.weekday() >= 5:
                pct = float(dow_rules.get("weekend_premium_pct", 0) or 0)
                dow_mult = 1.0 + pct / 100.0
            if dow_mult != 1.0:
                conservative = round(conservative * dow_mult, 2)
                balanced = round(balanced * dow_mult, 2)
                aggressive = round(aggressive * dow_mult, 2)

            suggested = balanced
            if min_conf is not None and out.confidence < min_conf:
                suggested = conservative
            delta = suggested - current_bar
            delta_pct = (delta / current_bar * 100) if current_bar else 0
            conf_level = "high" if out.confidence >= 75 else "med" if out.confidence >= 50 else "low"

            derived = _compute_derived_projections(features, d)

            recommendations.append({
                "stay_date": stay_str,
                "compset_avg": market_signal_val,
                "suggested_bar": suggested,
                "conservative_bar": conservative,
                "balanced_bar": balanced,
                "aggressive_bar": aggressive,
                "current_bar": current_bar,
                "delta_dollars": round(delta, 2),
                "delta_pct": round(delta_pct, 2),
                "occupancy_projection": derived["occupancy_projection"],
                "occupancy_projection_low": derived["occupancy_projection_low"],
                "occupancy_projection_high": derived["occupancy_projection_high"],
                "pickup_projection": derived["pickup_projection"],
                "sellout_probability": derived["sellout_probability"],
                "sellout_efficiency": derived["sellout_efficiency"],
                "revpar_impact": round(delta * 0.75, 2),
                "confidence": out.confidence,
                "confidence_level": conf_level,
                "why_bullets": list(out.why_drivers),
            })

        run_inputs: dict = {
            "property_id": property_id,
            "row_count": len(rows),
        }
        if first_market_snap:
            run_inputs["market_snapshot_id"] = first_market_snap.id

        engine_run = EngineRun(
            id=str(uuid.uuid4()),
            property_id=property_id,
            engine_type="engine_a",
            run_id=run_id,
            status="completed",
            inputs=run_inputs,
            outputs={
                "recommendation_count": len(recommendations),
                "model_version": model_version,
            },
            confidence=snapshot.data_health_score,
            why_drivers=["historical_adr", "data_health"],
        )
        db.add(engine_run)
        db.flush()

        for rec in recommendations:
            rec_obj = Recommendation(
                id=str(uuid.uuid4()),
                engine_run_id=engine_run.id,
                stay_date=rec["stay_date"],
                suggested_bar=rec["suggested_bar"],
                conservative_bar=rec.get("conservative_bar"),
                balanced_bar=rec.get("balanced_bar"),
                aggressive_bar=rec.get("aggressive_bar"),
                current_bar=rec["current_bar"],
                delta_dollars=rec["delta_dollars"],
                delta_pct=rec["delta_pct"],
                occupancy_projection=rec["occupancy_projection"],
                occupancy_projection_low=rec.get("occupancy_projection_low"),
                occupancy_projection_high=rec.get("occupancy_projection_high"),
                pickup_projection=rec.get("pickup_projection"),
                sellout_probability=rec.get("sellout_probability"),
                sellout_efficiency=rec.get("sellout_efficiency"),
                revpar_impact=rec.get("revpar_impact"),
                confidence_level=rec.get("confidence_level"),
                confidence=rec["confidence"],
                why_bullets=rec["why_bullets"],
                applied=False,
            )
            db.add(rec_obj)

        org_id = prop.organization_id if prop else None
        if org_id:
            alert = Alert(
                organization_id=org_id,
                property_id=property_id,
                alert_type="engine_run_complete",
                severity="info",
                title="Engine A run completed",
                message=f"Generated {len(recommendations)} recommendations",
                payload={"run_id": run_id},
            )
            db.add(alert)

            _create_engine_a_alerts(
                db, org_id, property_id, recommendations,
                min_conf, snapshot.data_health_score,
            )

        db.commit()
        return {
            "run_id": run_id,
            "status": "completed",
            "recommendations": recommendations,
        }
    finally:
        db.close()


def _engine_b_floor_stretch_bands(days_until_stay: int) -> tuple[float, float]:
    """
    Dynamic floor/stretch bands by lead time. Wider when further out.
    31-60d: 0.88–1.12, 61-90d: 0.85–1.15, 91-180d: 0.82–1.18, 181+: 0.80–1.20
    """
    if days_until_stay <= 60:
        return 0.88, 1.12
    if days_until_stay <= 90:
        return 0.85, 1.15
    if days_until_stay <= 180:
        return 0.82, 1.18
    return 0.80, 1.20


@celery_app.task(bind=True)
def run_engine_b(self, property_id: str) -> dict:
    """
    Engine B - Strategic (31-365 days).
    Seasonality-based floor/target/stretch with YoY curves, events, property constraints.
    """
    run_id = str(uuid.uuid4())
    self.update_state(state="PROGRESS", meta={"run_id": run_id, "step": "loading_data"})

    db = get_sync_session()
    try:
        from app.models.engine import EngineRun, Recommendation
        from app.models.engine_b_calendar import EngineBCalendar
        from app.models.organization import Property

        snapshot_result = db.execute(
            select(DataSnapshot).where(
                DataSnapshot.property_id == property_id,
                DataSnapshot.snapshot_type.in_(["current", "prior_year"]),
            ).order_by(DataSnapshot.created_at.desc()).limit(1)
        )
        snapshot = snapshot_result.scalar_one_or_none()
        if not snapshot:
            return {"run_id": run_id, "status": "no_data", "calendar": []}

        rows_result = db.execute(
            select(DataSnapshotRow).where(
                DataSnapshotRow.snapshot_id == snapshot.id
            )
        )
        rows = rows_result.scalars().all()
        adr_avg = float(
            sum((float(r.adr) if r.adr else 0) for r in rows if r.adr)
            / max(1, sum(1 for r in rows if r.adr))
        ) if any(r.adr for r in rows) else 100.0

        predictor = get_predictor_for_property(db, property_id, model_name="engine_b_heuristic")
        reg = get_active_model(db, "engine_b_heuristic", property_id=property_id)
        if not reg:
            reg = get_active_model(db, "engine_b_heuristic", property_id=None)
        model_version = reg.version if reg else _ensure_heuristic_model(
            db, "engine_b_heuristic", "Seasonality-based floor/target/stretch"
        )

        prop_result = db.execute(select(Property).where(Property.id == property_id))
        prop = prop_result.scalar_one_or_none()
        min_bar = float(prop.min_bar) if prop and prop.min_bar else None
        max_bar = float(prop.max_bar) if prop and prop.max_bar else None
        blackout = set(prop.blackout_dates or []) if prop else set()
        dow_rules = prop.dow_rules or {} if prop else {}

        today = date.today()
        calendar = []
        for d in range(31, 366):
            stay_d = today + timedelta(days=d)
            stay_str = stay_d.isoformat()
            if stay_str in blackout:
                continue

            days_until_stay = d
            features = compute_features(
                db, property_id, run_id, stay_str, snapshot, rows, None
            )
            store_features(db, property_id, run_id, stay_str, features)

            inp = PredictionInput(
                property_id=property_id,
                stay_date=stay_str,
                historical_adr=features.get("historical_adr"),
                historical_occupancy=features.get("historical_occupancy"),
                data_health_score=features.get("data_health_score"),
                market_signal=None,
                features=features,
                market_snapshot_at=None,
            )
            out = predictor.predict(inp)
            target = out.suggested_bar

            band_lo, band_hi = _engine_b_floor_stretch_bands(days_until_stay)
            floor = round(target * band_lo, 2)
            stretch = round(target * band_hi, 2)

            yoy_mult = get_yoy_multiplier(db, property_id, stay_str, days_until_stay=days_until_stay)
            event_mult = get_event_multiplier(db, property_id, stay_str)
            floor = round(floor * yoy_mult * event_mult, 2)
            target = round(target * yoy_mult * event_mult, 2)
            stretch = round(stretch * yoy_mult * event_mult, 2)

            if min_bar is not None:
                floor = max(floor, min_bar)
                target = max(target, min_bar)
                stretch = max(stretch, min_bar)
            if max_bar is not None:
                floor = min(floor, max_bar)
                target = min(target, max_bar)
                stretch = min(stretch, max_bar)

            dow_mult = 1.0
            dow_key = str(stay_d.weekday())
            if dow_key in dow_rules and isinstance(dow_rules[dow_key], (int, float)):
                dow_mult = float(dow_rules[dow_key])
            elif "weekend_premium_pct" in dow_rules and stay_d.weekday() >= 5:
                pct = float(dow_rules.get("weekend_premium_pct", 0) or 0)
                dow_mult = 1.0 + pct / 100.0
            if dow_mult != 1.0:
                floor = round(floor * dow_mult, 2)
                target = round(target * dow_mult, 2)
                stretch = round(stretch * dow_mult, 2)

            hist_occ = features.get("historical_occupancy")
            occ_mid = float(hist_occ) if hist_occ is not None else 75.0
            occ_band = 12.0 if hist_occ is None else 8.0
            occ_low = max(0.0, round(occ_mid - occ_band, 2))
            occ_high = min(100.0, round(occ_mid + occ_band, 2))

            why_bullets = list(out.why_drivers)
            if yoy_mult != 1.0:
                why_bullets.append("yoy_curves")
            if event_mult != 1.0:
                why_bullets.append("events")

            calendar.append({
                "stay_date": stay_str,
                "floor": floor,
                "target": target,
                "stretch": stretch,
                "occupancy_forecast_low": occ_low,
                "occupancy_forecast_high": occ_high,
                "confidence": out.confidence or snapshot.data_health_score or 60,
                "why_bullets": why_bullets,
            })

        org_id = prop.organization_id if prop else None

        engine_run = EngineRun(
            id=str(uuid.uuid4()),
            property_id=property_id,
            engine_type="engine_b",
            run_id=run_id,
            status="completed",
            inputs={"property_id": property_id},
            outputs={"calendar_count": len(calendar), "model_version": model_version},
            confidence=snapshot.data_health_score,
            why_drivers=["seasonality", "yoy_curves", "events"],
        )
        db.add(engine_run)
        db.flush()

        for c in calendar:
            cal_entry = EngineBCalendar(
                id=str(uuid.uuid4()),
                engine_run_id=engine_run.id,
                stay_date=c["stay_date"],
                floor=c["floor"],
                target=c["target"],
                stretch=c["stretch"],
                occupancy_forecast_low=c["occupancy_forecast_low"],
                occupancy_forecast_high=c["occupancy_forecast_high"],
                confidence=c["confidence"],
                why_bullets=c["why_bullets"],
            )
            db.add(cal_entry)

        for c in calendar:
            stay_str = c["stay_date"]
            try:
                stay_d = date.fromisoformat(stay_str)
            except (ValueError, TypeError):
                continue
            days_out = (stay_d - today).days
            if days_out < 31 or days_out > 90:
                continue
            row_for_date = next((r for r in rows if r.stay_date == stay_str), None)
            current_bar = float(row_for_date.adr) if row_for_date and row_for_date.adr else adr_avg
            target_bar = c["target"]
            delta = target_bar - current_bar
            delta_pct = (delta / current_bar * 100) if current_bar else 0
            rec_obj = Recommendation(
                id=str(uuid.uuid4()),
                engine_run_id=engine_run.id,
                stay_date=stay_str,
                suggested_bar=target_bar,
                conservative_bar=c["floor"],
                balanced_bar=target_bar,
                aggressive_bar=c["stretch"],
                current_bar=current_bar,
                delta_dollars=round(delta, 2),
                delta_pct=round(delta_pct, 2),
                occupancy_projection=(c["occupancy_forecast_low"] + c["occupancy_forecast_high"]) / 2,
                occupancy_projection_low=c["occupancy_forecast_low"],
                occupancy_projection_high=c["occupancy_forecast_high"],
                confidence=c["confidence"],
                why_bullets=c["why_bullets"],
                applied=False,
            )
            db.add(rec_obj)

        if org_id:
            alert = Alert(
                organization_id=org_id,
                property_id=property_id,
                alert_type="engine_run_complete",
                severity="info",
                title="Engine B run completed",
                message=f"Generated {len(calendar)} calendar entries",
                payload={"run_id": run_id},
            )
            db.add(alert)

        db.commit()

        return {
            "run_id": run_id,
            "status": "completed",
            "calendar": calendar,
        }
    finally:
        db.close()
