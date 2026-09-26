from fastapi import APIRouter

api_router = APIRouter(prefix="/api/v1")


@api_router.get("/status")
async def get_status():
    return {
        "service": "FinSight API",
        "version": "0.1.0",
        "api_prefix": "/api/v1",
        "features": {
            "auth": "ready",
            "profiles": "ready",
            "portfolios": "ready",
            "research": "ready",
            "simulations": "ready",
            "learning": "ready",
            "watchlists": "ready"
        }
    }
