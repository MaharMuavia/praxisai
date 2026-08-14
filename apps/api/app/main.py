import secrets
import uuid
from collections.abc import Awaitable, Callable

import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.responses import Response

from app.api import (
    auth,
    billing,
    credentials,
    governance,
    intake,
    internships_operations,
    internships_public,
    internships_student,
    internships_uploads,
    learning,
    notifications,
    offers,
    operations,
    projects,
    scope_control,
    talent,
    university,
    work,
    workspaces,
)
from app.config import get_settings
from app.db import SessionFactory
from app.domain.schemas import ErrorDetail, ErrorResponse
from app.readiness import assert_database_ready
from app.security.headers import apply_api_security_headers

settings = get_settings()
logger = structlog.get_logger()

app = FastAPI(
    title="PraxisAI API",
    version="0.1.0",
    docs_url="/docs" if settings.app_env != "production" else None,
    redoc_url=None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "X-CSRF-Token", "Idempotency-Key", "X-Correlation-ID"],
)


@app.middleware("http")
async def security_and_correlation(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    supplied = request.headers.get("X-Correlation-ID")
    try:
        request.state.correlation_id = uuid.UUID(supplied) if supplied else uuid.uuid4()
    except ValueError:
        request.state.correlation_id = uuid.uuid4()

    excluded = {
        "/api/v1/auth/session",
        "/api/v1/auth/local/session",
    }
    if request.method in {"POST", "PUT", "PATCH", "DELETE"} and request.url.path not in excluded:
        if request.cookies.get("praxis_session"):
            cookie_token = request.cookies.get("praxis_csrf", "")
            header_token = request.headers.get("X-CSRF-Token", "")
            if not cookie_token or not secrets.compare_digest(cookie_token, header_token):
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": {
                            "code": "csrf_failed",
                            "message": "CSRF token is missing or invalid",
                            "correlation_id": str(request.state.correlation_id),
                            "details": {},
                        }
                    },
                )
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = str(request.state.correlation_id)
    apply_api_security_headers(response, production=settings.app_env == "production")
    return response


@app.exception_handler(HTTPException)
async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
    correlation = getattr(request.state, "correlation_id", uuid.uuid4())
    detail: dict[str, object] = exc.detail if isinstance(exc.detail, dict) else {}
    payload = ErrorResponse(
        error=ErrorDetail(
            code=str(detail.get("code", f"http_{exc.status_code}")),
            message=str(detail.get("message", exc.detail)),
            correlation_id=correlation,
            details={key: value for key, value in detail.items() if key not in {"code", "message"}},
        )
    )
    return JSONResponse(status_code=exc.status_code, content=payload.model_dump(mode="json"))


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    correlation = getattr(request.state, "correlation_id", uuid.uuid4())
    errors = [
        {
            "type": error["type"],
            "loc": list(error["loc"]),
            "msg": error["msg"],
        }
        for error in exc.errors()
    ]
    payload = ErrorResponse(
        error=ErrorDetail(
            code="validation_error",
            message="Request validation failed",
            correlation_id=correlation,
            details={"errors": errors},
        )
    )
    return JSONResponse(status_code=422, content=payload.model_dump(mode="json"))


@app.exception_handler(Exception)
async def unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    correlation = getattr(request.state, "correlation_id", uuid.uuid4())
    logger.exception(
        "unhandled_request_error",
        correlation_id=str(correlation),
        method=request.method,
        path=request.url.path,
        error_type=type(exc).__name__,
    )
    payload = ErrorResponse(
        error=ErrorDetail(
            code="internal_error",
            message="An unexpected server error occurred",
            correlation_id=correlation,
        )
    )
    return JSONResponse(status_code=500, content=payload.model_dump(mode="json"))


@app.get("/health")
@app.get("/api/v1/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
@app.get("/api/v1/ready")
async def readiness() -> Response:
    try:
        await assert_database_ready(SessionFactory)
    except Exception as exc:
        logger.warning("readiness_check_failed", error_type=type(exc).__name__)
        return JSONResponse(status_code=503, content={"status": "not_ready"})
    return JSONResponse(content={"status": "ready"})


app.include_router(auth.router, prefix="/api/v1")
app.include_router(projects.router, prefix="/api/v1")
app.include_router(scope_control.router, prefix="/api/v1")
app.include_router(offers.router, prefix="/api/v1")
app.include_router(billing.router, prefix="/api/v1")
app.include_router(credentials.router, prefix="/api/v1")
app.include_router(operations.router, prefix="/api/v1")
app.include_router(work.router, prefix="/api/v1")
app.include_router(governance.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")
app.include_router(university.router, prefix="/api/v1")
app.include_router(workspaces.router, prefix="/api/v1")
app.include_router(learning.router, prefix="/api/v1")
app.include_router(talent.router, prefix="/api/v1")
app.include_router(intake.router, prefix="/api/v1")
app.include_router(internships_public.router, prefix="/api/v1")
app.include_router(internships_student.router, prefix="/api/v1")
app.include_router(internships_operations.router, prefix="/api/v1")
app.include_router(internships_uploads.router, prefix="/api/v1")
