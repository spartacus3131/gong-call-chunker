from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


# --- Customer ---
class CustomerOut(BaseModel):
    id: str
    name: str
    slug: str
    config_path: str
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Call ---
class CallCreate(BaseModel):
    customer_slug: str
    title: str
    date: datetime
    duration_seconds: Optional[int] = None
    participants: List[str] = []
    rep_name: Optional[str] = None
    rep_email: Optional[str] = None
    raw_transcript: str
    gong_call_id: Optional[str] = None


class CallOut(BaseModel):
    id: str
    customer_id: str
    gong_call_id: Optional[str]
    title: str
    date: datetime
    duration_seconds: Optional[int]
    participants: List[str]
    rep_name: Optional[str] = None
    rep_email: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    processed_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class ScoreOut(BaseModel):
    id: str
    skill_name: str
    skill_category: str
    score: int
    evidence: Optional[str]
    present: bool

    model_config = {"from_attributes": True}


class CallDetail(CallOut):
    raw_transcript: str
    chunks: List["ChunkOut"] = []
    fields: List["FieldOut"] = []
    summary: Optional["SummaryOut"] = None
    scores: List["ScoreOut"] = []


# --- Chunks ---
class ChunkOut(BaseModel):
    id: str
    level: str
    content: Dict[str, Any]
    timestamp_start: Optional[str]
    timestamp_end: Optional[str]

    model_config = {"from_attributes": True}


# --- Fields ---
class FieldOut(BaseModel):
    id: str
    field_name: str
    field_value: Any
    field_type: str

    model_config = {"from_attributes": True}


# --- Summary ---
class SummaryOut(BaseModel):
    overall_sentiment: Optional[str]
    deal_likelihood: Optional[float]
    next_steps: List[str]
    follow_up_date: Optional[str]
    summary_text: Optional[str]

    model_config = {"from_attributes": True}


# --- Search ---
class SearchRequest(BaseModel):
    query: Optional[str] = None
    customer_slug: Optional[str] = None
    filters: Dict[str, Any] = {}  # field_name -> value
    limit: int = 50
    offset: int = 0


class SearchResult(BaseModel):
    calls: List[CallOut]
    total: int


# --- Analytics ---
class FieldDistribution(BaseModel):
    field_name: str
    values: Dict[str, int]


class AnalyticsResponse(BaseModel):
    total_calls: int
    total_chunked: int
    field_distributions: List[FieldDistribution]


# --- Schema ---
class SchemaFieldDef(BaseModel):
    name: str
    type: str
    description: Optional[str] = None
    options: Optional[List[str]] = None
    examples: Optional[List[str]] = None


class CustomerSchema(BaseModel):
    customer: str
    display_name: str
    industry: str
    fields: List[SchemaFieldDef]
    chunk_levels: List[Dict[str, Any]]
    call_summary: List[str]


# --- Scorecard Analytics ---
class SkillAverage(BaseModel):
    skill_name: str
    skill_category: str
    avg_score: float
    times_present: int
    total_calls: int


class ScorecardOverview(BaseModel):
    skill_averages: List[SkillAverage]
    total_scored_calls: int
    categories: List[Dict[str, str]]


# --- Gong Sync ---
class GongSyncRequest(BaseModel):
    customer_slug: str
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
