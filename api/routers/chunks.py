"""Chunks router — search and query chunked call data."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, cast, func, String
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Call, CallChunk, CallField, CallSummary, Customer
from ..schemas import CallOut, ChunkOut, SearchRequest, SearchResult

router = APIRouter()


@router.get("/call/{call_id}", response_model=List[ChunkOut])
def get_chunks_for_call(
    call_id: str,
    level: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get all chunks for a specific call, optionally filtered by level."""
    query = db.query(CallChunk).filter(CallChunk.call_id == call_id)
    if level:
        query = query.filter(CallChunk.level == level)
    return query.all()


@router.post("/search", response_model=SearchResult)
def search_calls(body: SearchRequest, db: Session = Depends(get_db)):
    """Search calls by text query and/or field filters.

    Supports:
    - Full-text search across transcript content and chunk content
    - Field-based filtering (e.g., restaurant_type=fine_dining, pain_points contains "inventory_waste")
    - Customer filtering
    """
    query = db.query(Call)

    # Customer filter
    if body.customer_slug:
        customer = db.query(Customer).filter(Customer.slug == body.customer_slug).first()
        if customer:
            query = query.filter(Call.customer_id == customer.id)

    # Text search across transcript
    if body.query:
        query = query.filter(Call.raw_transcript.ilike(f"%{body.query}%"))

    # Field-based filters
    if body.filters:
        for field_name, field_value in body.filters.items():
            # Join CallField and filter
            query = query.filter(
                Call.id.in_(
                    db.query(CallField.call_id).filter(
                        and_(
                            CallField.field_name == field_name,
                            _field_value_matches(field_value),
                        )
                    )
                )
            )

    total = query.count()
    calls = query.offset(body.offset).limit(body.limit).all()

    return SearchResult(calls=calls, total=total)


@router.get("/search/quotes")
def search_quotes(
    q: str = Query(..., min_length=1),
    customer_slug: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """Search across all extracted quotes."""
    query = db.query(CallChunk).filter(
        CallChunk.level == "quotes",
        cast(CallChunk.content["quote"], String).ilike(f"%{q}%"),
    )

    if customer_slug:
        customer = db.query(Customer).filter(Customer.slug == customer_slug).first()
        if customer:
            call_ids = db.query(Call.id).filter(Call.customer_id == customer.id)
            query = query.filter(CallChunk.call_id.in_(call_ids))

    chunks = query.limit(limit).all()
    results = []
    for chunk in chunks:
        call = db.query(Call).filter(Call.id == chunk.call_id).first()
        results.append({
            "chunk": ChunkOut.model_validate(chunk),
            "call_title": call.title if call else "",
            "call_id": chunk.call_id,
            "call_date": call.date.isoformat() if call else "",
        })
    return results


def _field_value_matches(value: Any):
    """Build a JSONB match condition for field values.

    Handles:
    - Exact match for strings/numbers/booleans
    - Contains match for lists (e.g., pain_points contains "inventory_waste")
    """
    if isinstance(value, list):
        # Any item in the list matches
        conditions = []
        for item in value:
            conditions.append(
                cast(CallField.field_value, String).ilike(f"%{item}%")
            )
        return conditions[0] if len(conditions) == 1 else and_(*conditions)

    # Exact JSONB match
    return CallField.field_value == value
