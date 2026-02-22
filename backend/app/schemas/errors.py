"""Standard error envelope for ALL non-2xx responses (including 422 validation)."""
from pydantic import BaseModel, Field


class ValidationErrorDetail(BaseModel):
    """Single validation error detail."""

    loc: list[str] = Field(..., description="Path to the field")
    msg: str = Field(..., description="Error message")
    type: str = Field(..., description="Error type")


class ErrorEnvelope(BaseModel):
    """Standard error envelope - used for all non-2xx responses."""

    success: bool = Field(False, description="Always false for errors")
    error: str = Field(..., description="Human-readable error message")
    error_code: str | None = Field(None, description="Machine-readable error code")
    detail: list[ValidationErrorDetail] | None = Field(
        None, description="Validation errors (422) or additional context"
    )
    request_id: str | None = Field(None, description="Request trace ID")
