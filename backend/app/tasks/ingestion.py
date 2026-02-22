"""Data ingestion tasks - async processing for large CSV."""
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.celery_app import celery_app
from app.config import settings
from app.models.data_import import DataSnapshot
from app.services.yoy_curves import compute_yoy_curves

_sync_engine = create_engine(
    settings.database_url.replace("+asyncpg", ""),
    echo=False,
)
_SyncSession = sessionmaker(_sync_engine, autocommit=False, autoflush=False)


@celery_app.task
def process_import_async(snapshot_id: str) -> dict:
    """Process large import in background (validation, YoY curves for prior_year)."""
    db = _SyncSession()
    try:
        result = db.execute(select(DataSnapshot).where(DataSnapshot.id == snapshot_id))
        snap = result.scalar_one_or_none()
        if snap and snap.snapshot_type == "prior_year":
            count = compute_yoy_curves(db, snap.property_id)
            db.commit()
            return {"snapshot_id": snapshot_id, "status": "processed", "yoy_curves": count}
        return {"snapshot_id": snapshot_id, "status": "processed"}
    finally:
        db.close()


@celery_app.task
def compute_yoy_curves_task(property_id: str) -> dict:
    """Compute YoY curves from prior_year data."""
    db = _SyncSession()
    try:
        count = compute_yoy_curves(db, property_id)
        db.commit()
        return {"property_id": property_id, "curves_stored": count}
    finally:
        db.close()
