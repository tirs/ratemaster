"""Feature store - compute, store, and query features for engines."""
from datetime import date, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.data_import import DataSnapshot, DataSnapshotRow
from app.models.feature_store import FeatureStore
from app.models.market import MarketSnapshot


def compute_features(
    db: Session,
    property_id: str,
    run_id: str,
    stay_date: str,
    snapshot: DataSnapshot | None,
    rows: list,
    market_signal: float | None = None,
) -> dict[str, Any]:
    """
    Compute features for a stay_date from snapshot data and market.
    Used by engines and stored for training.
    """
    features: dict[str, Any] = {
        "stay_date": stay_date,
        "property_id": property_id,
        "run_id": run_id,
    }

    # Historical ADR / occupancy from rows
    row = next((r for r in rows if r.stay_date == stay_date), None)
    if row:
        features["historical_adr"] = float(row.adr) if row.adr else None
        features["rooms_available"] = row.rooms_available
        features["rooms_sold"] = row.rooms_sold
        if row.rooms_available and row.rooms_sold is not None:
            features["historical_occupancy"] = (
                row.rooms_sold / row.rooms_available * 100
                if row.rooms_available else None
            )
        else:
            features["historical_occupancy"] = None
    else:
        adr_vals = [float(r.adr) for r in rows if r.adr]
        features["historical_adr"] = sum(adr_vals) / len(adr_vals) if adr_vals else None
        features["historical_occupancy"] = None
        features["rooms_available"] = None
        features["rooms_sold"] = None

    features["data_health_score"] = snapshot.data_health_score if snapshot else None
    features["market_signal"] = market_signal
    features["row_count"] = len(rows)

    return features


def store_features(
    db: Session,
    property_id: str,
    run_id: str,
    stay_date: str,
    features: dict[str, Any],
) -> FeatureStore:
    """Store computed features in feature_store."""
    entry = FeatureStore(
        property_id=property_id,
        run_id=run_id,
        stay_date=stay_date,
        features=features,
    )
    db.add(entry)
    db.flush()
    return entry


def get_latest_market_signal(
    db: Session, property_id: str, stay_date: str | None = None
) -> float | None:
    """Get latest compset_avg for property from market_snapshots."""
    snap, _ = get_latest_market_snapshot(db, property_id, stay_date)
    return float(snap.compset_avg) if snap and snap.compset_avg else None


def get_latest_market_snapshot(
    db: Session, property_id: str, stay_date: str | None = None
) -> tuple[MarketSnapshot | None, float | None]:
    """
    Get market snapshot for property. When stay_date given, prefer snapshot
    with matching stay_date; else latest by snapshot_at.
    Returns (snapshot, compset_avg) for reproducibility and linkage to runs.
    """
    q = select(MarketSnapshot).where(MarketSnapshot.property_id == property_id)
    if stay_date:
        # Prefer per-stay-date snapshot, then fall back to latest overall
        q_match = q.where(MarketSnapshot.stay_date == stay_date)
        result = db.execute(
            q_match.order_by(MarketSnapshot.snapshot_at.desc()).limit(1)
        )
        snap = result.scalar_one_or_none()
        if snap:
            val = float(snap.compset_avg) if snap.compset_avg else None
            return snap, val
    result = db.execute(
        q.order_by(MarketSnapshot.snapshot_at.desc()).limit(1)
    )
    snap = result.scalar_one_or_none()
    val = float(snap.compset_avg) if snap and snap.compset_avg else None
    return snap, val


def get_features_for_training(
    db: Session,
    property_id: str,
    limit: int = 10000,
) -> list[dict]:
    """Fetch features for training dataset builder."""
    result = db.execute(
        select(FeatureStore)
        .where(FeatureStore.property_id == property_id)
        .order_by(FeatureStore.created_at.desc())
        .limit(limit)
    )
    return [r.features for r in result.scalars().all()]
