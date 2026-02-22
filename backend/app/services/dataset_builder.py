"""Training dataset builder - features + outcomes for model training."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.feature_store import FeatureStore
from app.models.market import Outcome


def build_training_dataset(
    db: Session,
    property_id: str,
    min_samples: int = 100,
    limit: int = 10000,
) -> list[dict]:
    """
    Build training dataset by joining features with outcomes.
    Returns list of {features, target} for model training.
    """
    features_result = db.execute(
        select(FeatureStore)
        .where(FeatureStore.property_id == property_id)
        .order_by(FeatureStore.created_at.desc())
        .limit(limit)
    )
    feature_rows = features_result.scalars().all()

    outcomes_result = db.execute(
        select(Outcome)
        .where(Outcome.property_id == property_id)
    )
    outcomes = {o.stay_date: o for o in outcomes_result.scalars().all()}

    dataset = []
    for fs in feature_rows:
        outcome = outcomes.get(fs.stay_date)
        if not outcome or outcome.actual_adr is None:
            continue
        dataset.append({
            "features": fs.features,
            "target_adr": float(outcome.actual_adr),
            "target_occupancy": float(outcome.actual_occupancy) if outcome.actual_occupancy else None,
            "stay_date": fs.stay_date,
        })

    if len(dataset) < min_samples:
        return []
    return dataset
