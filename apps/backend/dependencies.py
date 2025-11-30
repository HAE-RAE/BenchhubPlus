"""Common FastAPI dependencies for authentication and authorization."""

from typing import Optional

from fastapi import Depends, Header, HTTPException, Cookie, status
from sqlalchemy.orm import Session

from ..core.db import User, get_db
from ..core.security import verify_jwt_token


def _extract_token(authorization: Optional[str], access_token: Optional[str]) -> Optional[str]:
    """Extract JWT token from Authorization header or cookie."""
    if authorization and authorization.startswith("Bearer "):
        return authorization.replace("Bearer ", "", 1)
    if access_token:
        return access_token
    return None


def get_current_user(
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
) -> User:
    """Resolve current authenticated user."""
    token = _extract_token(authorization, access_token)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    payload = verify_jwt_token(token)
    user_id_raw = payload.get("sub")
    try:
        user_id = int(user_id_raw)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token subject",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User inactive")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    """Require administrative privileges."""
    if not (user.is_admin or user.role == "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return user


def get_optional_user(
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Best-effort user resolution; returns None if unauthenticated."""
    try:
        return get_current_user(authorization, access_token, db)
    except HTTPException as exc:
        if exc.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN):
            return None
        raise
