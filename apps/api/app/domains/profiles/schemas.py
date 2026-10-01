import uuid
from decimal import Decimal
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict


class QuestionnaireOption(BaseModel):
    value: str
    label: str
    description: Optional[str] = None


class QuestionnaireItem(BaseModel):
    id: str
    title: str
    category: str
    description: str
    why_it_matters: str
    question_type: str  # numeric, select
    options: Optional[List[QuestionnaireOption]] = None
    default_value: Optional[Any] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None


class ProfileAnswersSubmission(BaseModel):
    investable_capital: Decimal = Field(..., ge=0, description="Available capital to invest (USD)")
    monthly_contribution: Decimal = Field(..., ge=0, description="Anticipated monthly additions (USD)")
    investment_horizon: str = Field(..., description="'short' (<2y), 'medium' (3-7y), or 'long' (>7y)")
    primary_goal: str = Field(..., description="E.g., wealth_growth, retirement, capital_preservation, major_purchase")
    experience_level: str = Field(..., description="'beginner', 'intermediate', or 'advanced'")
    liquidity_requirement: str = Field(..., description="'immediate', 'moderate', or 'low'")
    reaction_to_market_drop: str = Field(..., description="'panic_sell', 'hold_steady', or 'buy_more'")
    emergency_fund_coverage: str = Field(..., description="'less_than_3_months', '3_to_6_months', or 'more_than_6_months'")
    income_stability: str = Field(..., description="'unstable', 'moderate', or 'very_stable'")
    clarification_response: Optional[str] = None
    is_conflicting_test: Optional[bool] = False  # Used for testing low-confidence routing edge-cases


class JevDimensionBreakdown(BaseModel):
    question_id: str
    dimension_name: str
    judgment: str
    probabilities: Dict[str, float]
    confidence: float
    description: str


class FinancialProfileResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    investable_capital: Decimal
    monthly_contribution: Decimal
    investment_horizon: str
    primary_goal: str
    experience_level: str
    liquidity_requirement: str
    risk_tolerance: Optional[str] = None
    risk_capacity: Optional[str] = None
    profile_version: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProfileAssessmentResponse(BaseModel):
    id: uuid.UUID
    financial_profile_id: uuid.UUID
    assessment_version: int
    confidence: float
    routing_action: str
    routing_reason: str
    follow_up_prompt: Optional[str] = None
    jev_dimensions: List[JevDimensionBreakdown]
    answers_summary: Dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProfileWithAssessmentResponse(BaseModel):
    profile: FinancialProfileResponse
    assessment: ProfileAssessmentResponse


class ProfileUpdateRequest(BaseModel):
    investable_capital: Optional[Decimal] = Field(None, ge=0)
    monthly_contribution: Optional[Decimal] = Field(None, ge=0)
    investment_horizon: Optional[str] = None
    primary_goal: Optional[str] = None
    experience_level: Optional[str] = None
    liquidity_requirement: Optional[str] = None
    risk_tolerance: Optional[str] = None
    risk_capacity: Optional[str] = None
