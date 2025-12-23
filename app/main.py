"""Main FastAPI application entry point."""
from fastapi import FastAPI, Request, status as http_status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from datetime import datetime
from app.config import settings
from app.routes import auth, products, orders, categories, discounts, catalog

# Initialize FastAPI
app = FastAPI(
    title="Dori by Gouri API",
    description="API for Dori by Gouri e-commerce platform",
    version="2.0.0"
)

# CORS Configuration - must be added before exception handlers
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if settings.CORS_ORIGINS != ["*"] else ["*"],
    allow_credentials=False if "*" in settings.CORS_ORIGINS else True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Exception handlers to ensure CORS headers are always added
def get_cors_headers(request: Request) -> dict:
    """Get CORS headers based on request origin and settings."""
    origin = request.headers.get("origin")
    if origin and origin in settings.CORS_ORIGINS:
        allow_origin = origin
    elif "*" in settings.CORS_ORIGINS:
        allow_origin = "*"
    elif settings.CORS_ORIGINS:
        allow_origin = settings.CORS_ORIGINS[0]
    else:
        allow_origin = "*"
    
    headers = {
        "Access-Control-Allow-Origin": allow_origin,
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
        "Access-Control-Allow-Headers": "*",
    }
    
    if allow_origin != "*":
        headers["Access-Control-Allow-Credentials"] = "true"
    
    return headers

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with CORS headers."""
    headers = get_cors_headers(request)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=headers
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with CORS headers."""
    headers = get_cors_headers(request)
    return JSONResponse(
        status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
        headers=headers
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions with CORS headers."""
    headers = get_cors_headers(request)
    return JSONResponse(
        status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc)},
        headers=headers
    )

# Include routers
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(categories.router)
app.include_router(discounts.router)
app.include_router(catalog.router)

# Root endpoint
@app.get("/")
async def read_root():
    """Root endpoint."""
    return {"message": "Dori by Gouri API is running", "version": "2.0.0"}

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }

