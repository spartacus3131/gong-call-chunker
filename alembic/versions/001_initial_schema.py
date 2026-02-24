"""Initial schema with User model and all tables.

Revision ID: 001
Revises:
Create Date: 2026-02-24
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table(
        "users",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("google_id", sa.String(), unique=True, nullable=False),
        sa.Column("email", sa.String(), unique=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("picture", sa.String(), nullable=True),
        sa.Column("has_completed_onboarding", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    # Customers table
    op.create_table(
        "customers",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("config_path", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("user_id", "slug", name="uq_customer_user_slug"),
    )

    # Calls table
    op.create_table(
        "calls",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("customer_id", sa.String(), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("gong_call_id", sa.String(), unique=True, nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("date", sa.DateTime(), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("participants", JSONB(), nullable=True),
        sa.Column("raw_transcript", sa.Text(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    # Call chunks table
    op.create_table(
        "call_chunks",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("call_id", sa.String(), sa.ForeignKey("calls.id", ondelete="CASCADE"), nullable=False),
        sa.Column("level", sa.String(), nullable=False),
        sa.Column("content", JSONB(), nullable=False),
        sa.Column("timestamp_start", sa.String(), nullable=True),
        sa.Column("timestamp_end", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    # Call fields table
    op.create_table(
        "call_fields",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("call_id", sa.String(), sa.ForeignKey("calls.id", ondelete="CASCADE"), nullable=False),
        sa.Column("field_name", sa.String(), nullable=False),
        sa.Column("field_value", JSONB(), nullable=False),
        sa.Column("field_type", sa.String(), nullable=False),
    )

    # Call summaries table
    op.create_table(
        "call_summaries",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("call_id", sa.String(), sa.ForeignKey("calls.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("overall_sentiment", sa.String(), nullable=True),
        sa.Column("deal_likelihood", sa.Float(), nullable=True),
        sa.Column("next_steps", JSONB(), nullable=True),
        sa.Column("follow_up_date", sa.String(), nullable=True),
        sa.Column("summary_text", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("call_summaries")
    op.drop_table("call_fields")
    op.drop_table("call_chunks")
    op.drop_table("calls")
    op.drop_table("customers")
    op.drop_table("users")
