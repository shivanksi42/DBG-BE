"""Authentication routes for admin login/logout."""
from fastapi import APIRouter, HTTPException, status
from app.models.auth import LoginRequest, LoginResponse, LogoutResponse
from app.services.auth_service import login_admin

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    """Login endpoint for admin authentication."""
    try:
        access_token = login_admin(login_data.username, login_data.password)
        return LoginResponse(access_token=access_token)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@router.post("/logout", response_model=LogoutResponse)
async def logout():
    """Logout endpoint (client should discard token)."""
    # Since we're using stateless JWT, logout is handled client-side
    # In a production system with token blacklisting, you'd invalidate the token here
    return LogoutResponse()

