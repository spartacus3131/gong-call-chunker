#!/usr/bin/env python3
"""
Gong Sync CLI
=============
Pull calls from Gong API and store them locally.

Usage:
    python scripts/sync_gong.py --customer touchbistro
    python scripts/sync_gong.py --customer touchbistro --from 2026-01-01 --to 2026-02-01
"""

import argparse
import asyncio
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv

load_dotenv()

from api.database import engine, SessionLocal, Base
from api.models import Call, Customer
from src.gong_client import GongClient
from src.transcript_parser import normalize_transcript, entries_to_text


async def sync(customer_slug: str, from_date: str = None, to_date: str = None):
    Base.metadata.create_all(engine)
    db = SessionLocal()

    customer = db.query(Customer).filter(Customer.slug == customer_slug).first()
    if not customer:
        print(f"Error: Customer '{customer_slug}' not found. Run seed_sample.py first or create via API.")
        return

    client = GongClient()

    from_dt = datetime.fromisoformat(from_date) if from_date else None
    to_dt = datetime.fromisoformat(to_date) if to_date else None

    print(f"Fetching calls from Gong...")
    calls = await client.sync_calls(from_dt, to_dt)
    print(f"Found {len(calls)} calls")

    created = 0
    for gong_call in calls:
        gong_id = gong_call.get("id") or gong_call.get("callId")
        if not gong_id:
            continue

        existing = db.query(Call).filter(Call.gong_call_id == gong_id).first()
        if existing:
            print(f"  Skipping (exists): {gong_id}")
            continue

        print(f"  Fetching transcript for {gong_id}...")
        transcript_data = await client.get_call_transcript(gong_id)
        entries = normalize_transcript("gong_api", transcript_data)
        transcript_text = entries_to_text(entries)

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
            raw_transcript=transcript_text,
        )
        db.add(call)
        created += 1

    db.commit()
    db.close()
    print(f"\nSynced {created} new calls from Gong.")


def main():
    parser = argparse.ArgumentParser(description="Sync calls from Gong API")
    parser.add_argument("--customer", required=True, help="Customer slug (e.g., touchbistro)")
    parser.add_argument("--from", dest="from_date", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--to", dest="to_date", help="End date (YYYY-MM-DD)")
    args = parser.parse_args()

    asyncio.run(sync(args.customer, args.from_date, args.to_date))


if __name__ == "__main__":
    main()
