import logging
from datetime import datetime, timezone
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, status
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from ...core.config import get_settings
from ...core.db import User, get_db
from ...core.schemas import ErrorResponse, UserResponse
from ...core.security import (
    create_jwt_token,
    get_google_user_info,
    verify_jwt_token,
)

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


@router.get("/google/login", status_code=status.HTTP_302_FOUND)
async def google_login():
    """Redirect to Google OAuth login page."""
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
