from fastapi import APIRouter
from app.domains.users.router import auth_router, admin_router
from app.domains.profiles.router import profile_router
from app.domains.goals.router import goals_router
from app.domains.portfolios.router import portfolio_router
from app.domains.research.router import research_router
from app.domains.simulations.router import simulation_router
from app.domains.learning.router import learning_router

api_router = APIRouter(prefix="/api/v1")

# Mount domain routers
api_router.include_router(auth_router)
api_router.include_router(admin_router)
api_router.include_router(profile_router)
api_router.include_router(goals_router)
api_router.include_router(portfolio_router)
api_router.include_router(research_router)
api_router.include_router(simulation_router)
api_router.include_router(learning_router)


@api_router.get("/status")
async def get_status():
    return {
        "service": "FinSight API",
        "version": "0.1.0",
        "api_prefix": "/api/v1",
        "features": {
            "auth": "active",
            "profiles": "active",
            "goals": "active",
            "portfolios": "active",
            "research": "active",
            "simulations": "active",
            "learning": "active",
            "watchlists": "ready"
        }
    }
