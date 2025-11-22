"""Product-related Pydantic models."""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ProductBase(BaseModel):
    """Base product model with common fields."""
    name: str
    price: float
    category_id: int
    description: Optional[str] = None
    scent: Optional[str] = None
    image: Optional[str] = None

class ProductCreate(ProductBase):
    """Model for creating a new product."""
    pass

class ProductUpdate(BaseModel):
    """Model for updating a product."""
    name: Optional[str] = None
    price: Optional[float] = None
    category_id: Optional[int] = None
    description: Optional[str] = None
    scent: Optional[str] = None
    image: Optional[str] = None

class Product(ProductBase):
    """Product model with all fields including ID and timestamps."""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

