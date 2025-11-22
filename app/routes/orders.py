"""Order management routes."""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from app.models.order import OrderRequest
from app.database.supabase_client import supabase
from app.dependencies import get_current_admin
from app.config import settings
import resend

router = APIRouter(prefix="/api/orders", tags=["Orders"])

# Initialize Resend
resend.api_key = settings.RESEND_API_KEY

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_order(order: OrderRequest):
    """Create a new order."""
    try:
        # Calculate total
        total = order.product_price * order.quantity
        
        # Save to database
        order_data = {
            **order.dict(),
            "total": total,
            "status": "pending"
        }
        db_response = supabase.table("orders").insert(order_data).execute()
        
        # Send email to owner using Resend
        email_content = f"""
        <h2>New Order Request</h2>
        <h3>Product Details</h3>
        <p><strong>Product:</strong> {order.product_name}</p>
        <p><strong>Price:</strong> ₹{order.product_price}</p>
        <p><strong>Quantity:</strong> {order.quantity}</p>
        <p><strong>Total:</strong> ₹{total}</p>
        
        <h3>Customer Details</h3>
        <p><strong>Name:</strong> {order.customer_name}</p>
        <p><strong>Email:</strong> {order.customer_email}</p>
        <p><strong>Phone:</strong> {order.customer_phone}</p>
        <p><strong>Address:</strong> {order.delivery_address}</p>
        
        {f'<p><strong>Message:</strong> {order.message}</p>' if order.message else ''}
        
        <p><em>Please contact the customer to confirm the order.</em></p>
        """
        
        resend.Emails.send({
            "from": "orders@yourdomain.com",  # Replace with your verified domain
            "to": settings.OWNER_EMAIL,
            "subject": f"New Order: {order.product_name} - {order.customer_name}",
            "html": email_content
        })
        
        return {
            "message": "Order request sent successfully",
            "order_id": db_response.data[0]["id"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("", response_model=List[dict])
async def get_orders(
    status_filter: Optional[str] = None,
    current_admin: dict = Depends(get_current_admin)
):
    """Get all orders (admin only)."""
    try:
        query = supabase.table("orders").select("*").order("created_at", desc=True)
        if status_filter:
            query = query.eq("status", status_filter)
        response = query.execute()
        return response.data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

