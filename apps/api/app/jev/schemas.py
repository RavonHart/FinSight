from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict


class JevResultType(str, Enum):
    CHOICE = "choice"
    SCORE = "score"
    NOUL = "noul"


class ConfidenceRoutingAction(str, Enum):
    CONTINUE = "continue"
    GATHER_MORE_EVIDENCE = "gather_more_evidence"
    REQUEST_CLARIFICATION = "request_clarification"
    MARK_INSUFFICIENT = "mark_insufficient"
    REFUSE_ADVISORY = "refuse_advisory"


class JevQuestionDefinition(BaseModel):
    id: str
    description: str
    result_type: JevResultType
    options: List[str] = Field(default_factory=list)
    version: str = "1.0.0"
    high_threshold: float = 0.80
    medium_threshold: float = 0.50

    model_config = ConfigDict(frozen=True)


class JevEvaluationRequest(BaseModel):
    question_id: str
    input_state: Dict[str, Any]


class JevEvaluationResult(BaseModel):
    question_id: str
    result_type: JevResultType
    choice_value: Optional[str] = None
    score_value: Optional[float] = None
    probabilities: Optional[Dict[str, float]] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    model_version: str = "jev-v1"
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class RoutingDecision(BaseModel):
    action: ConfidenceRoutingAction
    confidence: float
    high_threshold: float
    medium_threshold: float
    reason: str
    follow_up_prompt: Optional[str] = None
