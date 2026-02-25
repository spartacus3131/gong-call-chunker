"""Analytics router — aggregate queries across chunked calls."""

from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy import func, case
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import Call, CallField, CallScore, CallSummary, Customer, User
from ..schemas import AnalyticsResponse, FieldDistribution, ScorecardOverview, SkillAverage
from ..templates import SCORECARD_CATEGORIES

router = APIRouter()


def _user_call_query(
    db: Session,
    user: Optional[User],
    customer_slug: Optional[str] = None,
    rep_name: Optional[str] = None,
):
    """Build a base Call query scoped to the current user, optional customer, and optional rep."""
    query = db.query(Call)

    if user:
        user_customer_ids = db.query(Customer.id).filter(Customer.user_id == user.id)
        query = query.filter(Call.customer_id.in_(user_customer_ids))

    if customer_slug:
        cust_query = db.query(Customer).filter(Customer.slug == customer_slug)
        if user:
            cust_query = cust_query.filter(Customer.user_id == user.id)
        customer = cust_query.first()
        if customer:
            query = query.filter(Call.customer_id == customer.id)

    if rep_name:
        query = query.filter(Call.rep_name == rep_name)

    return query


def _call_id_subquery(
    db: Session,
    user: Optional[User],
    customer_slug: Optional[str] = None,
    rep_name: Optional[str] = None,
    processed_only: bool = False,
):
    """Return a subquery of call IDs (stays in SQL, no Python round-trip)."""
    q = db.query(Call.id)

    if user:
        user_customer_ids = db.query(Customer.id).filter(Customer.user_id == user.id)
        q = q.filter(Call.customer_id.in_(user_customer_ids))

    if customer_slug:
        cust_query = db.query(Customer).filter(Customer.slug == customer_slug)
        if user:
            cust_query = cust_query.filter(Customer.user_id == user.id)
        customer = cust_query.first()
        if customer:
            q = q.filter(Call.customer_id == customer.id)

    if rep_name:
        q = q.filter(Call.rep_name == rep_name)

    if processed_only:
        q = q.filter(Call.processed_at.isnot(None))

    return q.subquery()


