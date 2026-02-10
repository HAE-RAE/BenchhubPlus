import logging
import re
from datetime import datetime, timezone
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, status
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ...core.config import get_settings
from ...core.db import User, Organization, Workspace, WorkspaceMembership, get_db
from ...core.schemas import ErrorResponse, UserResponse
from ...core.security import (
    create_jwt_token,
    get_google_user_info,
    verify_jwt_token,
)

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


def _slugify(value: str) -> str:
    """Create a URL-safe slug."""
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", (value or "").strip().lower())
    return normalized.strip("-") or "org"


def _ensure_default_workspace(user: User, db: Session) -> None:
    """Ensure user has a default organization/workspace and membership."""
    org = None
    if user.default_org_id:
        org = db.query(Organization).filter(Organization.id == user.default_org_id).first()

    if org is None:
        org_slug = f"user-{user.id}"
        org_name = user.full_name or user.email or f"user-{user.id}"
        org = Organization(name=org_name, slug=_slugify(org_slug))
        db.add(org)
        db.commit()
        db.refresh(org)

    workspace = None
    if user.default_workspace_id:
        workspace = db.query(Workspace).filter(Workspace.id == user.default_workspace_id).first()

    if workspace is None:
        workspace_slug = f"default-{user.id}"
        workspace = Workspace(
            organization_id=org.id,
            name="Default",
            slug=_slugify(workspace_slug),
        )
        db.add(workspace)
        db.commit()
        db.refresh(workspace)

    membership = (
        db.query(WorkspaceMembership)
        .filter(
            WorkspaceMembership.workspace_id == workspace.id,
            WorkspaceMembership.user_id == user.id,
        )
        .first()
    )
    if membership is None:
        membership = WorkspaceMembership(
            workspace_id=workspace.id,
            user_id=user.id,
            role="owner",
            is_owner=True,
        )
        db.add(membership)
        db.commit()

    if user.default_org_id != org.id or user.default_workspace_id != workspace.id:
        user.default_org_id = org.id
        user.default_workspace_id = workspace.id
        db.commit()


class DevLoginRequest(BaseModel):
    """Payload for development-only login."""

    email: str = Field(..., min_length=1)
    name: Optional[str] = None


@router.get("/google/login", status_code=status.HTTP_302_FOUND)
async def google_login():
    """Redirect to Google OAuth login page."""
    if settings.debug or settings.dev_auth_bypass:
        # Dev-only: skip Google OAuth and use a default dev user.
        redirect_url = f"{settings.frontend_url}?dev_login=true"
        return RedirectResponse(url=redirect_url)

    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={settings.google_client_id}&"
        f"redirect_uri={settings.google_redirect_uri}&"
        "response_type=code&"
        "scope=openid email profile"
    )
    
    logger.info("Redirecting to Google OAuth")
    return RedirectResponse(url=google_auth_url)


@router.get("/google/callback", status_code=status.HTTP_302_FOUND)
async def google_callback(code: str, db: Session = Depends(get_db)):
    """Handle Google OAuth callback and authenticate user."""
    if settings.debug or settings.dev_auth_bypass:
        raise HTTPException(status_code=400, detail="Google OAuth disabled in dev mode")
    try:
        google_user = await get_google_user_info(code)
        logger.info(f"Google OAuth successful for email: {google_user.get('email')}")
        
        user = db.query(User).filter(User.email == google_user["email"]).first()
        
        if not user:
            is_first_user = db.query(User).count() == 0
            user = User(
                google_id=google_user["id"],
                email=google_user["email"],
                email_verified=google_user.get("verified_email", False),
                full_name=google_user.get("name"),
                picture_url=google_user.get("picture"),
                is_active=True,
                last_login_at=datetime.now(timezone.utc),
                role="admin" if is_first_user else "user",
                is_admin=is_first_user,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"Created new user: {user.email}")
        else:
            user.last_login_at = datetime.now(timezone.utc)
            user.full_name = google_user.get("name", user.full_name)
            user.picture_url = google_user.get("picture", user.picture_url)
            db.commit()
            logger.info(f"User logged in: {user.email}")

        _ensure_default_workspace(user, db)
        
        access_token = create_jwt_token(user.id, user.email)
        
        frontend_url = f"{settings.frontend_url}?token={access_token}"
        response = RedirectResponse(url=frontend_url, status_code=302)
        
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=86400,
            path="/"
        )
        
        logger.info(f"JWT token generated for user: {user.email}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google OAuth callback failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Authentication failed: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Get current authenticated user information."""
    try:
        token = None
        if authorization and authorization.startswith("Bearer "):
            token = authorization.replace("Bearer ", "")
        
        if not token:
            raise HTTPException(
                status_code=401,
                detail="Not authenticated - no token provided"
            )
        
        current_user = verify_jwt_token(token)
        user_id = int(current_user["sub"])
        
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if not user.is_active:
            raise HTTPException(status_code=403, detail="User account is inactive")
        
        return {
            "id": user.id,
            "email": user.email,
            "name": user.full_name,
            "picture": user.picture_url,
            "email_verified": user.email_verified,
            "role": user.role,
            "organization_id": user.default_org_id,
            "workspace_id": user.default_workspace_id,
            "created_at": user.created_at,
            "last_login_at": user.last_login_at
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID in token")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get current user: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user information")


@router.post("/logout", status_code=status.HTTP_302_FOUND)
async def logout():
    """Logout user and clear authentication cookie."""
    response = RedirectResponse(
        url=settings.frontend_url,
        status_code=302
    )
    
    response.delete_cookie(
        key="access_token",
        path="/",
        httponly=True,
        samesite="lax"
    )
    
    logger.info("User logged out")
    return response


@router.post("/dev-login")
async def dev_login(
    payload: DevLoginRequest,
    db: Session = Depends(get_db),
):
    """Development-only login that accepts any input."""
    if not (settings.debug or settings.dev_auth_bypass):
        raise HTTPException(status_code=404, detail="Not found")

    email = payload.email.strip()
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            google_id=f"dev:{email}",
            email=email,
            email_verified=True,
            full_name=payload.name or email,
            picture_url=None,
            is_active=True,
            role="admin",
            is_admin=True,
            last_login_at=datetime.now(timezone.utc),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        user.full_name = payload.name or user.full_name
        user.last_login_at = datetime.now(timezone.utc)
        user.role = "admin"
        user.is_admin = True
        db.commit()

    _ensure_default_workspace(user, db)

    access_token = create_jwt_token(user.id, user.email)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.full_name,
            "role": user.role,
        },
    }
