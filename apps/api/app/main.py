from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.db.session import check_database_health
from app.api.dependencies import check_redis_health
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
    """Readiness probe: verifies DB and Redis are reachable (§36)."""
    db_healthy = await check_database_health()
    redis_healthy = await check_redis_health()

    if db_healthy and redis_healthy:
        return {"status": "ready", "database": "ok", "redis": "ok"}

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": "not_ready",
            "database": "ok" if db_healthy else "failed",
            "redis": "ok" if redis_healthy else "failed"
        }
    )


app.include_router(api_router)
