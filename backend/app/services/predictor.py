"""
Predictor interface - stable internal API used by Engine A and Engine B.
Supports heuristic fallback and ML models from training.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.services.ml_training import load_model, features_to_vector


@dataclass
class PredictionInput:
    """Input features for predictor."""
    property_id: str
    stay_date: str
    historical_adr: float | None
    historical_occupancy: float | None
    data_health_score: int | None
    market_signal: float | None
    features: dict[str, Any]
    market_snapshot_at: datetime | None = None  # For signal freshness


@dataclass
class PredictionOutput:
    """Output from predictor."""
    suggested_bar: float
    confidence: int
    why_drivers: list[str]


def _signal_freshness_bonus(snapshot_at: datetime | None) -> int:
    """0-15 bonus based on market snapshot age. Fresher = higher confidence."""
    if not snapshot_at:
        return 0
    now = datetime.now(timezone.utc)
    snap_utc = snapshot_at if snapshot_at.tzinfo else snapshot_at.replace(tzinfo=timezone.utc)
    age_hours = (now - snap_utc).total_seconds() / 3600
    if age_hours < 24:
        return 15
    if age_hours < 168:  # 7 days
        return 10
    if age_hours < 720:  # 30 days
        return 5
    return 0


def _model_uncertainty_penalty(is_heuristic: bool, model_trained_at: str | None) -> int:
    """Penalty for model uncertainty. Heuristic = higher uncertainty; stale ML = some penalty."""
    if is_heuristic:
        return 15
    if not model_trained_at:
        return 0
    try:
        from datetime import datetime
        trained = datetime.fromisoformat(model_trained_at.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        days_old = (now - trained).days
        if days_old > 90:
            return 10
        if days_old > 30:
            return 5
    except (ValueError, TypeError):
        pass
    return 0


def _compute_confidence(
    data_health: int,
    is_heuristic: bool,
    model_trained_at: str | None,
    market_snapshot_at: datetime | None,
) -> int:
    """Confidence from data health + model uncertainty + signal freshness."""
    base = (data_health or 50) + 30
    penalty = _model_uncertainty_penalty(is_heuristic, model_trained_at)
    bonus = _signal_freshness_bonus(market_snapshot_at)
    return max(0, min(100, base - penalty + bonus))


class PredictorInterface(ABC):
    """Abstract predictor - Engine A and B use this."""

    @abstractmethod
    def predict(self, inp: PredictionInput) -> PredictionOutput:
        """Produce rate suggestion with confidence and reasoning."""
        pass


class HeuristicPredictor(PredictorInterface):
    """Heuristic predictor - 2% lift from historical ADR. Fallback when no ML model."""

    def predict(self, inp: PredictionInput) -> PredictionOutput:
        base = inp.historical_adr or 100.0
        suggested = round(base * 1.02, 2)
        confidence = _compute_confidence(
            inp.data_health_score or 50,
            is_heuristic=True,
            model_trained_at=None,
            market_snapshot_at=inp.market_snapshot_at,
        )
        drivers = ["historical_adr", "data_health"]
        if inp.market_signal:
            drivers.append("market_signal")
        return PredictionOutput(
            suggested_bar=suggested,
            confidence=confidence,
            why_drivers=drivers,
        )


class MLPredictor(PredictorInterface):
    """ML predictor - uses trained sklearn model. Falls back to heuristic on error."""

    def __init__(self, model_path: str, metadata: dict | None = None):
        self.model_path = model_path
        self._pipeline = load_model(model_path)
        self._heuristic = HeuristicPredictor()
        self._trained_at = (metadata or {}).get("trained_at") if metadata else None

    def predict(self, inp: PredictionInput) -> PredictionOutput:
        if self._pipeline is None:
            return self._heuristic.predict(inp)
        try:
            X = features_to_vector(inp.features)
            pred = self._pipeline.predict(X)
            suggested = round(float(pred[0]), 2)
            confidence = _compute_confidence(
                inp.data_health_score or 50,
                is_heuristic=False,
                model_trained_at=self._trained_at,
                market_snapshot_at=inp.market_snapshot_at,
            )
            return PredictionOutput(
                suggested_bar=max(1.0, suggested),
                confidence=confidence,
                why_drivers=["ml_model", "historical_adr", "data_health"],
            )
        except Exception:
            return self._heuristic.predict(inp)


def get_predictor_for_property(db, property_id: str | None, model_name: str = "engine_a_heuristic") -> PredictorInterface:
    """
    Get predictor for property: ML if trained model exists, else heuristic.
    """
    from app.services.model_registry import get_active_model

    reg = get_active_model(db, model_name, property_id=property_id)
    if reg and reg.metadata_.get("type") == "ml":
        path = reg.metadata_.get("model_path")
        if path:
            return MLPredictor(path, metadata=reg.metadata_)
    return HeuristicPredictor()
