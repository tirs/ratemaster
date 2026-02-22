"""Training jobs - fit ML model on features + outcomes, persist and register."""
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, Session

from app.celery_app import celery_app
from app.config import settings
from app.models.organization import Property
from app.services.dataset_builder import build_training_dataset
from app.services.model_registry import register_model
from app.services.ml_training import train_model, save_model

sync_engine = create_engine(
    settings.database_url.replace("+asyncpg", ""),
    echo=False,
)
SyncSession = sessionmaker(sync_engine, autocommit=False, autoflush=False)

MODELS_DIR = Path(__file__).resolve().parent.parent.parent / "models"


@celery_app.task(bind=True)
def run_training_job(self, property_id: str) -> dict:
    """
    Training job: build dataset from feature_store + outcomes,
    fit sklearn GradientBoostingRegressor, persist artifact, register version.
    """
    self.update_state(state="PROGRESS", meta={"step": "building_dataset"})

    db = SyncSession()
    try:
        dataset = build_training_dataset(db, property_id, min_samples=50)
        if len(dataset) < 50:
            return {
                "status": "insufficient_data",
                "samples": len(dataset),
                "required": 50,
            }

        self.update_state(state="PROGRESS", meta={"step": "training"})

        pipeline = train_model(dataset)
        version = f"v1.{datetime.now(timezone.utc).strftime('%Y%m%d%H%M')}"
        model_dir = MODELS_DIR / property_id
        model_dir.mkdir(parents=True, exist_ok=True)
        model_path = model_dir / f"engine_a_{version}.joblib"
        save_model(pipeline, str(model_path))

        reg = register_model(
            db,
            "engine_a_heuristic",
            version,
            property_id=property_id,
            metadata_={
                "type": "ml",
                "model_path": str(model_path),
                "trained_at": datetime.now(timezone.utc).isoformat(),
                "training_samples": len(dataset),
                "description": "GradientBoostingRegressor calibrated from outcomes",
            },
            set_active=True,
        )
        db.commit()

        return {
            "status": "completed",
            "model_version": reg.version,
            "training_samples": len(dataset),
        }
    finally:
        db.close()


@celery_app.task
def run_training_jobs_scheduled() -> dict:
    """
    Scheduled training: run training for all properties.
    Called daily via Celery beat.
    """
    db = SyncSession()
    try:
        result = db.execute(select(Property.id))
        property_ids = [r[0] for r in result.fetchall()]
        completed = 0
        for pid in property_ids:
            r = run_training_job.apply(args=[pid]).get()
            if isinstance(r, dict) and r.get("status") == "completed":
                completed += 1
        return {"completed": completed, "total": len(property_ids)}
    finally:
        db.close()
