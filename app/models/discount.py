"""Discount code-related Pydantic models."""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DiscountCodeBase(BaseModel):
    """Base discount code model."""
    code: str
    discount_percentage: float
    min_purchase_amount: Optional[float] = 0
    max_discount_amount: Optional[float] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    is_active: bool = True
    show_on_banner: bool = False
    usage_limit: Optional[int] = None
    usage_count: int = 0

class DiscountCodeCreate(DiscountCodeBase):
    """Model for creating a new discount code."""
    pass

class DiscountCodeUpdate(BaseModel):
    """Model for updating a discount code."""
    code: Optional[str] = None
    discount_percentage: Optional[float] = None
    min_purchase_amount: Optional[float] = None
    max_discount_amount: Optional[float] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    is_active: Optional[bool] = None
    show_on_banner: Optional[bool] = None
    usage_limit: Optional[int] = None
    usage_count: Optional[int] = None

class DiscountCode(DiscountCodeBase):
    """Discount code model with all fields including ID and timestamps."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class DiscountValidationRequest(BaseModel):
    """Model for validating a discount code."""
    code: str
    total_amount: float

class DiscountValidationResponse(BaseModel):
    """Model for discount validation response."""
    valid: bool
    discount_percentage: Optional[float] = None
    discount_amount: Optional[float] = None
    final_amount: Optional[float] = None
    message: Optional[str] = None

