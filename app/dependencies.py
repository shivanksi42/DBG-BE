"""FastAPI dependencies for authentication and authorization."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.utils.jwt import verify_token
from app.config import settings

security = HTTPBearer()

def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Dependency to verify admin authentication via JWT token."""
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username: str = payload.get("sub")
    role: str = payload.get("role")
    
    if username is None or role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return {"username": username, "role": role}

