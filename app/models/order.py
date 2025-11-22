"""Order-related Pydantic models."""
from pydantic import BaseModel, EmailStr
from typing import Optional

class OrderRequest(BaseModel):
    """Model for creating a new order."""
    product_name: str
    product_price: float
    customer_name: str
    customer_email: EmailStr
    customer_phone: str
    delivery_address: str
    quantity: int
    message: Optional[str] = None

