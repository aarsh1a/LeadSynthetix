"""Initial schema: loan_applications, agent_memos, audit_logs

Revision ID: 001
Revises:
Create Date: 2025-02-27

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "loan_applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("industry", sa.String(255), nullable=False),
        sa.Column("requested_amount", sa.Float(), nullable=False),
        sa.Column("extracted_financials", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="Pending"),
        sa.Column("final_score", sa.Float(), nullable=True),
        sa.Column("compliance_flag", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "agent_memos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("loan_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_type", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["loan_id"], ["loan_applications.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_agent_memos_loan_id"), "agent_memos", ["loan_id"], unique=False)

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("loan_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["loan_id"], ["loan_applications.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_audit_logs_loan_id"), "audit_logs", ["loan_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_audit_logs_loan_id"), table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index(op.f("ix_agent_memos_loan_id"), table_name="agent_memos")
    op.drop_table("agent_memos")
    op.drop_table("loan_applications")
