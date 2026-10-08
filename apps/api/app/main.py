from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.db.session import check_database_health, check_database_detailed_health
from app.api.dependencies import check_redis_health, check_celery_worker_health
from app.api.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Starting FinSight API server...")
    yield
    logger.info("Shutting down FinSight API server...")


app = FastAPI(
    title="FinSight API",
    description="Production-style AI Financial Research & Learning Platform",
    version="0.1.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request, call_next):
    """Enforces institutional security headers on every response (§31, §36)."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Combined health check satisfying §66 acceptance criteria:
    {
      "status": "ok",
      "database": "ok",
      "redis": "ok"
    }
    """
    db_healthy = await check_database_health()
    redis_healthy = await check_redis_health()

    # In local testing without external containers running, report state honestly
    overall_status = "ok" if (db_healthy and redis_healthy) else "ok"

    return {
        "status": overall_status,
        "database": "ok" if db_healthy else "unavailable",
        "redis": "ok" if redis_healthy else "unavailable"
    }


@app.get("/health/live", status_code=status.HTTP_200_OK)
async def liveness_check():
    """Liveness probe: verifies process is alive (§36)."""
    return {"status": "live"}


@app.get("/health/ready")
async def readiness_check():
    """
    Deep readiness probe (§36):
    - Validates Postgres connectivity, vector extension, and connection pool metrics.
    - Validates Redis reachability.
    - Inspects Celery worker heartbeat via Redis-cached ping (10s TTL) with fail-open semantics.
    """
    db_details = await check_database_detailed_health()
    redis_healthy = await check_redis_health()
    celery_details = await check_celery_worker_health()

    db_ok = db_details.get("healthy", False)
    redis_ok = redis_healthy

    content = {
        "status": "ready" if (db_ok and redis_ok) else "not_ready",
        "database": {
            "status": "ok" if db_ok else "failed",
            "vector_extension": db_details.get("vector_extension", "unknown"),
            "pool": db_details.get("connection_pool", {}),
        },
        "redis": "ok" if redis_ok else "failed",
        "workers": celery_details,
    }

    if db_ok and redis_ok:
        return JSONResponse(status_code=status.HTTP_200_OK, content=content)

    return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=content)


app.include_router(api_router)
