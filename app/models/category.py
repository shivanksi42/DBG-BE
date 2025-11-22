"""Category-related Pydantic models."""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CategoryBase(BaseModel):
    """Base category model."""
    name: str
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    """Model for creating a new category."""
    pass

class CategoryUpdate(BaseModel):
    """Model for updating a category."""
    name: Optional[str] = None
    description: Optional[str] = None

class Category(CategoryBase):
    """Category model with all fields including ID and timestamps."""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

