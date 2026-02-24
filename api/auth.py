"""JWT authentication — validates tokens issued by next-auth."""

import os
from typing import Optional

from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from .database import get_db
from .models import User

NEXTAUTH_SECRET = os.environ.get("NEXTAUTH_SECRET", "")
ALGORITHM = "HS256"

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Decode next-auth JWT, find or create user, return User ORM object.

    If NEXTAUTH_SECRET is not set (dev mode), returns None and all
    endpoints work without auth (backward compatible).
    """
    if not NEXTAUTH_SECRET:
        return None  # Dev mode: no auth required

    if not credentials:
        raise HTTPException(401, "Missing Authorization header")

    try:
        payload = jwt.decode(
            credentials.credentials, NEXTAUTH_SECRET, algorithms=[ALGORITHM]
        )
    except JWTError:
        raise HTTPException(401, "Invalid token")

    google_id = payload.get("sub")
    email = payload.get("email")
    if not google_id or not email:
        raise HTTPException(401, "Token missing required claims")

    # Find or create user
    user = db.query(User).filter(User.google_id == google_id).first()
    if not user:
        user = User(
            google_id=google_id,
            email=email,
            name=payload.get("name", email),
            picture=payload.get("picture"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return user
