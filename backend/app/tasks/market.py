"""Market data refresh tasks."""
from datetime import datetime, timezone

from sqlalchemy import create_engine, select, update
from sqlalchemy.orm import sessionmaker, Session

from app.celery_app import celery_app
from app.config import settings
from app.models.organization import Property
from app.services.market_adapter import ManualEntryAdapter

sync_engine = create_engine(
    settings.database_url.replace("+asyncpg", ""),
    echo=False,
)
SyncSession = sessionmaker(sync_engine, autocommit=False, autoflush=False)


def _get_adapter_for_property(property_id: str, db: Session):
    """Get market adapter for property. Extend to support per-property adapter config."""
    return ManualEntryAdapter()


def _should_refresh_property(prop: Property, now: datetime) -> bool:
    """Adaptive cadence: use property override or global; skip if refreshed recently."""
    minutes = prop.market_refresh_minutes if prop.market_refresh_minutes is not None else settings.market_refresh_minutes
    minutes = max(5, min(60, minutes))
    last = prop.last_market_refresh_at
    if last is None:
        return True
    last_utc = last if last.tzinfo else last.replace(tzinfo=timezone.utc)
    return (now - last_utc).total_seconds() >= minutes * 60


@celery_app.task
def refresh_market_signals(property_id: str) -> dict:
    """
    Refresh market rate signals for property.
    1. fetch_and_store: adapter may fetch from external API and store (e.g. third-party).
    2. fetch: get latest from market_snapshots.
    3. Returns status for Engine A trigger.
    """
    db = SyncSession()
    try:
        adapter = _get_adapter_for_property(property_id, db)
        adapter.fetch_and_store(property_id, db)
        db.commit()
        snap = adapter.fetch(property_id, db)
        if snap:
            return {
                "property_id": property_id,
                "status": "ok",
                "compset_avg": snap.compset_avg,
                "source": snap.source,
            }
        return {"property_id": property_id, "status": "no_data", "signals": []}
    finally:
        db.close()


@celery_app.task
def refresh_all_market_signals() -> dict:
    """
    Refresh market signals for all properties.
    Scheduled via Celery beat (e.g. every 5 min). Uses adaptive cadence:
    - Per-property market_refresh_minutes overrides global
    - Skips properties refreshed within their cadence window
    - fetch_and_store runs first (third-party adapters fetch+store; manual is no-op)
    - Triggers Engine A re-runs for properties with market data
    """
    from app.tasks.engine import run_engine_a

    db = SyncSession()
    try:
        result = db.execute(select(Property))
        properties = result.scalars().all()
        now = datetime.now(timezone.utc)
        refreshed = 0
        for prop in properties:
            if not _should_refresh_property(prop, now):
                continue
            r = refresh_market_signals(prop.id)
            if r.get("status") == "ok":
                refreshed += 1
                db.execute(
                    update(Property)
                    .where(Property.id == prop.id)
                    .values(last_market_refresh_at=now)
                )
                db.commit()
                run_engine_a.delay(prop.id)
        return {"refreshed": refreshed, "total": len(properties)}
    finally:
        db.close()
