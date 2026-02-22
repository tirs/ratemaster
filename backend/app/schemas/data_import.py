"""Data import schemas."""
from datetime import date
from pydantic import BaseModel, Field


class ColumnMappingSchema(BaseModel):
    """Column mapping for CSV import."""

    stay_date: str | None = Field(None, description="CSV column for stay_date")
    rooms_available: str | None = Field(None)
    total_rooms: str | None = Field(None)
    rooms_sold: str | None = Field(None)
    adr: str | None = Field(None)
    total_rate: str | None = Field(None)
    revenue: str | None = Field(None)


class DataImportRequest(BaseModel):
    """Data import request - multipart with file + mapping."""

    property_id: str = Field(..., description="Property to import for")
    snapshot_type: str = Field("current", pattern="^(current|prior_year)$")
    column_mapping: dict[str, str] = Field(
        default_factory=dict,
        description="Map logical field -> CSV header name",
    )


class DataSnapshotResponse(BaseModel):
    """Data snapshot response."""

    id: str
    property_id: str
    snapshot_date: str | None
    snapshot_type: str
    row_count: int
    data_health_score: int | None
    created_at: str
    recommended_fixes: list[str] | None = None
