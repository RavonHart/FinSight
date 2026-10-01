import uuid
from typing import List
from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.dependencies import get_current_active_user
from app.db.models.users import User
from app.domains.goals.schemas import GoalCreateRequest, GoalUpdateRequest, GoalResponse
from app.domains.goals.service import (
    list_user_goals,
    create_user_goal,
    update_user_goal,
    delete_user_goal,
)

goals_router = APIRouter(prefix="/goals", tags=["Financial Goals"])


@goals_router.get("", response_model=List[GoalResponse])
async def get_goals_endpoint(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists all goals configured by the authenticated user (§22)."""
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    return await list_user_goals(db, user_uuid)


@goals_router.post("", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
async def create_goal_endpoint(
    request: GoalCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Creates a new financial goal scoped to the authenticated user (§22)."""
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    return await create_user_goal(db, user_uuid, request)


@goals_router.put("/{goal_id}", response_model=GoalResponse)
async def update_goal_endpoint(
    goal_id: uuid.UUID,
    request: GoalUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Updates a financial goal ensuring user ownership (§22)."""
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    return await update_user_goal(db, user_uuid, goal_id, request)


@goals_router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal_endpoint(
    goal_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Deletes a financial goal ensuring user ownership (§22)."""
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    await delete_user_goal(db, user_uuid, goal_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
