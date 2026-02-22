"""Error handling - standard envelope for all non-2xx."""
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.schemas.errors import ErrorEnvelope, ValidationErrorDetail

# Map status codes to machine-readable error codes
HTTP_STATUS_TO_ERROR_CODE = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    409: "conflict",
}


def error_envelope_response(
    status_code: int,
    error: str,
    error_code: str | None = None,
    detail: list[ValidationErrorDetail] | None = None,
    request_id: str | None = None,
) -> JSONResponse:
    """Build JSON response with standard error envelope."""
    envelope = ErrorEnvelope(
        success=False,
        error=error,
        error_code=error_code,
        detail=detail,
        request_id=request_id,
    )
    return JSONResponse(
        status_code=status_code,
        content=envelope.model_dump(exclude_none=True),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Convert 422 validation errors to standard envelope."""
    detail = [
        ValidationErrorDetail(
            loc=[str(x) for x in e["loc"]],
            msg=e["msg"],
            type=e["type"],
        )
        for e in exc.errors()
    ]
    return error_envelope_response(
        status_code=422,
        error="Validation error",
        error_code="validation_error",
        detail=detail,
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Convert HTTPException (401, 403, 404, 400, 409, etc.) to standard envelope."""
    if isinstance(exc.detail, str):
        error_msg = exc.detail
    elif isinstance(exc.detail, list):
        error_msg = "Validation error" if exc.detail else "Error"
    else:
        error_msg = str(exc.detail) if exc.detail else "Error"
    error_code = HTTP_STATUS_TO_ERROR_CODE.get(
        exc.status_code, f"http_{exc.status_code}"
    )
    return error_envelope_response(
        status_code=exc.status_code,
        error=error_msg,
        error_code=error_code,
    )
