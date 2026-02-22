"""Portfolio dashboard - 30/60/90 outlook, rollups, alerts."""
import json
from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.organization import Organization, Property
from app.models.user import User
from app.services.org_access import get_org_ids_for_user
from app.models.engine import EngineRun, Recommendation
from app.models.engine_b_calendar import EngineBCalendar
from app.models.alert import Alert
from app.config import settings
from app.services.cache import get_redis

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("/outlook")
async def portfolio_outlook(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Rollups across properties: next 30/60/90 outlook. Cached."""
    r = await get_redis()
    if r:
        try:
            key = f"cache:portfolio:outlook:{current_user.id}"
            cached = await r.get(key)
            if cached:
                return json.loads(cached)
        except Exception:
            pass
    org_ids = await get_org_ids_for_user(db, current_user.id)
    if not org_ids:
        return {"outlook": [], "property_count": 0}

    props_result = await db.execute(
        select(Property).where(Property.organization_id.in_(org_ids))
    )
    props = props_result.scalars().all()

    today = date.today()
    horizons = [
        (30, (today + timedelta(days=30)).isoformat()),
        (60, (today + timedelta(days=60)).isoformat()),
        (90, (today + timedelta(days=90)).isoformat()),
    ]

    outlook = []
    for days, end_str in horizons:
        lift_query = (
            select(func.coalesce(func.sum(Recommendation.delta_dollars), 0))
            .join(EngineRun)
            .where(
                EngineRun.property_id.in_([p.id for p in props]),
                Recommendation.stay_date >= today.isoformat(),
                Recommendation.stay_date <= end_str,
            )
        )
        result = await db.execute(lift_query)
        total_lift = float(result.scalar() or 0)
        outlook.append({"horizon_days": days, "projected_lift": total_lift})

    result = {"outlook": outlook, "property_count": len(props)}
    if r:
        try:
            await r.setex(
                f"cache:portfolio:outlook:{current_user.id}",
                settings.api_cache_ttl_seconds,
                json.dumps(result, default=str),
            )
        except Exception:
            pass
    return result


@router.get("/forecast")
async def forecast_dashboard(
    property_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Dedicated 30/60/90 forecast: occupancy, ADR, RevPAR, pickup.
    Aggregates from latest Engine A (0-30d) and Engine B (31-90d) outputs.
    """
    org_ids = await get_org_ids_for_user(db, current_user.id)
    if not org_ids:
        return {"horizons": [], "property_count": 0}

    props_query = select(Property).where(Property.organization_id.in_(org_ids))
    if property_id:
        props_query = props_query.where(Property.id == property_id)
    props_result = await db.execute(props_query)
    props = props_result.scalars().all()
    prop_ids = [p.id for p in props]
    if not prop_ids:
        return {"horizons": [], "property_count": 0}

    today = date.today()
    horizons = [
        (30, today + timedelta(days=30)),
        (60, today + timedelta(days=60)),
        (90, today + timedelta(days=90)),
    ]

    recs_result = await db.execute(
        select(
            Recommendation.stay_date,
            Recommendation.occupancy_projection,
            Recommendation.suggested_bar,
            Recommendation.pickup_projection,
            Recommendation.revpar_impact,
            Recommendation.current_bar,
            EngineRun.property_id,
        )
        .join(EngineRun)
        .where(
            EngineRun.property_id.in_(prop_ids),
            EngineRun.engine_type == "engine_a",
        )
    )
    recs = recs_result.all()

    run_ids_result = await db.execute(
        select(EngineRun.id)
        .where(
            EngineRun.property_id.in_(prop_ids),
            EngineRun.engine_type == "engine_b",
        )
        .order_by(EngineRun.created_at.desc())
        .limit(100)
    )
    run_ids = [r[0] for r in run_ids_result.fetchall()]
    cal_entries = []
    if run_ids:
        cal_result = await db.execute(
            select(EngineBCalendar)
            .where(EngineBCalendar.engine_run_id.in_(run_ids))
        )
        cal_entries = cal_result.scalars().all()

    result_horizons = []
    for days, end_dt in horizons:
        start_str = today.isoformat()
        end_str = end_dt.isoformat()

        occ_vals, adr_vals, revpar_vals, pickup_vals = [], [], [], []
        for r in recs:
            if start_str <= r.stay_date <= end_str:
                occ = float(r.occupancy_projection or 75)
                adr = float(r.suggested_bar or r.current_bar or 0)
                occ_vals.append(occ)
                adr_vals.append(adr)
                revpar_vals.append(occ * adr / 100 if adr else 0)
                pickup_vals.append(float(r.pickup_projection or 5))

        for c in cal_entries:
            if start_str <= c.stay_date <= end_str:
                occ = float(c.occupancy_forecast_low or 0) + float(c.occupancy_forecast_high or 0)
                occ = occ / 2 if occ else 75
                adr = float(c.target or c.floor or 0)
                occ_vals.append(occ)
                adr_vals.append(adr)
                revpar_vals.append(occ * adr / 100 if adr else 0)
                pickup_vals.append(5.0)

        n = len(occ_vals)
        result_horizons.append({
            "days": days,
            "occupancy_avg": round(sum(occ_vals) / n, 1) if n else 0,
            "adr_avg": round(sum(adr_vals) / n, 2) if n else 0,
            "revpar_avg": round(sum(revpar_vals) / n, 2) if n else 0,
            "pickup_avg": round(sum(pickup_vals) / n, 1) if n else 0,
            "date_count": n,
        })

    return {
        "horizons": result_horizons,
        "property_count": len(props),
    }


@router.get("/alerts-rollup")
async def alerts_rollup(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Alerts rollup for portfolio."""
    org_ids = await get_org_ids_for_user(db, current_user.id)
    if not org_ids:
        return []
    result = await db.execute(
        select(Alert)
        .where(Alert.organization_id.in_(org_ids))
        .order_by(Alert.created_at.desc())
        .limit(limit)
    )
    alerts = result.scalars().all()
    return [
        {
            "id": a.id,
            "property_id": a.property_id,
            "alert_type": a.alert_type,
            "severity": a.severity,
            "title": a.title,
            "acknowledged": a.acknowledged,
            "created_at": a.created_at.isoformat(),
        }
        for a in alerts
    ]


@router.get("/value-rollup")
async def value_rollup(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """RateMaster value generated rollup. Cached."""
    r = await get_redis()
    if r:
        try:
            key = f"cache:portfolio:value:{current_user.id}"
            cached = await r.get(key)
            if cached:
                return json.loads(cached)
        except Exception:
            pass
    org_ids = await get_org_ids_for_user(db, current_user.id)
    if not org_ids:
        return {
            "realized_lift": 0,
            "projected_lift": 0,
            "property_count": 0,
        }
    props_result = await db.execute(
        select(Property).where(Property.organization_id.in_(org_ids))
    )
    props = props_result.scalars().all()
    prop_ids = [p.id for p in props]

    lift_result = await db.execute(
        select(func.coalesce(func.sum(Recommendation.delta_dollars), 0))
        .join(EngineRun)
        .where(
            EngineRun.property_id.in_(prop_ids),
            Recommendation.applied == True,
        )
    )
    realized = float(lift_result.scalar() or 0)

    all_lift_result = await db.execute(
        select(func.coalesce(func.sum(Recommendation.delta_dollars), 0))
        .join(EngineRun)
        .where(EngineRun.property_id.in_(prop_ids))
    )
    projected = float(all_lift_result.scalar() or 0)

    result = {
        "realized_lift": realized,
        "projected_lift": projected,
        "property_count": len(props),
    }
    if r:
        try:
            await r.setex(
                f"cache:portfolio:value:{current_user.id}",
                settings.api_cache_ttl_seconds,
                json.dumps(result, default=str),
            )
        except Exception:
            pass
    return result
