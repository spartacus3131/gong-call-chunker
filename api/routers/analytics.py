"""Analytics router — aggregate queries across chunked calls."""

from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import Call, CallField, CallScore, CallSummary, Customer, User
from ..schemas import AnalyticsResponse, FieldDistribution, ScorecardOverview, SkillAverage
from ..templates import DEFAULT_SCORECARD_SKILLS, SCORECARD_CATEGORIES

router = APIRouter()


def _user_call_query(db: Session, user: Optional[User], customer_slug: Optional[str] = None):
    """Build a base Call query scoped to the current user and optional customer."""
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

    return query


@router.get("/overview", response_model=AnalyticsResponse)
def analytics_overview(
    customer_slug: Optional[str] = None,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    """High-level analytics: total calls, field distributions."""
    call_query = _user_call_query(db, user, customer_slug)

    total = call_query.count()
    chunked = call_query.filter(Call.processed_at.isnot(None)).count()

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
    user: Optional[User] = Depends(get_current_user),
):
    return _field_frequency(db, "pain_points", user, customer_slug)


@router.get("/competitors")
def competitor_analysis(
    customer_slug: Optional[str] = None,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    return _field_frequency(db, "competitor_mentions", user, customer_slug)


@router.get("/deal-likelihood")
def deal_likelihood_distribution(
    customer_slug: Optional[str] = None,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    call_query = _user_call_query(db, user, customer_slug)
    call_ids = db.query(Call.id).filter(Call.id.in_([c.id for c in call_query.all()]))

    summaries = db.query(CallSummary).filter(
        CallSummary.call_id.in_(call_ids),
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
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    call_query = _user_call_query(db, user, customer_slug)
    call_ids = db.query(Call.id).filter(Call.id.in_([c.id for c in call_query.all()]))

    summaries = db.query(CallSummary).filter(
        CallSummary.call_id.in_(call_ids),
        CallSummary.overall_sentiment.isnot(None),
    ).all()
    counter = Counter(s.overall_sentiment for s in summaries)
    return {"distribution": dict(counter), "total": len(summaries)}


@router.get("/scorecard", response_model=ScorecardOverview)
def scorecard_analytics(
    customer_slug: Optional[str] = None,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    """Aggregate scorecard: average score per skill across all scored calls."""
    call_query = _user_call_query(db, user, customer_slug)
    call_ids = [c.id for c in call_query.filter(Call.processed_at.isnot(None)).all()]

    if not call_ids:
        return ScorecardOverview(
            skill_averages=[],
            total_scored_calls=0,
            categories=[{"key": c["key"], "label": c["label"]} for c in SCORECARD_CATEGORIES],
        )

    scores = db.query(CallScore).filter(CallScore.call_id.in_(call_ids)).all()

    # Group by skill
    skill_data: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"scores": [], "present_count": 0, "category": ""})
    scored_call_ids = set()
    for s in scores:
        skill_data[s.skill_name]["scores"].append(s.score)
        skill_data[s.skill_name]["category"] = s.skill_category
        if s.present:
            skill_data[s.skill_name]["present_count"] += 1
        scored_call_ids.add(s.call_id)

    skill_averages = []
    for skill_name, data in sorted(skill_data.items()):
        skill_averages.append(SkillAverage(
            skill_name=skill_name,
            skill_category=data["category"],
            avg_score=round(sum(data["scores"]) / len(data["scores"]), 1),
            times_present=data["present_count"],
            total_calls=len(data["scores"]),
        ))

    return ScorecardOverview(
        skill_averages=skill_averages,
        total_scored_calls=len(scored_call_ids),
        categories=[{"key": c["key"], "label": c["label"]} for c in SCORECARD_CATEGORIES],
    )


@router.get("/scorecard/correlation")
def scorecard_correlation(
    customer_slug: Optional[str] = None,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    """Which skills correlate with higher deal likelihood?"""
    call_query = _user_call_query(db, user, customer_slug)
    call_ids = [c.id for c in call_query.filter(Call.processed_at.isnot(None)).all()]

    if not call_ids:
        return {"correlations": [], "total_calls": 0}

    # Get deal likelihoods
    summaries = db.query(CallSummary).filter(
        CallSummary.call_id.in_(call_ids),
        CallSummary.deal_likelihood.isnot(None),
    ).all()
    deal_map = {s.call_id: s.deal_likelihood for s in summaries}

    if not deal_map:
        return {"correlations": [], "total_calls": 0}

    # Get scores for calls that have deal likelihood
    scores = db.query(CallScore).filter(
        CallScore.call_id.in_(list(deal_map.keys())),
    ).all()

    # For each skill: avg deal likelihood when present vs absent
    skill_present: Dict[str, List[float]] = defaultdict(list)
    skill_absent: Dict[str, List[float]] = defaultdict(list)
    for s in scores:
        if s.call_id not in deal_map:
            continue
        dl = deal_map[s.call_id]
        if s.present:
            skill_present[s.skill_name].append(dl)
        else:
            skill_absent[s.skill_name].append(dl)

    correlations = []
    for skill_name in sorted(set(list(skill_present.keys()) + list(skill_absent.keys()))):
        present_deals = skill_present.get(skill_name, [])
        absent_deals = skill_absent.get(skill_name, [])
        avg_when_present = round(sum(present_deals) / len(present_deals), 1) if present_deals else None
        avg_when_absent = round(sum(absent_deals) / len(absent_deals), 1) if absent_deals else None
        correlations.append({
            "skill_name": skill_name,
            "avg_deal_when_present": avg_when_present,
            "avg_deal_when_absent": avg_when_absent,
            "lift": round(avg_when_present - avg_when_absent, 1) if avg_when_present and avg_when_absent else None,
            "calls_present": len(present_deals),
            "calls_absent": len(absent_deals),
        })

    # Sort by lift descending
    correlations.sort(key=lambda x: x.get("lift") or 0, reverse=True)

    return {"correlations": correlations, "total_calls": len(deal_map)}


def _field_frequency(
    db: Session, field_name: str, user: Optional[User] = None, customer_slug: Optional[str] = None
) -> Dict[str, Any]:
    """Get frequency counts for a list-type field."""
    call_query = _user_call_query(db, user, customer_slug)
    call_ids = [c.id for c in call_query.all()]

    fields = db.query(CallField).filter(
        CallField.field_name == field_name,
        CallField.call_id.in_(call_ids),
    ).all() if call_ids else []

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
