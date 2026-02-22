"""ML training - fit sklearn model on features + outcomes, persist artifact."""
import os
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# Feature columns used for training and prediction (must match)
FEATURE_COLS = [
    "historical_adr",
    "historical_occupancy",
    "data_health_score",
    "market_signal",
    "row_count",
    "month",
    "day_of_week",
]


def _features_to_vector(features: dict) -> np.ndarray:
    """Convert features dict to fixed-size vector for model input."""
    # Parse stay_date for month, day_of_week
    month, day_of_week = 6, 2  # defaults
    stay_date = features.get("stay_date")
    if stay_date:
        try:
            from datetime import datetime
            dt = datetime.strptime(stay_date, "%Y-%m-%d")
            month = dt.month
            day_of_week = dt.weekday()
        except (ValueError, TypeError):
            pass

    adr = features.get("historical_adr")
    occ = features.get("historical_occupancy")
    health = features.get("data_health_score")
    market = features.get("market_signal")
    row_count = features.get("row_count")

    return np.array([[
        float(adr) if adr is not None else 100.0,
        float(occ) if occ is not None else 70.0,
        float(health) if health is not None else 50.0,
        float(market) if market is not None else 0.0,
        int(row_count) if row_count is not None else 30,
        month,
        day_of_week,
    ]], dtype=np.float64)


def build_X_y(dataset: list[dict]) -> tuple[np.ndarray, np.ndarray]:
    """Build X matrix and y vector from training dataset."""
    X_list = []
    y_list = []
    for row in dataset:
        vec = _features_to_vector(row["features"])
        X_list.append(vec[0])
        y_list.append(row["target_adr"])
    return np.array(X_list), np.array(y_list)


def train_model(dataset: list[dict]) -> Pipeline:
    """
    Fit GradientBoostingRegressor on dataset.
    Returns fitted pipeline (scaler + model).
    """
    X, y = build_X_y(dataset)
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("model", GradientBoostingRegressor(
            n_estimators=50,
            max_depth=4,
            learning_rate=0.1,
            random_state=42,
        )),
    ])
    pipeline.fit(X, y)
    return pipeline


def save_model(pipeline: Pipeline, path: str) -> None:
    """Persist model to disk."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, path)


def load_model(path: str) -> Pipeline | None:
    """Load model from disk. Returns None if file missing."""
    if not path or not os.path.isfile(path):
        return None
    return joblib.load(path)


def features_to_vector(features: dict) -> np.ndarray:
    """Public API for predictor - convert features to vector."""
    return _features_to_vector(features)
