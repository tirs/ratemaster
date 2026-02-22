"""Organization and property schemas."""
from datetime import datetime
from pydantic import BaseModel, Field


class OrganizationCreate(BaseModel):
    """Create organization request."""

    name: str = Field(..., min_length=1, max_length=255)


class OrganizationResponse(BaseModel):
    """Organization response."""

    id: str
    name: str
    created_at: datetime
    logo_url: str | None = None

    class Config:
        from_attributes = True


class PropertyCreate(BaseModel):
    """Create property request."""

    name: str = Field(..., min_length=1, max_length=255)
    organization_id: str = Field(..., description="Parent organization ID")


class PropertyResponse(BaseModel):
    """Property response."""

    id: str
    name: str
    organization_id: str
    created_at: datetime

    class Config:
        from_attributes = True
