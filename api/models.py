import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from .database import Base


def _uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=_uuid)
    google_id = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    picture = Column(String, nullable=True)
    has_completed_onboarding = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    customers = relationship("Customer", back_populates="user")


class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = (
        UniqueConstraint("user_id", "slug", name="uq_customer_user_slug"),
    )

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)  # nullable for legacy/seed data
    name = Column(String, nullable=False)
    slug = Column(String, nullable=False)
    config_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="customers")
    calls = relationship("Call", back_populates="customer")


class Call(Base):
    __tablename__ = "calls"

    id = Column(String, primary_key=True, default=_uuid)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)
    gong_call_id = Column(String, nullable=True, unique=True)
    title = Column(String, nullable=False)
    date = Column(DateTime, nullable=False)
    duration_seconds = Column(Integer, nullable=True)
    participants = Column(JSONB, default=list)
    rep_name = Column(String, nullable=True)
    rep_email = Column(String, nullable=True)
    raw_transcript = Column(Text, nullable=False)
    status = Column(String, nullable=False, default="pending")  # pending, processing, chunked, failed
    error_message = Column(Text, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    customer = relationship("Customer", back_populates="calls")
    chunks = relationship("CallChunk", back_populates="call", cascade="all, delete-orphan")
    fields = relationship("CallField", back_populates="call", cascade="all, delete-orphan")
    summary = relationship("CallSummary", back_populates="call", uselist=False, cascade="all, delete-orphan")
    scores = relationship("CallScore", back_populates="call", cascade="all, delete-orphan")


class CallChunk(Base):
    __tablename__ = "call_chunks"

    id = Column(String, primary_key=True, default=_uuid)
    call_id = Column(String, ForeignKey("calls.id", ondelete="CASCADE"), nullable=False)
    level = Column(String, nullable=False)  # "topics", "insights", "quotes"
    content = Column(JSONB, nullable=False)
    timestamp_start = Column(String, nullable=True)
    timestamp_end = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    call = relationship("Call", back_populates="chunks")


class CallField(Base):
    __tablename__ = "call_fields"

    id = Column(String, primary_key=True, default=_uuid)
    call_id = Column(String, ForeignKey("calls.id", ondelete="CASCADE"), nullable=False)
    field_name = Column(String, nullable=False)
    field_value = Column(JSONB, nullable=False)
    field_type = Column(String, nullable=False)  # "enum", "text", "integer", "boolean", "list"

    call = relationship("Call", back_populates="fields")


class CallScore(Base):
    """Individual skill score for a call — one row per skill per call."""
    __tablename__ = "call_scores"

    id = Column(String, primary_key=True, default=_uuid)
    call_id = Column(String, ForeignKey("calls.id", ondelete="CASCADE"), nullable=False)
    skill_name = Column(String, nullable=False)
    skill_category = Column(String, nullable=False)  # discovery, middle_of_call, pricing, end_of_call, prospect_engagement, general
    score = Column(Integer, nullable=False)  # 1-5 rating
    evidence = Column(Text, nullable=True)  # quote or explanation from the call
    present = Column(Boolean, nullable=False, default=False)  # was this skill demonstrated?

    call = relationship("Call", back_populates="scores")


class CallSummary(Base):
    __tablename__ = "call_summaries"

    id = Column(String, primary_key=True, default=_uuid)
    call_id = Column(String, ForeignKey("calls.id", ondelete="CASCADE"), unique=True, nullable=False)
    overall_sentiment = Column(String, nullable=True)
    deal_likelihood = Column(Float, nullable=True)
    next_steps = Column(JSONB, default=list)
    follow_up_date = Column(String, nullable=True)
    summary_text = Column(Text, nullable=True)

    call = relationship("Call", back_populates="summary")
