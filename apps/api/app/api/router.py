from fastapi import APIRouter
from app.domains.users.router import auth_router, admin_router

api_router = APIRouter(prefix="/api/v1")

# Mount authentication & admin routers
api_router.include_router(auth_router)
api_router.include_router(admin_router)


@api_router.get("/status")
async def get_status():
    return {
        "service": "FinSight API",
        "version": "0.1.0",
        "api_prefix": "/api/v1",
        "features": {
            "auth": "active",
            "profiles": "ready",
            "portfolios": "ready",
            "research": "ready",
            "simulations": "ready",
            "learning": "ready",
            "watchlists": "ready"
        }
    }
