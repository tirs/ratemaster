"""Feature store service tests."""
import pytest
from app.services.feature_store import compute_features


def test_compute_features_no_snapshot():
    """Features computed without snapshot use defaults."""
    features = compute_features(
        db=None,
        property_id="prop1",
        run_id="run1",
        stay_date="2024-01-15",
        snapshot=None,
        rows=[],
        market_signal=95.0,
    )
    assert features["property_id"] == "prop1"
    assert features["run_id"] == "run1"
    assert features["stay_date"] == "2024-01-15"
    assert features["historical_adr"] is None
    assert features["market_signal"] == 95.0
    assert features["data_health_score"] is None
    assert features["row_count"] == 0


def test_compute_features_with_row():
    """Features include historical_adr when row exists."""
    class MockRow:
        stay_date = "2024-01-15"
        adr = 120.0
        rooms_available = 100
        rooms_sold = 80

    class MockSnapshot:
        data_health_score = 85

    features = compute_features(
        db=None,
        property_id="prop1",
        run_id="run1",
        stay_date="2024-01-15",
        snapshot=MockSnapshot(),
        rows=[MockRow()],
        market_signal=None,
    )
    assert features["historical_adr"] == 120.0
    assert features["historical_occupancy"] == 80.0
    assert features["data_health_score"] == 85
    assert features["row_count"] == 1
