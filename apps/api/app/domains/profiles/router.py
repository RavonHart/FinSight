import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.dependencies import get_current_active_user
from app.db.models.users import User
from app.jev.client import JevClient
from app.domains.profiles.schemas import (
    QuestionnaireItem,
    ProfileAnswersSubmission,
    FinancialProfileResponse,
    ProfileAssessmentResponse,
    ProfileWithAssessmentResponse,
    ProfileUpdateRequest,
)
from app.domains.profiles.service import (
    get_questionnaire,
    submit_profile_assessment,
    get_user_profile,
    get_latest_profile_assessment,
    update_user_profile,
)

profile_router = APIRouter(prefix="/profile", tags=["Financial Profile"])


@profile_router.get("/questionnaire", response_model=List[QuestionnaireItem])
async def get_questionnaire_endpoint():
    """Returns the standardized structured financial questionnaire (§12)."""
    return get_questionnaire()


@profile_router.post("/assessment", response_model=ProfileWithAssessmentResponse, status_code=status.HTTP_201_CREATED)
async def submit_assessment_endpoint(
    answers: ProfileAnswersSubmission,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Evaluates questionnaire submissions via Jev / TypeSafe AI System One (§12, §13).
    Executes confidence routing (§14), constructs/versions the profile, and returns structured dimensions.
    """
    client = JevClient()
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    return await submit_profile_assessment(db, user_uuid, answers, client)


@profile_router.get("/assessment", response_model=ProfileAssessmentResponse)
async def get_assessment_endpoint(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves the latest versioned assessment and Jev dimension breakdown."""
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    assessment = await get_latest_profile_assessment(db, user_uuid)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No financial profile assessment found for this user."
        )
    return assessment


@profile_router.get("", response_model=FinancialProfileResponse)
async def get_profile_endpoint(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns the user's active financial profile (§22)."""
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    profile = await get_user_profile(db, user_uuid)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Financial profile not found. Please complete the onboarding questionnaire."
        )
    return profile


@profile_router.put("", response_model=FinancialProfileResponse)
async def update_profile_endpoint(
    update_data: ProfileUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Updates attributes of the user's active financial profile (§22)."""
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    return await update_user_profile(db, user_uuid, update_data)
