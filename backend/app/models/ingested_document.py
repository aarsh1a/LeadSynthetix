"""IngestedDocument model - stores raw PDF text and extracted data."""

from __future__ import annotations

import uuid
from datetime import datetime
from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class IngestedDocument(Base):
    __tablename__ = "ingested_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    extracted_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )