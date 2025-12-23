"""Order management routes."""
from fastapi import APIRouter, HTTPException, status, Depends, Response
from fastapi.responses import StreamingResponse
from typing import List, Optional
from datetime import datetime
from app.models.order import OrderRequest
from app.database.supabase_client import supabase
from app.dependencies import get_current_admin
from app.config import settings
import resend
import csv
import io

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
        
        # Send email to owner using Resend (optional - order is saved even if email fails)
        if settings.RESEND_API_KEY:
            try:
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
                    "from": settings.RESEND_FROM_EMAIL,
                    "to": settings.OWNER_EMAIL,
                    "subject": f"New Order: {order.product_name} - {order.customer_name}",
                    "html": email_content
                })
            except Exception as email_error:
                # Log email error but don't fail the order creation
                # In production, you might want to log this to a monitoring service
                print(f"Failed to send order notification email: {str(email_error)}")
                # Order is still created successfully
        
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
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_admin: dict = Depends(get_current_admin)
):
    """Get all orders (admin only) with optional filters."""
    try:
        query = supabase.table("orders").select("*").order("created_at", desc=True)
        
        if status_filter:
            query = query.eq("status", status_filter)
        
        if start_date:
            query = query.gte("created_at", start_date)
        
        if end_date:
            query = query.lte("created_at", end_date)
        
        response = query.execute()
        return response.data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/stats")
async def get_order_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_admin: dict = Depends(get_current_admin)
):
    """Get order statistics (admin only)."""
    try:
        query = supabase.table("orders").select("*")
        
        if start_date:
            query = query.gte("created_at", start_date)
        
        if end_date:
            query = query.lte("created_at", end_date)
        
        response = query.execute()
        orders = response.data
        
        # Calculate statistics
        total_orders = len(orders)
        total_revenue = sum(float(order.get("total", 0) or 0) for order in orders)
        
        # Status breakdown
        status_counts = {}
        for order in orders:
            status = order.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Average order value
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
        
        return {
            "total_orders": total_orders,
            "total_revenue": round(total_revenue, 2),
            "average_order_value": round(avg_order_value, 2),
            "status_breakdown": status_counts
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.patch("/{order_id}/status")
async def update_order_status(
    order_id: int,
    status: str,
    current_admin: dict = Depends(get_current_admin)
):
    """Update order status (admin only)."""
    try:
        valid_statuses = ["pending", "confirmed", "processing", "shipped", "delivered", "cancelled"]
        if status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        
        response = supabase.table("orders").update({"status": status}).eq("id", order_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/{order_id}")
async def update_order(
    order_id: int,
    order_data: dict,
    current_admin: dict = Depends(get_current_admin)
):
    """Update an order (admin only)."""
    try:
        # Remove None values
        update_data = {k: v for k, v in order_data.items() if v is not None}
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        response = supabase.table("orders").update(update_data).eq("id", order_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(
    order_id: int,
    current_admin: dict = Depends(get_current_admin)
):
    """Delete an order (admin only)."""
    try:
        response = supabase.table("orders").delete().eq("id", order_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("")
async def delete_orders_by_date_range(
    start_date: str,
    end_date: str,
    current_admin: dict = Depends(get_current_admin)
):
    """Delete orders within a date range (admin only)."""
    try:
        query = supabase.table("orders").select("*")
        
        if start_date:
            query = query.gte("created_at", start_date)
        
        if end_date:
            query = query.lte("created_at", end_date)
        
        # Get orders to be deleted
        response = query.execute()
        order_ids = [order["id"] for order in response.data]
        
        if not order_ids:
            return {
                "message": "No orders found in the specified date range",
                "deleted_count": 0
            }
        
        # Delete orders
        for order_id in order_ids:
            supabase.table("orders").delete().eq("id", order_id).execute()
        
        return {
            "message": f"Successfully deleted {len(order_ids)} orders",
            "deleted_count": len(order_ids)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/export/excel")
async def export_orders_excel(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_admin: dict = Depends(get_current_admin)
):
    """Export orders to CSV/Excel format (admin only)."""
    try:
        query = supabase.table("orders").select("*").order("created_at", desc=True)
        
        if start_date:
            query = query.gte("created_at", start_date)
        
        if end_date:
            query = query.lte("created_at", end_date)
        
        response = query.execute()
        orders = response.data
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        if orders:
            headers = list(orders[0].keys())
            writer.writerow(headers)
            
            # Write data
            for order in orders:
                writer.writerow([order.get(header, "") for header in headers])
        else:
            # Empty CSV with common headers
            writer.writerow([
                "id", "product_name", "product_price", "quantity", "total",
                "customer_name", "customer_email", "customer_phone",
                "delivery_address", "status", "message", "created_at"
            ])
        
        output.seek(0)
        
        # Return as CSV file
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=orders_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

