"""Schemas router — manage customer extraction schemas."""

import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import Customer, User
from ..schemas import CustomerSchema
from src.schema_loader import (
    list_customers,
    load_customer_schema,
    save_customer_schema,
)

router = APIRouter()

SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def _validate_slug(slug: str) -> None:
    if not SLUG_PATTERN.match(slug) or len(slug) > 64:
        raise HTTPException(
            400,
            "Slug must be lowercase alphanumeric with hyphens/underscores only (max 64 chars)",
        )


@router.get("", response_model=List[Dict[str, str]])
def list_schemas(
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    """List customer schemas owned by the current user."""
    if not user:
        # Dev mode: return all from filesystem
        return list_customers()

    customers = db.query(Customer).filter(Customer.user_id == user.id).all()
    return [
        {
            "slug": c.slug,
            "display_name": c.name,
            "config_path": c.config_path,
        }
        for c in customers
    ]


@router.get("/{slug}")
def get_schema(
    slug: str,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    """Get the full extraction schema for a customer."""
    _validate_slug(slug)

    # Verify ownership
    if user:
        customer = db.query(Customer).filter(
            Customer.slug == slug, Customer.user_id == user.id
        ).first()
        if not customer:
            raise HTTPException(404, f"No schema found for: {slug}")

    try:
        return load_customer_schema(slug)
    except FileNotFoundError:
        raise HTTPException(404, f"No schema found for: {slug}")


@router.put("/{slug}")
def update_schema(
    slug: str,
    body: Dict[str, Any],
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    """Update a customer's extraction schema."""
    _validate_slug(slug)

    # Verify ownership
    if user:
        customer = db.query(Customer).filter(
            Customer.slug == slug, Customer.user_id == user.id
        ).first()
        if not customer:
            raise HTTPException(404, f"No schema found for: {slug}")

    body["customer"] = slug
    path = save_customer_schema(slug, body)
    return {"saved": True, "path": str(path)}


@router.post("")
def create_schema(
    body: Dict[str, Any],
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    """Create a new customer schema."""
    slug = body.get("customer")
    if not slug:
        raise HTTPException(400, "customer slug is required")
    _validate_slug(slug)

    # Check uniqueness within user's schemas
    if user:
        existing = db.query(Customer).filter(
            Customer.slug == slug, Customer.user_id == user.id
        ).first()
        if existing:
            raise HTTPException(409, f"Schema already exists for: {slug}")
    else:
        try:
            load_customer_schema(slug)
            raise HTTPException(409, f"Schema already exists for: {slug}")
        except FileNotFoundError:
            pass

    # Save YAML file
    path = save_customer_schema(slug, body)

    # Create Customer DB record
    customer = Customer(
        user_id=user.id if user else None,
        name=body.get("display_name", slug),
        slug=slug,
        config_path=str(path),
    )
    db.add(customer)
    db.commit()

    return {"created": True, "slug": slug, "path": str(path)}
