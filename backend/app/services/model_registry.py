"""Model registry - register versions, get active model for predictions."""
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.model_registry import ModelRegistry


def register_model(
    db: Session,
    model_name: str,
    version: str,
    property_id: str | None = None,
    metadata_: dict | None = None,
    set_active: bool = True,
) -> ModelRegistry:
    """
    Register a new model version. If set_active, deactivates other versions.
    """
    if set_active:
        q = update(ModelRegistry).where(ModelRegistry.model_name == model_name)
        if property_id:
            q = q.where(ModelRegistry.property_id == property_id)
        else:
            q = q.where(ModelRegistry.property_id.is_(None))
        db.execute(q.values(is_active=False))

    reg = ModelRegistry(
        model_name=model_name,
        version=version,
        property_id=property_id,
        metadata_=metadata_ or {},
        is_active=set_active,
    )
    db.add(reg)
    db.flush()
    return reg


def get_active_model(
    db: Session,
    model_name: str,
    property_id: str | None = None,
) -> ModelRegistry | None:
    """
    Get active model for property (or global if property_id None).
    Prefer property-calibrated over global.
    """
    # Property-specific first
    if property_id:
        result = db.execute(
            select(ModelRegistry)
            .where(ModelRegistry.model_name == model_name)
            .where(ModelRegistry.property_id == property_id)
            .where(ModelRegistry.is_active == True)
            .order_by(ModelRegistry.created_at.desc())
            .limit(1)
        )
        reg = result.scalar_one_or_none()
        if reg:
            return reg

    # Fall back to global
    result = db.execute(
        select(ModelRegistry)
        .where(ModelRegistry.model_name == model_name)
        .where(ModelRegistry.property_id.is_(None))
        .where(ModelRegistry.is_active == True)
        .order_by(ModelRegistry.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


def activate_model_version(
    db: Session,
    model_id: str,
) -> ModelRegistry | None:
    """
    Activate a model version by id (rollback). Deactivates other versions
    with same model_name and property_id.
    """
    result = db.execute(select(ModelRegistry).where(ModelRegistry.id == model_id))
    reg = result.scalar_one_or_none()
    if not reg:
        return None

    q = update(ModelRegistry).where(ModelRegistry.model_name == reg.model_name)
    if reg.property_id:
        q = q.where(ModelRegistry.property_id == reg.property_id)
    else:
        q = q.where(ModelRegistry.property_id.is_(None))
    db.execute(q.values(is_active=False))

    reg.is_active = True
    db.flush()
    return reg
