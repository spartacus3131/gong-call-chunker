"""Chunks router — search and query chunked call data."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, cast, String
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import Call, CallChunk, CallField, Customer, User
from ..schemas import CallOut, ChunkOut, SearchRequest, SearchResult

router = APIRouter()


def _user_customer_ids(db: Session, user: Optional[User]):
    """Get subquery of customer IDs belonging to the current user."""
    if not user:
        return db.query(Customer.id)
    return db.query(Customer.id).filter(Customer.user_id == user.id)


@router.get("/call/{call_id}", response_model=List[ChunkOut])
def get_chunks_for_call(
    call_id: str,
    level: Optional[str] = None,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    """Get all chunks for a specific call, optionally filtered by level."""
    # Verify call belongs to user
    call = db.query(Call).filter(
        Call.id == call_id,
        Call.customer_id.in_(_user_customer_ids(db, user)),
    ).first()
    if not call:
        return []

    query = db.query(CallChunk).filter(CallChunk.call_id == call_id)
    if level:
        query = query.filter(CallChunk.level == level)
    return query.all()


@router.post("/search", response_model=SearchResult)
def search_calls(
    body: SearchRequest,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    """Search calls by text query and/or field filters."""
    query = db.query(Call).filter(
        Call.customer_id.in_(_user_customer_ids(db, user))
    )

    if body.customer_slug:
        cust_query = db.query(Customer).filter(Customer.slug == body.customer_slug)
        if user:
            cust_query = cust_query.filter(Customer.user_id == user.id)
        customer = cust_query.first()
        if customer:
            query = query.filter(Call.customer_id == customer.id)

    if body.query:
        query = query.filter(Call.raw_transcript.ilike(f"%{body.query}%"))

    if body.filters:
        for field_name, field_value in body.filters.items():
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
    user: Optional[User] = Depends(get_current_user),
):
    """Search across all extracted quotes."""
    user_call_ids = db.query(Call.id).filter(
        Call.customer_id.in_(_user_customer_ids(db, user))
    )

    query = db.query(CallChunk).filter(
        CallChunk.level == "quotes",
        CallChunk.call_id.in_(user_call_ids),
        cast(CallChunk.content["quote"], String).ilike(f"%{q}%"),
    )

    if customer_slug:
        cust_query = db.query(Customer).filter(Customer.slug == customer_slug)
        if user:
            cust_query = cust_query.filter(Customer.user_id == user.id)
        customer = cust_query.first()
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
    """Build a JSONB match condition for field values."""
    if isinstance(value, list):
        conditions = []
        for item in value:
            conditions.append(
                cast(CallField.field_value, String).ilike(f"%{item}%")
            )
        return conditions[0] if len(conditions) == 1 else and_(*conditions)
    return CallField.field_value == value
