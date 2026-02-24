#!/usr/bin/env python3
"""
Seed Sample Data
================
Creates sample call records with a mock TouchBistro transcript for demo purposes.
Run: python scripts/seed_sample.py
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv

load_dotenv()

from api.database import engine, SessionLocal, Base
from api.models import Customer, Call

# Sample transcripts
SAMPLE_CALLS = [
    {
        "title": "Discovery Call - Mario's Pizzeria (3 locations)",
        "date": datetime(2026, 2, 10, 14, 30),
        "duration_seconds": 1800,
        "participants": ["Sarah Chen (AE)", "Mario Rossi (Owner)"],
        "transcript": """[00:00] Sarah Chen: Hi Mario, thanks for taking the time today. I'd love to learn more about your restaurant operations and see if TouchBistro might be a good fit.

[00:15] Mario Rossi: Thanks Sarah. Yeah, we've been looking at options. We have three pizzeria locations in the Chicago area - two dine-in and one that's mostly delivery and takeout.

[00:32] Sarah Chen: That's great. What POS system are you currently using?

[00:38] Mario Rossi: We're on Square right now. It was fine when we had one location, but honestly it's been a nightmare trying to manage three stores. The reporting is terrible - I can't get a consolidated view across locations without exporting spreadsheets and doing it manually.

[01:05] Sarah Chen: That's a really common pain point we hear, especially from multi-location operators. What does your team size look like across the three locations?

[01:15] Mario Rossi: About 45 people total. The scheduling is another headache. We're using a separate app for that - 7shifts actually - but it doesn't talk to Square very well. I end up with labor data in one place and sales data in another.

[01:42] Sarah Chen: Integration issues between systems - that's huge. Are there other tools in your tech stack that you'd ideally want connected?

[01:52] Mario Rossi: Yeah, we use DoorDash and UberEats for delivery, and QuickBooks for accounting. Right now everything is manual. My manager spends probably 10 hours a week just reconciling numbers across systems.

[02:15] Sarah Chen: That's a lot of wasted time. Let me ask about your dine-in operations - how many seats do you have at each location?

[02:22] Mario Rossi: The main location has about 80 seats, the second one has 50, and the delivery spot obviously doesn't have dine-in. We've been thinking about adding online ordering directly through our website too, instead of relying on the delivery apps and paying their fees.

[02:48] Sarah Chen: Smart move. The commission fees from those apps really eat into margins. With TouchBistro, you'd get built-in online ordering that goes through your own branded system - no commission fees. Plus it integrates natively with DoorDash and UberEats for the orders that do come through those channels.

[03:15] Mario Rossi: That sounds interesting. What about the kitchen side? We've been having issues with order accuracy, especially during rush hours. Tickets get lost, modifications get missed.

[03:30] Sarah Chen: Our Kitchen Display System solves exactly that. Orders flow directly from the POS to the kitchen screens with all modifications highlighted. No more lost paper tickets.

[03:45] Mario Rossi: And the pricing? We're paying about $60 per month per terminal with Square. We have 8 terminals total across the three locations.

[04:00] Sarah Chen: I'd want to put together a custom quote based on your exact needs, but I can tell you we're very competitive in the multi-location space. The value really comes from consolidating all those separate tools - scheduling, online ordering, kitchen display - into one platform.

[04:20] Mario Rossi: Makes sense. We're not in a huge rush - our Square contract renews in about 3 months. But I'd like to see a demo with my operations manager, Tony. He's the one who'd be using it day to day.

[04:40] Sarah Chen: Absolutely. Let's set up a demo for next week. I'll make sure to show the multi-location reporting and the kitchen display system since those seem like your biggest pain points.

[04:55] Mario Rossi: Sounds good. Tuesday or Wednesday would work best for us.

