"""Authentication service for admin operations."""
from fastapi import HTTPException, status
from app.config import settings
from app.utils.jwt import create_access_token
from datetime import timedelta

def authenticate_admin(username: str, password: str) -> bool:
    """Authenticate admin credentials."""
    if username == settings.ADMIN_USERNAME and password == settings.ADMIN_PASSWORD:
        return True
    return False

def login_admin(username: str, password: str) -> str:
    """Login admin and return JWT token."""
    if not authenticate_admin(username, password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": username, "role": "admin"},
        expires_delta=access_token_expires
    )
    
    return access_token

