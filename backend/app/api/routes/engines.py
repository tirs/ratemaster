"""Engine runs and recommendations API."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.organization import Organization, Property
from app.models.user import User
from app.services.org_access import get_org_ids_for_user
from app.models.engine import EngineRun, Recommendation
from app.models.engine_b_calendar import EngineBCalendar
from app.schemas.engine import EngineRunResponse, EngineRunDetailResponse, RecommendationResponse

router = APIRouter(prefix="/engines", tags=["engines"])


@router.get("/runs", response_model=list[EngineRunResponse])
async def list_engine_runs(
    property_id: str | None = None,
    engine_type: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[EngineRunResponse]:
    """List engine runs for user's properties (owner, GM, or Analyst)."""
    org_ids = await get_org_ids_for_user(db, current_user.id)
    if not org_ids:
        return []
    query = (
        select(EngineRun)
        .join(Property)
        .where(Property.organization_id.in_(org_ids))
    )
    if property_id:
        query = query.where(EngineRun.property_id == property_id)
    if engine_type:
        query = query.where(EngineRun.engine_type == engine_type)
    query = query.order_by(EngineRun.created_at.desc()).limit(50)
    result = await db.execute(query)
    runs = result.scalars().all()
    return [
        EngineRunResponse(
            id=r.id,
            property_id=r.property_id,
            engine_type=r.engine_type,
            run_id=r.run_id,
            status=r.status,
            confidence=r.confidence,
            created_at=r.created_at.isoformat(),
        )
        for r in runs
    ]


@router.get("/runs/{run_id}", response_model=EngineRunDetailResponse)
async def get_engine_run(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EngineRunDetailResponse:
    """Get engine run with recommendations."""
    org_ids = await get_org_ids_for_user(db, current_user.id)
    if not org_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )
    result = await db.execute(
        select(EngineRun)
        .join(Property)
        .where(
            EngineRun.run_id == run_id,
            Property.organization_id.in_(org_ids),
        )
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )

    recs_result = await db.execute(
        select(Recommendation).where(Recommendation.engine_run_id == run.id)
    )
    recs = recs_result.scalars().all()
    recommendations = [
        RecommendationResponse(
            id=r.id,
            stay_date=r.stay_date,
            suggested_bar=float(r.suggested_bar) if r.suggested_bar else None,
            current_bar=float(r.current_bar) if r.current_bar else None,
            delta_dollars=float(r.delta_dollars) if r.delta_dollars else None,
            delta_pct=float(r.delta_pct) if r.delta_pct else None,
            occupancy_projection=float(r.occupancy_projection) if r.occupancy_projection else None,
            occupancy_projection_low=float(r.occupancy_projection_low) if r.occupancy_projection_low else None,
            occupancy_projection_high=float(r.occupancy_projection_high) if r.occupancy_projection_high else None,
            confidence=r.confidence,
            why_bullets=r.why_bullets,
            applied=r.applied,
        )
        for r in recs
    ]

    if run.engine_type == "engine_b":
        cal_result = await db.execute(
            select(EngineBCalendar).where(EngineBCalendar.engine_run_id == run.id)
        )
        cal_entries = cal_result.scalars().all()
        calendar = [
            {
                "stay_date": c.stay_date,
                "floor": float(c.floor) if c.floor else None,
                "target": float(c.target) if c.target else None,
                "stretch": float(c.stretch) if c.stretch else None,
                "confidence": c.confidence,
            }
            for c in cal_entries
        ]
        return EngineRunDetailResponse(
            id=run.id,
            property_id=run.property_id,
            engine_type=run.engine_type,
            run_id=run.run_id,
            status=run.status,
            confidence=run.confidence,
            created_at=run.created_at.isoformat(),
            recommendations=recommendations,
            calendar=calendar,
        )

    return EngineRunDetailResponse(
        id=run.id,
        property_id=run.property_id,
        engine_type=run.engine_type,
        run_id=run.run_id,
        status=run.status,
        confidence=run.confidence,
        created_at=run.created_at.isoformat(),
        recommendations=recommendations,
        calendar=None,
    )


@router.delete("/runs/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_engine_run(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an engine run and its recommendations/calendar. User must have access."""
    org_ids = await get_org_ids_for_user(db, current_user.id)
    if not org_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )
    result = await db.execute(
        select(EngineRun)
        .join(Property)
        .where(
            EngineRun.run_id == run_id,
            Property.organization_id.in_(org_ids),
        )
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )
    await db.execute(delete(EngineBCalendar).where(EngineBCalendar.engine_run_id == run.id))
    await db.execute(delete(Recommendation).where(Recommendation.engine_run_id == run.id))
    await db.execute(delete(EngineRun).where(EngineRun.id == run.id))


@router.post("/recommendations/{rec_id}/apply")
async def mark_recommendation_applied(
    rec_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark recommendation as applied. Owner and GM can approve; Analyst cannot."""
    from datetime import datetime, timezone

    from app.services.org_access import user_can_approve_for_property, user_has_property_access

    result = await db.execute(
        select(Recommendation, EngineRun.property_id)
        .join(EngineRun, Recommendation.engine_run_id == EngineRun.id)
        .where(Recommendation.id == rec_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found",
        )
    rec, property_id = row
    if not await user_has_property_access(db, current_user.id, property_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found",
        )
    if not await user_can_approve_for_property(db, current_user.id, property_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Owner, Full user, or GM can approve recommendations",
        )
    rec.applied = True
    rec.applied_at = datetime.now(timezone.utc)
    await db.flush()
    return {"applied": True}
