import uuid
from decimal import Decimal
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class GoalCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    type: str = Field(..., min_length=1, max_length=50, description="E.g. retirement, real_estate, emergency_fund, education")
    target_amount: Optional[Decimal] = Field(None, ge=0)
    target_date: Optional[date] = None
    priority: int = Field(1, ge=1, le=10)


class GoalUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    type: Optional[str] = Field(None, min_length=1, max_length=50)
    target_amount: Optional[Decimal] = Field(None, ge=0)
    target_date: Optional[date] = None
    priority: Optional[int] = Field(None, ge=1, le=10)


class GoalResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    type: str
    target_amount: Optional[Decimal] = None
    target_date: Optional[date] = None
    priority: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
