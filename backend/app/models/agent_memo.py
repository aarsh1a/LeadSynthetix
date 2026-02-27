"""AgentMemo model."""

from __future__ import annotations

import uuid
from datetime import datetime
from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class AgentMemo(Base):
    __tablename__ = "agent_memos"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    loan_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("loan_applications.id", ondelete="CASCADE"),
        nullable=False,
    )
    agent_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # Sales / Risk / Compliance / Moderator
    content: Mapped[str] = mapped_column(Text, nullable=False)
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    loan_application: Mapped["LoanApplication"] = relationship(
        "LoanApplication", back_populates="agent_memos"
    )
