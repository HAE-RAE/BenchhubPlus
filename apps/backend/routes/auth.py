import logging
import re
from datetime import datetime, timezone
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, field_validator

from ...core.config import get_settings
from ...core.db import User, Organization, Workspace, WorkspaceMembership, get_db
from ...core.schemas import ErrorResponse, UserResponse
from ...core.security import (
    create_jwt_token,
    enforce_login_rate_limit,
    get_google_user_info,
    mask_email,
)
from ..dependencies import get_current_user as _get_current_user_dep

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
    """Payload for development-only login.

    The dev path is intentionally lenient about email format (so quick
    placeholders like ``dev@local`` work). The endpoint itself is gated
    behind DEBUG / DEV_AUTH_BYPASS, so the only consumer is a developer
    on their own machine.
    """

    email: str = Field(..., min_length=3, max_length=255)
    name: Optional[str] = Field(default=None, max_length=255)

    @field_validator("email")
    @classmethod
    def _shape_check(cls, v: str) -> str:
        v = (v or "").strip()
        if "@" not in v or v.startswith("@") or v.endswith("@"):
            raise ValueError("email must contain a local-part and a domain")
        return v


def _client_ip(request: Request) -> str:
    return request.client.host if request and request.client else "anonymous"


def _set_auth_cookie(response, token: str) -> None:
    """Set the access_token cookie with environment-aware flags."""
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=settings.effective_cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.access_token_expire_hours * 3600,
        path="/",
    )


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
async def google_callback(
    request: Request,
    code: str,
    db: Session = Depends(get_db),
):
    """Handle Google OAuth callback and authenticate user."""
    if settings.debug or settings.dev_auth_bypass:
        raise HTTPException(status_code=400, detail="Google OAuth disabled in dev mode")

    await enforce_login_rate_limit(request, scope="oauth")

    try:
        google_user = await get_google_user_info(code)
        email = google_user.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="Google account is missing an email")
        logger.info("Google OAuth successful for email: %s", mask_email(email))

        user = db.query(User).filter(User.email == email).first()

        if not user:
            user = User(
                google_id=google_user["id"],
                email=email,
                email_verified=google_user.get("verified_email", False),
                full_name=google_user.get("name"),
                picture_url=google_user.get("picture"),
                is_active=True,
                last_login_at=datetime.now(timezone.utc),
                role="user",
                is_admin=False,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info("Created new user id=%s", user.id)
        else:
            user.last_login_at = datetime.now(timezone.utc)
            user.full_name = google_user.get("name", user.full_name)
            user.picture_url = google_user.get("picture", user.picture_url)
            db.commit()
            logger.info("User logged in id=%s", user.id)

        _ensure_default_workspace(user, db)

        access_token = create_jwt_token(user.id, user.email)

        # Do not put the token in the redirect URL — leaks via referer/history/logs.
        # The HttpOnly cookie below carries the session; the SPA should call /me.
        response = RedirectResponse(url=settings.frontend_url, status_code=302)
        _set_auth_cookie(response, access_token)
        return response

    except HTTPException:
        raise
    except Exception as e:
        # Never leak the underlying exception text to the client.
        logger.exception("Google OAuth callback failed: %s", e)
        raise HTTPException(status_code=500, detail="Authentication failed")


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    user: User = Depends(_get_current_user_dep),
):
    """Return the current authenticated user.

    Auth comes from the shared dependency which reads either the
    ``Authorization: Bearer …`` header or the ``access_token`` cookie set
    by the login endpoints — keeping this route in sync with every other
    authenticated endpoint.
    """
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
        "last_login_at": user.last_login_at,
    }


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
        secure=settings.effective_cookie_secure,
        samesite=settings.cookie_samesite,
    )

    logger.info("User logged out")
    return response


@router.post("/dev-login")
async def dev_login(
    request: Request,
    payload: DevLoginRequest,
    db: Session = Depends(get_db),
):
    """Development-only login. Disabled outside debug/dev_auth_bypass mode."""
    # Hard gate: refuse if running in production-like mode.
    if settings.is_production or not (settings.debug or settings.dev_auth_bypass):
        raise HTTPException(status_code=404, detail="Not found")

    await enforce_login_rate_limit(request, scope="dev-login")

    email = payload.email.strip().lower()
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
    response = JSONResponse(
        content={
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.full_name,
                "role": user.role,
            },
        }
    )
    # Mirror the Google callback: drop the JWT into an HttpOnly cookie so
    # subsequent `api.me()` calls from the SPA carry credentials.
    _set_auth_cookie(response, access_token)
    return response
