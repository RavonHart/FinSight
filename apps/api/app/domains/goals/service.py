import uuid
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.profiles import Goal
from app.db.models.audit import AuditLog
from app.domains.goals.schemas import GoalCreateRequest, GoalUpdateRequest, GoalResponse


async def list_user_goals(db: AsyncSession, user_id: uuid.UUID) -> List[GoalResponse]:
    """Lists all goals belonging to authenticated user, ordered by priority."""
    result = await db.execute(
        select(Goal).where(Goal.user_id == user_id).order_by(Goal.priority.asc(), Goal.created_at.asc())
    )
    goals = result.scalars().all()
    return [GoalResponse.model_validate(g) for g in goals]


async def create_user_goal(db: AsyncSession, user_id: uuid.UUID, request: GoalCreateRequest) -> GoalResponse:
    """Creates a new goal for the authenticated user and records audit log."""
    goal = Goal(
        id=uuid.uuid4(),
        user_id=user_id,
        name=request.name.strip(),
        type=request.type.strip(),
        target_amount=request.target_amount,
        target_date=request.target_date,
        priority=request.priority,
    )
    db.add(goal)

    audit = AuditLog(
        id=uuid.uuid4(),
        user_id=user_id,
        action="goal_created",
        resource_type="goal",
        resource_id=goal.id,
        metadata_json={"goal_name": goal.name, "type": goal.type}
    )
    db.add(audit)

    await db.commit()
    await db.refresh(goal)
    return GoalResponse.model_validate(goal)


async def update_user_goal(
    db: AsyncSession,
    user_id: uuid.UUID,
    goal_id: uuid.UUID,
    request: GoalUpdateRequest
) -> GoalResponse:
    """Updates an existing goal ensuring ownership and RLS isolation."""
    result = await db.execute(
        select(Goal).where(Goal.id == goal_id, Goal.user_id == user_id)
    )
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found or access denied"
        )

    for field, val in request.model_dump(exclude_unset=True).items():
        setattr(goal, field, val)

    await db.commit()
    await db.refresh(goal)
    return GoalResponse.model_validate(goal)


async def delete_user_goal(db: AsyncSession, user_id: uuid.UUID, goal_id: uuid.UUID) -> None:
    """Deletes an existing goal ensuring ownership."""
    result = await db.execute(
        select(Goal).where(Goal.id == goal_id, Goal.user_id == user_id)
    )
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found or access denied"
        )

    await db.delete(goal)
    await db.commit()
