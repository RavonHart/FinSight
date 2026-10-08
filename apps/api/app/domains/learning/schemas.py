import uuid
from decimal import Decimal
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict


class QuizQuestionView(BaseModel):
    id: str
    question: str
    options: List[str]


class QuizQuestionFeedback(BaseModel):
    id: str
    question: str
    options: List[str]
    selected_index: int
    correct_index: int
    is_correct: bool
    explanation: str


class QuizSubmissionRequest(BaseModel):
    answers: Dict[str, int] = Field(..., description="Mapping of question ID to chosen option index (0-based)")


class QuizAttemptResponse(BaseModel):
    id: uuid.UUID
    module_id: uuid.UUID
    score: Decimal
    passed: bool
    correct_count: int
    total_questions: int
    feedback: List[QuizQuestionFeedback]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LearningProgressSchema(BaseModel):
    module_id: uuid.UUID
    progress: Decimal
    completed: bool
    last_accessed: datetime

    model_config = ConfigDict(from_attributes=True)


class LearningModuleSummaryResponse(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    category: str
    difficulty: str
    summary: str
    progress: Decimal = Decimal("0.00")
    completed: bool = False
    last_accessed: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class LearningModuleDetailResponse(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    category: str
    difficulty: str
    summary: str
    concept: str
    example: str
    eli5: str
    quant: str
    visual_type: str
    key_takeaways: List[str]
    quiz_questions: List[QuizQuestionView]
    progress: Decimal = Decimal("0.00")
    completed: bool = False
    last_accessed: Optional[datetime] = None
    best_score: Optional[Decimal] = None
    latest_score: Optional[Decimal] = None

    model_config = ConfigDict(from_attributes=True)


class CategoryProgressItem(BaseModel):
    total_modules: int
    completed_modules: int
    average_progress: Decimal


class LearningSummaryResponse(BaseModel):
    total_modules: int
    completed_modules: int
    overall_completion_pct: Decimal
    average_quiz_score: Optional[Decimal] = None
    category_breakdown: Dict[str, CategoryProgressItem]


class AITutorRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=1000, description="User question about financial concept")
    mode: str = Field(
        "clarify",
        description="Tutoring style: 'clarify' (standard), 'eli5' (simple analogy), 'quant' (mathematical rigor), 'portfolio_context' (connect to user's assets/profile)"
    )


class AITutorResponse(BaseModel):
    module_slug: str
    query: str
    mode: str
    explanation: str
    concepts_referenced: List[str]
    suggested_followups: List[str]
    profile_context_applied: bool
    disclaimer: str
