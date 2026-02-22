"""Alerts and task inbox API."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.alert import Alert
from app.models.user import User

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("")
async def list_alerts(
    property_id: str | None = None,
    acknowledged: bool | None = None,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Property-level inbox + portfolio rollup."""
    from app.services.org_access import get_org_ids_for_user

    org_ids = await get_org_ids_for_user(db, current_user.id)
    if not org_ids:
        return []
    query = select(Alert).where(Alert.organization_id.in_(org_ids))
    if property_id:
        query = query.where(Alert.property_id == property_id)
    if acknowledged is not None:
        query = query.where(Alert.acknowledged == acknowledged)
    query = query.order_by(Alert.created_at.desc()).limit(limit)
    result = await db.execute(query)
    alerts = result.scalars().all()
    return [
        {
            "id": a.id,
            "property_id": a.property_id,
            "alert_type": a.alert_type,
            "severity": a.severity,
            "title": a.title,
            "message": a.message,
            "acknowledged": a.acknowledged,
            "created_at": a.created_at.isoformat(),
        }
        for a in alerts
    ]


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark alert as acknowledged."""
    from app.services.org_access import user_has_org_access

    result = await db.execute(
        select(Alert).where(Alert.id == alert_id)
    )
    alert = result.scalar_one_or_none()
    if not alert:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Alert not found")
    if not await user_has_org_access(db, current_user.id, alert.organization_id):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Forbidden")
    alert.acknowledged = True
    await db.flush()
    return {"acknowledged": True}
