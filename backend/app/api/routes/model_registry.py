"""Model registry API - list models and versions."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.model_registry import ModelRegistry
from app.models.user import User
from app.services.org_access import user_has_property_access

router = APIRouter(prefix="/model-registry", tags=["model-registry"])


@router.get("/models")
async def list_models(
    property_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List registered models - optionally filtered by property."""
    q = select(ModelRegistry).order_by(ModelRegistry.created_at.desc())
    if property_id:
        from app.services.org_access import user_has_property_access
        if not await user_has_property_access(db, current_user.id, property_id):
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Property not found")
        q = q.where(ModelRegistry.property_id == property_id)
    else:
        q = q.where(ModelRegistry.property_id.is_(None))

    result = await db.execute(q.limit(50))
    models = result.scalars().all()
    return [
        {
            "id": m.id,
            "model_name": m.model_name,
            "version": m.version,
            "property_id": m.property_id,
            "is_active": m.is_active,
            "metadata": m.metadata_,
            "created_at": m.created_at.isoformat(),
        }
        for m in models
    ]


@router.post("/models/{model_id}/activate")
async def activate_model(
    model_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Activate a model version (rollback). Deactivates other versions with same model_name and property."""
    result = await db.execute(select(ModelRegistry).where(ModelRegistry.id == model_id))
    reg = result.scalar_one_or_none()
    if not reg:
        raise HTTPException(status_code=404, detail="Model not found")
    if reg.property_id and not await user_has_property_access(db, current_user.id, reg.property_id):
        raise HTTPException(status_code=404, detail="Model not found")

    q = update(ModelRegistry).where(ModelRegistry.model_name == reg.model_name)
    if reg.property_id:
        q = q.where(ModelRegistry.property_id == reg.property_id)
    else:
        q = q.where(ModelRegistry.property_id.is_(None))
    await db.execute(q.values(is_active=False))
    reg.is_active = True
    await db.flush()
    return {
        "id": reg.id,
        "model_name": reg.model_name,
        "version": reg.version,
        "property_id": reg.property_id,
        "is_active": reg.is_active,
    }