@router.get("/reps")
def list_reps(
    customer_slug: Optional[str] = None,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    """List distinct rep names for the current user's calls."""
    query = _user_call_query(db, user, customer_slug)
    reps = (
        query.filter(Call.rep_name.isnot(None))
        .with_entities(Call.rep_name)
        .distinct()
        .order_by(Call.rep_name)
        .all()
    )
    return [r[0] for r in reps]


@router.get("/overview", response_model=AnalyticsResponse)
def analytics_overview(
    customer_slug: Optional[str] = None,
    rep_name: Optional[str] = None,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    """High-level analytics: total calls, field distributions."""
    call_query = _user_call_query(db, user, customer_slug, rep_name)

    total = call_query.count()
    chunked = call_query.filter(Call.processed_at.isnot(None)).count()

    call_ids_sq = _call_id_subquery(db, user, customer_slug, rep_name)
    fields = db.query(CallField).filter(CallField.call_id.in_(db.query(call_ids_sq))).all()

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
    rep_name: Optional[str] = None,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    return _field_frequency(db, "pain_points", user, customer_slug, rep_name)


@router.get("/competitors")
def competitor_analysis(
    customer_slug: Optional[str] = None,
    rep_name: Optional[str] = None,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    return _field_frequency(db, "competitor_mentions", user, customer_slug, rep_name)


@router.get("/deal-likelihood")
def deal_likelihood_distribution(
    customer_slug: Optional[str] = None,
    rep_name: Optional[str] = None,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    call_ids_sq = _call_id_subquery(db, user, customer_slug, rep_name)

    summaries = db.query(CallSummary).filter(
        CallSummary.call_id.in_(db.query(call_ids_sq)),
        CallSummary.deal_likelihood.isnot(None),
    ).all()
    scores = [s.deal_likelihood for s in summaries]

    if not scores:
        return {"average": None, "distribution": {}, "total": 0}

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
    rep_name: Optional[str] = None,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    call_ids_sq = _call_id_subquery(db, user, customer_slug, rep_name)

    summaries = db.query(CallSummary).filter(
        CallSummary.call_id.in_(db.query(call_ids_sq)),
        CallSummary.overall_sentiment.isnot(None),
    ).all()
    counter = Counter(s.overall_sentiment for s in summaries)
    return {"distribution": dict(counter), "total": len(summaries)}


@router.get("/scorecard", response_model=ScorecardOverview)
def scorecard_analytics(
    customer_slug: Optional[str] = None,
    rep_name: Optional[str] = None,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    """Aggregate scorecard: average score per skill across all scored calls."""
    call_ids_sq = _call_id_subquery(db, user, customer_slug, rep_name, processed_only=True)

    # SQL aggregation instead of loading all rows into Python
    rows = (
        db.query(
            CallScore.skill_name,
            CallScore.skill_category,
            func.avg(CallScore.score).label("avg_score"),
            func.sum(case((CallScore.present == True, 1), else_=0)).label("times_present"),
            func.count().label("total"),
        )
        .filter(CallScore.call_id.in_(db.query(call_ids_sq)))
        .group_by(CallScore.skill_name, CallScore.skill_category)
        .all()
    )

    if not rows:
        return ScorecardOverview(
            skill_averages=[],
            total_scored_calls=0,
            categories=[{"key": c["key"], "label": c["label"]} for c in SCORECARD_CATEGORIES],
        )

    # Count distinct scored calls
    scored_count = (
        db.query(func.count(func.distinct(CallScore.call_id)))
        .filter(CallScore.call_id.in_(db.query(call_ids_sq)))
        .scalar()
    )

    skill_averages = [
        SkillAverage(
            skill_name=row.skill_name,
            skill_category=row.skill_category,
            avg_score=round(float(row.avg_score), 1),
            times_present=int(row.times_present),
            total_calls=int(row.total),
        )
        for row in rows
    ]

    return ScorecardOverview(
        skill_averages=skill_averages,
        total_scored_calls=scored_count or 0,
        categories=[{"key": c["key"], "label": c["label"]} for c in SCORECARD_CATEGORIES],
    )


@router.get("/scorecard/correlation")
def scorecard_correlation(
    customer_slug: Optional[str] = None,
    rep_name: Optional[str] = None,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    """Which skills correlate with higher deal likelihood?"""
    call_ids_sq = _call_id_subquery(db, user, customer_slug, rep_name, processed_only=True)

    # SQL join: scores + summaries, grouped by skill
    rows = (
        db.query(
            CallScore.skill_name,
            func.avg(case((CallScore.present == True, CallSummary.deal_likelihood))).label("avg_when_present"),
            func.avg(case((CallScore.present == False, CallSummary.deal_likelihood))).label("avg_when_absent"),
            func.sum(case((CallScore.present == True, 1), else_=0)).label("calls_present"),
            func.sum(case((CallScore.present == False, 1), else_=0)).label("calls_absent"),
        )
        .join(CallSummary, CallScore.call_id == CallSummary.call_id)
        .filter(
            CallScore.call_id.in_(db.query(call_ids_sq)),
            CallSummary.deal_likelihood.isnot(None),
        )
        .group_by(CallScore.skill_name)
        .all()
    )

    total_calls = (
        db.query(func.count(func.distinct(CallScore.call_id)))
        .join(CallSummary, CallScore.call_id == CallSummary.call_id)
        .filter(
            CallScore.call_id.in_(db.query(call_ids_sq)),
            CallSummary.deal_likelihood.isnot(None),
        )
        .scalar()
    ) or 0

    correlations = []
    for row in rows:
        avg_p = round(float(row.avg_when_present), 1) if row.avg_when_present else None
        avg_a = round(float(row.avg_when_absent), 1) if row.avg_when_absent else None
        correlations.append({
            "skill_name": row.skill_name,
            "avg_deal_when_present": avg_p,
            "avg_deal_when_absent": avg_a,
            "lift": round(avg_p - avg_a, 1) if avg_p is not None and avg_a is not None else None,
            "calls_present": int(row.calls_present),
            "calls_absent": int(row.calls_absent),
        })

    correlations.sort(key=lambda x: x.get("lift") or 0, reverse=True)
    return {"correlations": correlations, "total_calls": total_calls}


def _field_frequency(
    db: Session, field_name: str, user: Optional[User] = None,
    customer_slug: Optional[str] = None, rep_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Get frequency counts for a list-type field."""
    call_ids_sq = _call_id_subquery(db, user, customer_slug, rep_name)

    fields = db.query(CallField).filter(
        CallField.field_name == field_name,
        CallField.call_id.in_(db.query(call_ids_sq)),
    ).all()

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
