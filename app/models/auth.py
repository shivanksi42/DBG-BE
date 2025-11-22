"""Authentication-related Pydantic models."""
from pydantic import BaseModel

class LoginRequest(BaseModel):
    """Model for admin login."""
    username: str
    password: str

class LoginResponse(BaseModel):
    """Model for login response."""
    access_token: str
    token_type: str = "bearer"
    message: str = "Login successful"

class LogoutResponse(BaseModel):
    """Model for logout response."""
    message: str = "Logout successful"

