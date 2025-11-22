"""Main FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from app.config import settings
from app.routes import auth, products, orders, categories

# Initialize FastAPI
app = FastAPI(
    title="Dori by Gouri API",
    description="API for Dori by Gouri e-commerce platform",
    version="2.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if settings.CORS_ORIGINS != ["*"] else ["*"],
    allow_credentials=False if "*" in settings.CORS_ORIGINS else True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(categories.router)

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