[05:05] Sarah Chen: Perfect, I'll send over a calendar invite for Tuesday at 2pm. Thanks Mario, looking forward to showing you what we can do.""",
    },
    {
        "title": "Demo Follow-up - Sakura Sushi Bar (Fine Dining)",
        "date": datetime(2026, 2, 15, 11, 0),
        "duration_seconds": 2400,
        "participants": ["James Park (AE)", "Yuki Tanaka (Owner)", "Lisa Wong (GM)"],
        "transcript": """[00:00] James Park: Yuki, Lisa, great to have you both on. How did the demo go from your perspective?

[00:08] Yuki Tanaka: It was impressive, honestly. Lisa and I were talking after and we both liked the reservation management piece a lot. That's been our biggest struggle.

[00:22] Lisa Wong: Yeah, we're using Resy right now and it's fine, but having it built into the POS would simplify things. We wouldn't need two separate systems for front-of-house management.

[00:38] James Park: That integration is a big win for fine dining operations. Everything flows together - reservations, table management, the POS. No more switching between apps.

[00:50] Yuki Tanaka: My concern is the transition. We're a 60-seat fine dining restaurant. We can't afford any downtime or confusion during service. Our average check is $120 and our guests expect perfection.

[01:10] James Park: Completely understand. For fine dining transitions, we do a phased rollout. We'd train your staff in sessions over two weeks before going live, and we have a dedicated onboarding specialist on-site for your first three services.

[01:30] Lisa Wong: That's reassuring. What about the loyalty program? We have regulars who come in weekly and we want to recognize them without it feeling transactional. You know, not like a punch card.

[01:48] James Park: Our loyalty system is very customizable. For fine dining, most of our clients use it behind the scenes - your staff sees a note when a loyalty member is seated, their preferences, previous orders, any allergies. The guest doesn't have to scan anything or present a card.

[02:10] Yuki Tanaka: That's exactly what we want. Now, the elephant in the room - we're currently on Toast and we still have about 8 months on our contract. We'd need to factor in the early termination.

[02:30] James Park: That's something we can absolutely work with. We have programs to help with transition costs for operators switching from competitive platforms. I can put together a proposal that accounts for that overlap period.

[02:48] Lisa Wong: What about inventory management? We do omakase so our menu changes daily based on what fish is available. We need flexibility.

[03:05] James Park: The inventory system supports dynamic menus. You can update items and pricing on the fly, and it tracks waste - which I know is critical for a sushi operation where ingredient costs are high.

[03:22] Yuki Tanaka: Waste tracking would be huge for us. We're probably losing 15-20% on fish waste right now and we don't have good data on it.

[03:35] James Park: That's a significant number. Most of our sushi and fine dining clients reduce waste by 8-12% within the first quarter just from having visibility into the data.

[03:50] Yuki Tanaka: That alone could pay for the system. Let me talk to my accountant about the Toast termination costs and the overall budget. Can you send over a formal proposal by Friday?

[04:05] James Park: Absolutely. I'll include the transition support package and the ROI analysis based on the waste reduction numbers we discussed. Anything else you'd like me to address in the proposal?

[04:20] Lisa Wong: Can you include details on the staff training program? I want to make sure our servers are comfortable with it before we commit.

[04:30] James Park: Of course. I'll outline the full onboarding timeline and training plan. You'll have it by Friday.""",
    },
    {
        "title": "Outbound Discovery - Quick Bites QSR (10 locations)",
        "date": datetime(2026, 2, 20, 9, 0),
        "duration_seconds": 1200,
        "participants": ["Sarah Chen (AE)", "Dave Martinez (VP Ops)"],
        "transcript": """[00:00] Sarah Chen: Dave, thanks for taking my call. I know you're busy managing 10 locations. I'll keep this brief.

[00:10] Dave Martinez: Yeah, I've got about 15 minutes. What's this about?

[00:15] Sarah Chen: We've been working with several QSR chains in your area and I wanted to see if you're facing any of the same challenges - specifically around speed of service and labor efficiency.

[00:28] Dave Martinez: Honestly, speed is everything in QSR. Our average order time needs to be under 3 minutes and right now we're closer to 4. It's costing us customers during lunch rush.

[00:42] Sarah Chen: What POS system are you running across the 10 locations?

[00:48] Dave Martinez: Clover. It's been okay for basic transactions but it's really just a glorified cash register. I don't get the operational insights I need to optimize throughput.

[01:05] Sarah Chen: How are you handling the kitchen flow? Paper tickets or digital?

[01:10] Dave Martinez: Paper. And it's chaos during rush. Orders get mixed up, custom modifications get missed. We probably remake 5-8% of orders due to errors.

[01:28] Sarah Chen: 5-8% remake rate across 10 locations - that's a significant food cost hit. Our KDS routes orders intelligently and highlights modifications. Most QSR clients see remake rates drop to under 2%.

[01:45] Dave Martinez: That would save us a fortune. What about drive-through? Eight of our ten locations have drive-through and that's where we do 65% of our volume.

[02:00] Sarah Chen: Drive-through optimization is one of our strongest areas for QSR. We have timer integration, order confirmation displays, and the kitchen gets orders queued before the car reaches the window.

[02:15] Dave Martinez: Interesting. We're also looking at self-service kiosks for the two locations that don't have drive-through. Is that something you support?

[02:28] Sarah Chen: Yes, our kiosk solution integrates directly with the POS and kitchen display. Same menu, same modifiers, no separate system to manage.

[02:40] Dave Martinez: Look, I'm interested but I need to be real with you - we're mid-budget cycle. Any POS change would be a Q3 decision at the earliest. Our CEO needs to sign off on anything over $50K.

[02:58] Sarah Chen: Totally understand. Would it be helpful if I put together an ROI analysis showing the savings from reduced remake rates and improved throughput? That could give you the business case for the Q3 budget conversation.

[03:12] Dave Martinez: Yeah, that would actually be really helpful. Send me something I can bring to my CEO.

[03:20] Sarah Chen: Will do. I'll have it to you by end of week. Thanks for the time, Dave.""",
    },
]


def seed():
    Base.metadata.create_all(engine)
    db = SessionLocal()

    # Create or get TouchBistro customer
    customer = db.query(Customer).filter(Customer.slug == "touchbistro").first()
    if not customer:
        customer = Customer(
            name="TouchBistro POS",
            slug="touchbistro",
            config_path="config/customers/touchbistro.yaml",
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
        print(f"Created customer: {customer.name}")

    # Create sample calls
    for sample in SAMPLE_CALLS:
        existing = (
            db.query(Call)
            .filter(Call.title == sample["title"], Call.customer_id == customer.id)
            .first()
        )
        if existing:
            print(f"  Skipping (exists): {sample['title']}")
            continue

        call = Call(
            customer_id=customer.id,
            title=sample["title"],
            date=sample["date"],
            duration_seconds=sample["duration_seconds"],
            participants=sample["participants"],
            raw_transcript=sample["transcript"],
        )
        db.add(call)
        print(f"  Created: {sample['title']}")

    db.commit()
    db.close()
    print(f"\nDone! Seeded {len(SAMPLE_CALLS)} sample calls for TouchBistro.")
    print("Run the API and chunk them: POST /api/v1/calls/{id}/chunk")


if __name__ == "__main__":
    seed()
