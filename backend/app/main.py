"""RateMaster FastAPI application."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

logger = logging.getLogger(__name__)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.errors import (
    error_envelope_response,
    http_exception_handler,
    validation_exception_handler,
)
from app.api.routes import (
    auth,
    organizations,
    data_import,
    jobs,
    engines,
    contribution,
    exports,
    alerts,
    property_settings,
    property_events,
    billing,
    outcomes,
    manual_data,
    portfolio,
    market,
    org_members,
    model_registry,
)
from app.database import init_db

responses = {
    401: {"model": "ErrorEnvelope", "description": "Unauthorized"},
    403: {"model": "ErrorEnvelope", "description": "Forbidden"},
    404: {"model": "ErrorEnvelope", "description": "Not found"},
    422: {"model": "ErrorEnvelope", "description": "Validation error"},
    500: {"model": "ErrorEnvelope", "description": "Internal server error"},
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    await init_db()
    yield


app = FastAPI(
    title="RateMaster API",
    description="Revenue/pricing recommendation SaaS for hotels",
    version="0.1.0",
    lifespan=lifespan,
    openapi_url="/openapi.json",
    docs_url="/docs",
)

# Rate limiting (configurable via RATE_LIMIT_PER_MINUTE env)
from slowapi import Limiter
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.config import settings as app_settings

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{app_settings.rate_limit_per_minute}/minute"],
)
app.state.limiter = limiter


async def rate_limit_handler(request, exc: RateLimitExceeded):
    return error_envelope_response(
        status_code=429,
        error="Rate limit exceeded. Try again later.",
        error_code="rate_limit_exceeded",
    )


app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:30000",
        "http://127.0.0.1:30000",
        "https://ratemaster.flowtasks.io",
        "http://ratemaster.flowtasks.io",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Standard error envelope for all non-2xx
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)


@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    """Catch-all for unhandled exceptions."""
    logger.exception("Unhandled exception: %s", exc)
    return error_envelope_response(
        status_code=500,
        error="Internal server error",
        error_code="internal_error",
    )


app.include_router(auth.router, prefix="/api/v1")
app.include_router(organizations.router, prefix="/api/v1")
app.include_router(data_import.router, prefix="/api/v1")
app.include_router(jobs.router, prefix="/api/v1")
app.include_router(engines.router, prefix="/api/v1")
app.include_router(contribution.router, prefix="/api/v1")
app.include_router(exports.router, prefix="/api/v1")
app.include_router(alerts.router, prefix="/api/v1")
app.include_router(property_settings.router, prefix="/api/v1")
app.include_router(property_events.router, prefix="/api/v1")
app.include_router(billing.router, prefix="/api/v1")
app.include_router(outcomes.router, prefix="/api/v1")
app.include_router(manual_data.router, prefix="/api/v1")
app.include_router(portfolio.router, prefix="/api/v1")
app.include_router(market.router, prefix="/api/v1")
app.include_router(org_members.router, prefix="/api/v1")
app.include_router(model_registry.router, prefix="/api/v1")


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "ok"}
