import uuid
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy import String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.base import Base


class JevEvaluation(Base):
    __tablename__ = "jev_evaluations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    research_run_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("research_runs.id", ondelete="CASCADE"), nullable=True)
    financial_profile_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("financial_profiles.id", ondelete="CASCADE"), nullable=True)

    question_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)

    input_state_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    result_type: Mapped[str] = mapped_column(String(50), nullable=False)  # choice, score, distribution

    choice_value: Mapped[str | None] = mapped_column(String(100), nullable=True)
    score_value: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)

    probabilities_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)

    model_version: Mapped[str] = mapped_column(String(50), default="jev-v1", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
