"""Category management routes."""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from app.models.category import Category, CategoryCreate, CategoryUpdate
from app.database.supabase_client import supabase
from app.dependencies import get_current_admin

router = APIRouter(prefix="/api/categories", tags=["Categories"])

@router.get("", response_model=List[Category])
async def get_categories():
    """Get all categories."""
    try:
        response = supabase.table("categories").select("*").order("name").execute()
        return response.data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{category_id}", response_model=Category)
async def get_category(category_id: int):
    """Get a specific category by ID."""
    try:
        response = supabase.table("categories").select("*").eq("id", category_id).execute()
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("", response_model=Category, status_code=status.HTTP_201_CREATED)
async def create_category(
    category: CategoryCreate,
    current_admin: dict = Depends(get_current_admin)
):
    """Create a new category (admin only)."""
    try:
        response = supabase.table("categories").insert(category.dict()).execute()
        return response.data[0]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/{category_id}", response_model=Category)
async def update_category(
    category_id: int,
    category: CategoryUpdate,
    current_admin: dict = Depends(get_current_admin)
):
    """Update a category (admin only)."""
    try:
        # Remove None values
        update_data = {k: v for k, v in category.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        response = supabase.table("categories").update(update_data).eq("id", category_id).execute()
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    current_admin: dict = Depends(get_current_admin)
):
    """Delete a category (admin only)."""
    try:
        # Check if category is used by any products
        products_response = supabase.table("products").select("id").eq("category_id", category_id).limit(1).execute()
        if products_response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete category that is in use by products"
            )
        
        response = supabase.table("categories").delete().eq("id", category_id).execute()
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

