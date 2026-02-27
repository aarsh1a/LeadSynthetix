"""LoanApplication model."""

from __future__ import annotations

import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class LoanApplication(Base):
    __tablename__ = "loan_applications"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    industry: Mapped[str] = mapped_column(String(255), nullable=False)
    requested_amount: Mapped[float] = mapped_column(nullable=False)
    extracted_financials: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="Pending"
    )  # Pending / Approved / Rejected
    workflow_state: Mapped[str] = mapped_column(
        String(20), nullable=False, default="INGESTED"
    )  # INGESTED | INITIAL_REVIEW | DEBATE | CONSENSUS | FINALIZED
    final_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    compliance_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    agent_memos: Mapped[list["AgentMemo"]] = relationship(
        "AgentMemo", back_populates="loan_application"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", back_populates="loan_application"
    )
