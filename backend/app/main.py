# backend/app/main.py
import os
import sys
import uuid
import logging

from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from app.core.limiter import limiter
from app.routes import auth
from app.routes import list as list_routes
from app.routes import item as item_routes
from app.routes import share as share_routes
from app.routes import account as account_routes
from app.routes import verification as verification_routes
from app.routes import users as users_routes
from app.database.database import init_indexes, get_database

log = logging.getLogger("app")

# ── Env validation (fail fast in production) ──────────────────────────────────
def _validate_env() -> None:
    if os.getenv("ENV", "dev").lower() != "prod":
        return
    errors = []
    if os.getenv("JWT_SECRET", "CHANGE_ME_DEV_SECRET") == "CHANGE_ME_DEV_SECRET":
        errors.append("JWT_SECRET must be changed from the default in production")
    if not os.getenv("SENDGRID_API_KEY"):
        errors.append("SENDGRID_API_KEY is required in production")
    if not os.getenv("EMAIL_FROM"):
        errors.append("EMAIL_FROM is required in production")
    if not os.getenv("ALLOWED_ORIGINS"):
        errors.append("ALLOWED_ORIGINS is required in production")
    if errors:
        for msg in errors:
            print(f"[CONFIG ERROR] {msg}", file=sys.stderr)
        sys.exit(1)

_validate_env()

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Listalicious API",
    version="1.0.0",
    description="Backend for the Listalicious grocery list app.",
    docs_url="/v1/docs",
    redoc_url="/v1/redoc",
    openapi_url="/v1/openapi.json",
)

# ── Rate limiter ──────────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ──────────────────────────────────────────────────────────────────────
_allowed_origins = [
    o.strip()
    for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Security headers ──────────────────────────────────────────────────────────
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "0"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# ── Request ID ────────────────────────────────────────────────────────────────
class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

app.add_middleware(RequestIDMiddleware)

# ── Global exception handler (never leak stack traces) ────────────────────────
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    log.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

# ── Startup ───────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    await init_indexes()

# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check(db=Depends(get_database)):
    try:
        await db.command("ping")
        return {"status": "ok", "db": "connected"}
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "db": "unreachable"},
        )

@app.get("/", tags=["Health"])
async def read_root():
    return {"message": "Listalicious backend is alive!"}

# ── Routers (all under /v1) ───────────────────────────────────────────────────
V1 = "/v1"
app.include_router(auth.router,                prefix=V1)
app.include_router(list_routes.router,         prefix=V1, tags=["Grocery Lists"])
app.include_router(item_routes.router,         prefix=V1)
app.include_router(share_routes.router,        prefix=V1)
app.include_router(account_routes.router,      prefix=V1)
app.include_router(verification_routes.router, prefix=V1)
app.include_router(users_routes.router,        prefix=V1)
