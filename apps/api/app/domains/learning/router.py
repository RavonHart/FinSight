import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.dependencies import get_current_active_user
from app.db.models.users import User
from app.domains.learning.schemas import (
    LearningModuleSummaryResponse,
    LearningModuleDetailResponse,
    QuizSubmissionRequest,
    QuizAttemptResponse,
    LearningSummaryResponse,
    AITutorRequest,
    AITutorResponse,
)
from app.domains.learning.service import (
    list_learning_modules,
    get_learning_module_detail,
    submit_quiz_attempt,
    get_quiz_attempts_history,
    get_user_learning_summary,
    ask_ai_tutor,
)

learning_router = APIRouter(prefix="/learning", tags=["Learning"])


@learning_router.get(
    "",
    response_model=List[LearningModuleSummaryResponse],
    summary="List learning modules with user progress",
)
async def list_modules(
    category: Optional[str] = Query(None, description="Filter by category (e.g. Basics, Risk, Portfolio)"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty (beginner, intermediate, advanced)"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns curated financial education modules across the 8 curriculum categories (§22, §29)
    with the current user's progress and completion status attached.
    """
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    return await list_learning_modules(db, user_uuid, category=category, difficulty=difficulty)


@learning_router.get(
    "/progress",
    response_model=LearningSummaryResponse,
    summary="Get user overall learning progress",
)
async def get_progress_summary(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Computes overall learning metrics, completed modules, average quiz score,
    and category-specific progress for the authenticated user (§22, §29).
    """
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    return await get_user_learning_summary(db, user_uuid)


@learning_router.get(
    "/{slug_or_id}",
    response_model=LearningModuleDetailResponse,
    summary="Get learning module details and concept materials",
)
async def get_module_detail(
    slug_or_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieves full lesson content (Concept, Example, ELI5, Quant, Visual Type)
    and sanitized quiz questions. Automatically tracks initial progress (§22, §29).
    """
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    return await get_learning_module_detail(db, user_uuid, slug_or_id)


@learning_router.post(
    "/{slug_or_id}/quiz",
    response_model=QuizAttemptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit quiz answers and evaluate score",
)
async def submit_quiz(
    slug_or_id: str,
    submission: QuizSubmissionRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Grades submitted quiz answers using deterministic Decimal arithmetic.
    Persists quiz attempt, provides question-by-question feedback with explanations,
    and marks module as completed if passing score (>= 70%) is achieved (§22, §29).
    """
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    return await submit_quiz_attempt(db, user_uuid, slug_or_id, submission.answers)


@learning_router.get(
    "/{slug_or_id}/quiz-history",
    response_model=List[QuizAttemptResponse],
    summary="Get previous quiz attempts for module",
)
async def get_quiz_history(
    slug_or_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves all previous quiz attempts and scores for the specified module (§11, §22)."""
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    return await get_quiz_attempts_history(db, user_uuid, slug_or_id)


@learning_router.post(
    "/{slug_or_id}/tutor",
    response_model=AITutorResponse,
    summary="Ask AI Financial Tutor a question about the module",
)
async def ask_tutor(
    slug_or_id: str,
    data: AITutorRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Interacts with the AI Financial Tutor grounded in the module's core curriculum,
    with pedagogical explanations and personalized profile context (§18, §29, §32).
    """
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    return await ask_ai_tutor(db, user_uuid, slug_or_id, data.query, data.mode)
