"""Calls router — CRUD, upload, Gong sync, and chunking."""

import json
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import desc
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Call, CallChunk, CallField, CallSummary, Customer
from ..schemas import CallCreate, CallDetail, CallOut, GongSyncRequest
from src.call_chunker import CallChunker
from src.schema_loader import list_customers
from src.transcript_parser import normalize_transcript

router = APIRouter()


def _get_or_create_customer(db: Session, slug: str) -> Customer:
    customer = db.query(Customer).filter(Customer.slug == slug).first()
    if customer:
        return customer

    # Auto-create from config
    configs = {c["slug"]: c for c in list_customers()}
    if slug not in configs:
        raise HTTPException(404, f"No config found for customer: {slug}")

    cfg = configs[slug]
    customer = Customer(
        name=cfg["display_name"],
        slug=slug,
        config_path=cfg["config_path"],
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("", response_model=List[CallOut])
def list_calls(
    customer_slug: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    query = db.query(Call).order_by(desc(Call.date))
    if customer_slug:
        customer = db.query(Customer).filter(Customer.slug == customer_slug).first()
        if customer:
            query = query.filter(Call.customer_id == customer.id)
    return query.offset(offset).limit(limit).all()


@router.get("/{call_id}", response_model=CallDetail)
def get_call(call_id: str, db: Session = Depends(get_db)):
    call = db.query(Call).filter(Call.id == call_id).first()
    if not call:
        raise HTTPException(404, "Call not found")
    return call


@router.post("", response_model=CallOut)
def create_call(body: CallCreate, db: Session = Depends(get_db)):
    customer = _get_or_create_customer(db, body.customer_slug)
    call = Call(
        customer_id=customer.id,
        gong_call_id=body.gong_call_id,
        title=body.title,
        date=body.date,
        duration_seconds=body.duration_seconds,
        participants=body.participants,
        raw_transcript=body.raw_transcript,
    )
    db.add(call)
    db.commit()
    db.refresh(call)
    return call


@router.post("/upload", response_model=CallOut)
async def upload_transcript(
    file: UploadFile = File(...),
    customer_slug: str = Form(...),
    title: str = Form(...),
    date: str = Form(...),
    db: Session = Depends(get_db),
):
    """Upload a transcript file (JSON, CSV, or plain text)."""
    content = (await file.read()).decode("utf-8")
    customer = _get_or_create_customer(db, customer_slug)

    # Detect format from filename
    format_hint = None
    if file.filename:
        if file.filename.endswith(".csv"):
            format_hint = "csv"
        elif file.filename.endswith(".json"):
            format_hint = "json"

    call = Call(
        customer_id=customer.id,
        title=title,
        date=datetime.fromisoformat(date),
        participants=[],
        raw_transcript=content,
    )
    db.add(call)
    db.commit()
    db.refresh(call)
    return call


@router.post("/{call_id}/chunk", response_model=CallDetail)
def chunk_call(call_id: str, db: Session = Depends(get_db)):
    """Process a call through the chunking engine."""
    call = db.query(Call).filter(Call.id == call_id).first()
    if not call:
        raise HTTPException(404, "Call not found")

    customer = db.query(Customer).filter(Customer.id == call.customer_id).first()
    if not customer:
        raise HTTPException(404, "Customer not found")

    # Mark as processing
    call.status = "processing"
    call.error_message = None
    db.commit()

    try:
        # Run chunker
        chunker = CallChunker()
        entries = normalize_transcript("paste", call.raw_transcript)
        result = chunker.chunk_call(
            transcript_entries=entries,
            customer_slug=customer.slug,
            title=call.title,
            participants=call.participants,
        )
    except Exception as e:
        call.status = "failed"
        call.error_message = str(e)
        db.commit()
        raise HTTPException(
            502,
            detail=f"Chunking failed: {e}. The call has been marked as 'failed' and can be retried.",
        )

    # Clear existing chunks/fields if re-processing
    db.query(CallChunk).filter(CallChunk.call_id == call_id).delete()
    db.query(CallField).filter(CallField.call_id == call_id).delete()
    db.query(CallSummary).filter(CallSummary.call_id == call_id).delete()

    # Store extracted fields
    for field_name, field_value in result.get("fields", {}).items():
        if field_value is not None:
            db.add(CallField(
                call_id=call_id,
                field_name=field_name,
                field_value=field_value,
                field_type=type(field_value).__name__,
            ))

    # Store chunks
    for level in ["topics", "insights", "quotes"]:
        for chunk_data in result.get("chunks", {}).get(level, []):
            db.add(CallChunk(
                call_id=call_id,
                level=level,
                content=chunk_data,
                timestamp_start=chunk_data.get("timestamp_start"),
                timestamp_end=chunk_data.get("timestamp_end"),
            ))

    # Store summary
    summary_data = result.get("summary", {})
    db.add(CallSummary(
        call_id=call_id,
        overall_sentiment=summary_data.get("overall_sentiment"),
        deal_likelihood=summary_data.get("deal_likelihood"),
        next_steps=summary_data.get("next_steps", []),
        follow_up_date=summary_data.get("follow_up_date"),
        summary_text=summary_data.get("summary_text"),
    ))

    call.status = "chunked"
    call.processed_at = datetime.utcnow()
    db.commit()
    db.refresh(call)
    return call


@router.delete("/{call_id}")
def delete_call(call_id: str, db: Session = Depends(get_db)):
    call = db.query(Call).filter(Call.id == call_id).first()
    if not call:
        raise HTTPException(404, "Call not found")
    db.delete(call)
    db.commit()
    return {"deleted": True}


@router.post("/sync/gong")
async def sync_gong(body: GongSyncRequest, db: Session = Depends(get_db)):
    """Pull calls from Gong API and store them.

    Resilient sync: commits in batches, skips failed transcript fetches,
    respects Gong rate limits, and reports per-call errors.
    """
    import asyncio
    from src.gong_client import GongClient

    customer = _get_or_create_customer(db, body.customer_slug)
    client = GongClient()
    calls = await client.sync_calls(body.from_date, body.to_date)

    created = 0
    skipped = 0
    errors = []
    BATCH_SIZE = 10

    for i, gong_call in enumerate(calls):
        gong_id = gong_call.get("id") or gong_call.get("callId")
        if not gong_id:
            continue

        # Skip if already imported
        existing = db.query(Call).filter(Call.gong_call_id == gong_id).first()
        if existing:
            skipped += 1
            continue

        # Fetch transcript with error recovery
        try:
            transcript_data = await client.get_call_transcript(gong_id)
        except Exception as e:
            errors.append({"call_id": gong_id, "error": str(e)})
            continue

        call = Call(
            customer_id=customer.id,
            gong_call_id=gong_id,
            title=gong_call.get("title", f"Call {gong_id}"),
            date=datetime.fromisoformat(
                gong_call.get("started", datetime.utcnow().isoformat()).replace("Z", "")
            ),
            duration_seconds=gong_call.get("duration"),
            participants=[
                p.get("name", p.get("emailAddress", ""))
                for p in gong_call.get("parties", [])
            ],
            raw_transcript=json.dumps(transcript_data),
        )
        db.add(call)
        created += 1

        # Batch commit to preserve progress
        if created % BATCH_SIZE == 0:
            db.commit()

        # Respect Gong rate limits (~3 requests/sec)
        await asyncio.sleep(0.35)

    # Final commit for remaining
    db.commit()

    return {
        "synced": created,
        "skipped_existing": skipped,
        "errors": errors,
        "total_from_gong": len(calls),
    }
