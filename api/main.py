import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .auth import get_current_user
from .database import get_db
from .models import User
from .routers import analytics, calls, chunks, schemas
from .templates import get_template, list_templates

app = FastAPI(
    title="Gong Call Chunker",
    description="Extract structured intelligence from sales call transcripts",
    version="1.0.0",
)

origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(calls.router, prefix="/api/v1/calls", tags=["calls"])
app.include_router(chunks.router, prefix="/api/v1/chunks", tags=["chunks"])
app.include_router(schemas.router, prefix="/api/v1/schemas", tags=["schemas"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])


@app.get("/health")
def health():
    return {"status": "ok"}


# --- User endpoints ---


@app.get("/api/v1/me")
def get_me(
    user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not user:
        return {"id": None, "authenticated": False}
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "picture": user.picture,
        "has_completed_onboarding": user.has_completed_onboarding,
        "authenticated": True,
    }


class UserUpdate(BaseModel):
    has_completed_onboarding: Optional[bool] = None
    name: Optional[str] = None


@app.patch("/api/v1/me")
def update_me(
    body: UserUpdate,
    user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not user:
        return {"ok": False, "error": "Not authenticated"}
    if body.has_completed_onboarding is not None:
        user.has_completed_onboarding = body.has_completed_onboarding
    if body.name is not None:
        user.name = body.name
    db.commit()
    return {"ok": True}


# --- Templates endpoint ---


@app.get("/api/v1/templates")
def get_templates():
    """List available industry templates for onboarding."""
    return list_templates()


@app.get("/api/v1/templates/{industry}")
def get_template_detail(industry: str):
    """Get a specific industry template with full field definitions."""
    template = get_template(industry)
    if not template:
        from fastapi import HTTPException
        raise HTTPException(404, f"No template found for: {industry}")
    return template
