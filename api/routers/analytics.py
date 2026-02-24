"""Analytics router — aggregate queries across chunked calls."""

import json
from collections import Counter
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Call, CallField, CallSummary, Customer
from ..schemas import AnalyticsResponse, FieldDistribution

router = APIRouter()


@router.get("/overview", response_model=AnalyticsResponse)
def analytics_overview(
    customer_slug: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """High-level analytics: total calls, field distributions."""
    call_query = db.query(Call)
    if customer_slug:
        customer = db.query(Customer).filter(Customer.slug == customer_slug).first()
        if customer:
            call_query = call_query.filter(Call.customer_id == customer.id)

    total = call_query.count()
    chunked = call_query.filter(Call.processed_at.isnot(None)).count()

    # Get field distributions
    call_ids = [c.id for c in call_query.all()]
    fields = db.query(CallField).filter(CallField.call_id.in_(call_ids)).all() if call_ids else []

    distributions: Dict[str, Counter] = {}
    for field in fields:
        name = field.field_name
        if name not in distributions:
            distributions[name] = Counter()

        value = field.field_value
        if isinstance(value, list):
            for item in value:
                distributions[name][str(item)] += 1
        elif isinstance(value, bool):
            distributions[name][str(value).lower()] += 1
        elif value is not None:
            distributions[name][str(value)] += 1

    field_dists = [
        FieldDistribution(field_name=name, values=dict(counter.most_common(20)))
        for name, counter in sorted(distributions.items())
    ]

    return AnalyticsResponse(
        total_calls=total,
        total_chunked=chunked,
        field_distributions=field_dists,
    )


@router.get("/pain-points")
def pain_point_analysis(
    customer_slug: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Frequency analysis of pain points across calls."""
    return _field_frequency(db, "pain_points", customer_slug)


@router.get("/competitors")
def competitor_analysis(
    customer_slug: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Frequency analysis of competitor mentions across calls."""
    return _field_frequency(db, "competitor_mentions", customer_slug)


@router.get("/deal-likelihood")
def deal_likelihood_distribution(
    customer_slug: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Distribution of deal likelihood scores."""
    query = db.query(CallSummary)
    if customer_slug:
        customer = db.query(Customer).filter(Customer.slug == customer_slug).first()
        if customer:
            call_ids = db.query(Call.id).filter(Call.customer_id == customer.id)
            query = query.filter(CallSummary.call_id.in_(call_ids))

    summaries = query.filter(CallSummary.deal_likelihood.isnot(None)).all()
    scores = [s.deal_likelihood for s in summaries]

    if not scores:
        return {"average": None, "distribution": {}, "total": 0}

    # Bucket into ranges
    buckets = {"1-3 (Low)": 0, "4-6 (Medium)": 0, "7-8 (High)": 0, "9-10 (Very High)": 0}
    for s in scores:
        if s <= 3:
            buckets["1-3 (Low)"] += 1
        elif s <= 6:
            buckets["4-6 (Medium)"] += 1
        elif s <= 8:
            buckets["7-8 (High)"] += 1
        else:
            buckets["9-10 (Very High)"] += 1

    return {
        "average": round(sum(scores) / len(scores), 1),
        "distribution": buckets,
        "total": len(scores),
    }


@router.get("/sentiment")
def sentiment_distribution(
    customer_slug: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Distribution of overall call sentiments."""
    query = db.query(CallSummary)
    if customer_slug:
        customer = db.query(Customer).filter(Customer.slug == customer_slug).first()
        if customer:
            call_ids = db.query(Call.id).filter(Call.customer_id == customer.id)
            query = query.filter(CallSummary.call_id.in_(call_ids))

    summaries = query.filter(CallSummary.overall_sentiment.isnot(None)).all()
    counter = Counter(s.overall_sentiment for s in summaries)
    return {"distribution": dict(counter), "total": len(summaries)}


def _field_frequency(
    db: Session, field_name: str, customer_slug: Optional[str] = None
) -> Dict[str, Any]:
    """Get frequency counts for a list-type field."""
    query = db.query(CallField).filter(CallField.field_name == field_name)
    if customer_slug:
        customer = db.query(Customer).filter(Customer.slug == customer_slug).first()
        if customer:
            call_ids = db.query(Call.id).filter(Call.customer_id == customer.id)
            query = query.filter(CallField.call_id.in_(call_ids))

    fields = query.all()
    counter: Counter = Counter()
    for field in fields:
        value = field.field_value
        if isinstance(value, list):
            for item in value:
                counter[str(item)] += 1
        elif value is not None:
            counter[str(value)] += 1

    return {
        "field": field_name,
        "counts": dict(counter.most_common(30)),
        "total_calls": len(fields),
    }
