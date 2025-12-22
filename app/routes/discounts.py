"""Discount code management routes."""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from datetime import datetime
from app.models.discount import (
    DiscountCode, DiscountCodeCreate, DiscountCodeUpdate,
    DiscountValidationRequest, DiscountValidationResponse
)
from app.database.supabase_client import supabase
from app.dependencies import get_current_admin

router = APIRouter(prefix="/api/discounts", tags=["Discount Codes"])

@router.post("/validate", response_model=DiscountValidationResponse)
async def validate_discount_code(request: DiscountValidationRequest):
    """Validate a discount code and calculate discount."""
    try:
        code = request.code.upper().strip()
        total_amount = request.total_amount
        
        # Find active discount code
        response = supabase.table("discount_codes").select("*").eq("code", code).eq("is_active", True).execute()
        
        if not response.data:
            return DiscountValidationResponse(
                valid=False,
                message="Invalid or inactive discount code"
            )
        
        discount = response.data[0]
        
        # Check validity dates
        now = datetime.now()
        if discount.get("valid_from"):
            valid_from = datetime.fromisoformat(discount["valid_from"].replace("Z", "+00:00"))
            if now < valid_from:
                return DiscountValidationResponse(
                    valid=False,
                    message="Discount code is not yet valid"
                )
        
        if discount.get("valid_until"):
            valid_until = datetime.fromisoformat(discount["valid_until"].replace("Z", "+00:00"))
            if now > valid_until:
                return DiscountValidationResponse(
                    valid=False,
                    message="Discount code has expired"
                )
        
        # Check minimum purchase amount
        min_purchase = discount.get("min_purchase_amount", 0) or 0
        if total_amount < min_purchase:
            return DiscountValidationResponse(
                valid=False,
                message=f"Minimum purchase amount of ₹{min_purchase} required"
            )
        
        # Check usage limit
        usage_limit = discount.get("usage_limit")
        usage_count = discount.get("usage_count", 0) or 0
        if usage_limit and usage_count >= usage_limit:
            return DiscountValidationResponse(
                valid=False,
                message="Discount code has reached its usage limit"
            )
        
        # Calculate discount
        discount_percentage = discount.get("discount_percentage", 0) or 0
        discount_amount = (total_amount * discount_percentage) / 100
        
        # Apply max discount limit if set
        max_discount = discount.get("max_discount_amount")
        if max_discount and discount_amount > max_discount:
            discount_amount = max_discount
        
        final_amount = total_amount - discount_amount
        
        return DiscountValidationResponse(
            valid=True,
            discount_percentage=discount_percentage,
            discount_amount=discount_amount,
            final_amount=final_amount,
            message="Discount code applied successfully"
        )
    except Exception as e:
        return DiscountValidationResponse(
            valid=False,
            message=f"Error validating discount code: {str(e)}"
        )

@router.get("/featured", response_model=List[DiscountCode])
async def get_featured_discount_codes():
    """Get featured discount codes (public endpoint)."""
    try:
        now = datetime.now().isoformat()
        response = supabase.table("discount_codes").select("*").eq("is_active", True).eq("show_on_banner", True).execute()
        
        # Filter by date validity
        valid_codes = []
        for code in response.data:
            valid = True
            if code.get("valid_from"):
                if now < code["valid_from"]:
                    valid = False
            if code.get("valid_until"):
                if now > code["valid_until"]:
                    valid = False
            if valid:
                valid_codes.append(code)
        
        return valid_codes
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("", response_model=List[DiscountCode])
async def get_discount_codes(current_admin: dict = Depends(get_current_admin)):
    """Get all discount codes (admin only)."""
    try:
        response = supabase.table("discount_codes").select("*").order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("", response_model=DiscountCode, status_code=status.HTTP_201_CREATED)
async def create_discount_code(
    discount: DiscountCodeCreate,
    current_admin: dict = Depends(get_current_admin)
):
    """Create a new discount code (admin only)."""
    try:
        # Normalize code to uppercase
        discount_data = discount.dict()
        discount_data["code"] = discount_data["code"].upper().strip()
        
        # Check if code already exists
        existing = supabase.table("discount_codes").select("id").eq("code", discount_data["code"]).execute()
        if existing.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Discount code already exists"
            )
        
        response = supabase.table("discount_codes").insert(discount_data).execute()
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/{discount_id}", response_model=DiscountCode)
async def update_discount_code(
    discount_id: int,
    discount: DiscountCodeUpdate,
    current_admin: dict = Depends(get_current_admin)
):
    """Update a discount code (admin only)."""
    try:
        update_data = {k: v for k, v in discount.dict().items() if v is not None}
        
        # Normalize code if provided
        if "code" in update_data:
            update_data["code"] = update_data["code"].upper().strip()
            # Check if new code already exists (excluding current)
            existing = supabase.table("discount_codes").select("id").eq("code", update_data["code"]).neq("id", discount_id).execute()
            if existing.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Discount code already exists"
                )
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        update_data["updated_at"] = datetime.now().isoformat()
        
        response = supabase.table("discount_codes").update(update_data).eq("id", discount_id).execute()
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Discount code not found"
            )
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/{discount_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_discount_code(
    discount_id: int,
    current_admin: dict = Depends(get_current_admin)
):
    """Delete a discount code (admin only)."""
    try:
        response = supabase.table("discount_codes").delete().eq("id", discount_id).execute()
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Discount code not found"
            )
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

