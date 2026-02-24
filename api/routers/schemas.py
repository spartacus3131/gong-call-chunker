"""Schemas router — manage customer extraction schemas."""

import re
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from src.schema_loader import (
    list_customers,
    load_customer_schema,
    save_customer_schema,
)
from ..schemas import CustomerSchema

router = APIRouter()

SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def _validate_slug(slug: str) -> None:
    if not SLUG_PATTERN.match(slug) or len(slug) > 64:
        raise HTTPException(
            400,
            "Slug must be lowercase alphanumeric with hyphens/underscores only (max 64 chars)",
        )


@router.get("", response_model=List[Dict[str, str]])
def list_schemas():
    """List all available customer schemas."""
    return list_customers()


@router.get("/{slug}")
def get_schema(slug: str):
    """Get the full extraction schema for a customer."""
    _validate_slug(slug)
    try:
        return load_customer_schema(slug)
    except FileNotFoundError:
        raise HTTPException(404, f"No schema found for: {slug}")


@router.put("/{slug}")
def update_schema(slug: str, body: Dict[str, Any]):
    """Update a customer's extraction schema.

    Accepts the full schema YAML structure as JSON.
    Writes back to the YAML file.
    """
    _validate_slug(slug)
    body["customer"] = slug
    path = save_customer_schema(slug, body)
    return {"saved": True, "path": str(path)}


@router.post("")
def create_schema(body: Dict[str, Any]):
    """Create a new customer schema."""
    slug = body.get("customer")
    if not slug:
        raise HTTPException(400, "customer slug is required")
    _validate_slug(slug)

    try:
        load_customer_schema(slug)
        raise HTTPException(409, f"Schema already exists for: {slug}")
    except FileNotFoundError:
        pass

    path = save_customer_schema(slug, body)
    return {"created": True, "slug": slug, "path": str(path)}
