"""Predictor interface tests."""
import pytest
from unittest.mock import MagicMock, patch

from app.services.predictor import (
    HeuristicPredictor,
    MLPredictor,
    PredictionInput,
    PredictionOutput,
    get_predictor_for_property,
)


def test_heuristic_predictor_basic():
    """Heuristic predictor returns 2% lift from historical ADR."""
    predictor = HeuristicPredictor()
    inp = PredictionInput(
        property_id="p1",
        stay_date="2024-01-15",
        historical_adr=100.0,
        historical_occupancy=75.0,
        data_health_score=80,
        market_signal=None,
        features={},
    )
    out = predictor.predict(inp)
    assert out.suggested_bar == 102.0  # 2% lift
    assert 0 <= out.confidence <= 100
    assert "historical_adr" in out.why_drivers


def test_heuristic_predictor_no_adr():
    """Uses 100 when no historical ADR."""
    predictor = HeuristicPredictor()
    inp = PredictionInput(
        property_id="p1",
        stay_date="2024-01-15",
        historical_adr=None,
        historical_occupancy=None,
        data_health_score=50,
        market_signal=None,
        features={},
    )
    out = predictor.predict(inp)
    assert out.suggested_bar == 102.0  # 100 * 1.02


def test_heuristic_predictor_with_market():
    """Market signal included in drivers."""
    predictor = HeuristicPredictor()
    inp = PredictionInput(
        property_id="p1",
        stay_date="2024-01-15",
        historical_adr=100.0,
        historical_occupancy=None,
        data_health_score=60,
        market_signal=95.0,
        features={},
    )
    out = predictor.predict(inp)
    assert "market_signal" in out.why_drivers


def test_get_predictor_returns_heuristic_when_no_ml_model():
    """get_predictor_for_property returns HeuristicPredictor when no ML model registered."""
    with patch(
        "app.services.model_registry.get_active_model",
        return_value=None,
    ):
        db = MagicMock()
        predictor = get_predictor_for_property(db, "prop-1")
    assert isinstance(predictor, HeuristicPredictor)


def test_ml_predictor_falls_back_to_heuristic_when_model_missing():
    """MLPredictor falls back to heuristic when model file does not exist."""
    predictor = MLPredictor("/nonexistent/path/model.joblib")
    inp = PredictionInput(
        property_id="p1",
        stay_date="2024-01-15",
        historical_adr=100.0,
        historical_occupancy=None,
        data_health_score=50,
        market_signal=None,
        features={"historical_adr": 100, "stay_date": "2024-01-15"},
    )
    out = predictor.predict(inp)
    assert out.suggested_bar == 102.0  # heuristic fallback
