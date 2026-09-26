import uuid
from decimal import Decimal
from datetime import date, datetime, timezone
from sqlalchemy import String, Numeric, Integer, Date, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.base import Base, TimestampMixin


class FinancialProfile(Base, TimestampMixin):
    __tablename__ = "financial_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)

    investable_capital: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False, default=Decimal("0.00"))
    monthly_contribution: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False, default=Decimal("0.00"))

    investment_horizon: Mapped[str] = mapped_column(String(50), nullable=False)
    primary_goal: Mapped[str] = mapped_column(String(100), nullable=False)

    experience_level: Mapped[str] = mapped_column(String(50), nullable=False)
    liquidity_requirement: Mapped[str] = mapped_column(String(50), nullable=False)

    risk_tolerance: Mapped[str | None] = mapped_column(String(50), nullable=True)
    risk_capacity: Mapped[str | None] = mapped_column(String(50), nullable=True)

    profile_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class FinancialProfileAssessment(Base):
    __tablename__ = "financial_profile_assessments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    financial_profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("financial_profiles.id", ondelete="CASCADE"), nullable=False)
    assessment_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    questions_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    answers_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    jev_results_json: Mapped[dict] = mapped_column(JSONB, nullable=False)

    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class Goal(Base, TimestampMixin):
    __tablename__ = "goals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)

    target_amount: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    priority: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
