"""Engine run and recommendation schemas."""
from pydantic import BaseModel, Field


class RecommendationResponse(BaseModel):
    id: str
    stay_date: str
    suggested_bar: float | None
    current_bar: float | None
    delta_dollars: float | None
    delta_pct: float | None
    occupancy_projection: float | None
    occupancy_projection_low: float | None = None
    occupancy_projection_high: float | None = None
    confidence: int | None
    why_bullets: list[str] | None
    applied: bool


class EngineRunResponse(BaseModel):
    id: str
    property_id: str
    engine_type: str
    run_id: str
    status: str
    confidence: int | None
    created_at: str


class EngineRunDetailResponse(EngineRunResponse):
    recommendations: list[RecommendationResponse] | None = None
    calendar: list[dict] | None = None
