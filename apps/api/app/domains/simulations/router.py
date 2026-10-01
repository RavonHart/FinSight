import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.dependencies import get_current_active_user
from app.db.models.users import User
from app.domains.simulations.schemas import (
    SimulationRequest,
    SimulationRunResponse,
)
from app.domains.simulations.service import (
    execute_and_persist_simulation,
    get_simulation_run,
    list_simulation_runs,
)

simulation_router = APIRouter(prefix="/simulations", tags=["Simulations"])


@simulation_router.post(
    "",
    response_model=SimulationRunResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Run and persist investment simulation",
)
async def create_simulation(
    data: SimulationRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Executes a deterministic multi-scenario forward investment simulation (§20, §28).
    Pins engine_version='financial-engine-v1' and stores reproducible results.
    """
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    return await execute_and_persist_simulation(db, user_uuid, data)


@simulation_router.get(
    "/{simulation_id}",
    response_model=SimulationRunResponse,
    summary="Get simulation run details",
)
async def get_simulation(
    simulation_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves a previously computed simulation run (§11, §30)."""
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    return await get_simulation_run(db, user_uuid, simulation_id)


@simulation_router.get(
    "",
    response_model=List[SimulationRunResponse],
    summary="List simulation runs",
)
async def list_simulations(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists historical simulation runs for authenticated user."""
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    return await list_simulation_runs(db, user_uuid)
