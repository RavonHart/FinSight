import uuid
from decimal import Decimal
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict


class ResearchProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    research_type: str = Field("equity", description="equity, macro, industry, thematic")


class ResearchProjectResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: Optional[str] = None
    research_type: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResearchRunCreate(BaseModel):
    question: str = Field(..., min_length=3, description="E.g. 'Research NVIDIA'")
    idempotency_key: Optional[str] = Field(None, max_length=128, description="Client-supplied idempotency key (§45)")


class ResearchTaskResponse(BaseModel):
    id: uuid.UUID
    research_run_id: uuid.UUID
    task_type: str
    title: str
    status: str
    assigned_agent: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class SourceResponse(BaseModel):
    id: uuid.UUID
    source_type: str
    title: str
    url: Optional[str] = None
    publisher: Optional[str] = None
    published_at: Optional[datetime] = None
    retrieved_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EvidenceResponse(BaseModel):
    id: uuid.UUID
    research_run_id: uuid.UUID
    source_id: uuid.UUID
    claim: str
    evidence_text: str
    relevance_score: Optional[Decimal] = None
    source: Optional[SourceResponse] = None

    model_config = ConfigDict(from_attributes=True)


class ClaimResponse(BaseModel):
    id: uuid.UUID
    research_run_id: uuid.UUID
    claim_text: str
    claim_type: str
    confidence: Optional[Decimal] = None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JevEvaluationResponse(BaseModel):
    id: uuid.UUID
    research_run_id: Optional[uuid.UUID] = None
    question_id: str
    result_type: str
    choice_value: Optional[str] = None
    score_value: Optional[Decimal] = None
    probabilities_json: Optional[Dict[str, float]] = None
    confidence: Decimal
    model_version: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResearchRunResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    user_id: uuid.UUID
    question: str
    status: str
    idempotency_key: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    research_iterations: int
    tool_calls_used: int
    model_metadata_json: Optional[Dict[str, Any]] = None
    usage_metadata_json: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
