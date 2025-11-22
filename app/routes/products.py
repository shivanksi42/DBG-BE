"""Product management routes."""
from fastapi import APIRouter, HTTPException, status, Depends, File, UploadFile, Form
from typing import List, Optional
from app.models.product import Product, ProductCreate, ProductUpdate
from app.database.supabase_client import supabase
from app.dependencies import get_current_admin
from app.utils.cloudinary import upload_image

router = APIRouter(prefix="/api/products", tags=["Products"])

@router.get("", response_model=List[Product])
async def get_products(category_id: Optional[int] = None):
    """Get all products, optionally filtered by category."""
    try:
        query = supabase.table("products").select("*, categories(*)")
        if category_id:
            query = query.eq("category_id", category_id)
        response = query.order("created_at").execute()
        # Reverse the list to get newest first (Supabase orders ascending by default)
        if response.data:
            response.data.reverse()
        return response.data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{product_id}", response_model=Product)
async def get_product(product_id: int):
    """Get a specific product by ID."""
    try:
        response = supabase.table("products").select("*, categories(*)").eq("id", product_id).execute()
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("", response_model=Product, status_code=status.HTTP_201_CREATED)
async def create_product(
    name: str = Form(...),
    price: float = Form(...),
    category_id: int = Form(...),
    description: Optional[str] = Form(None),
    scent: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    image_url: Optional[str] = Form(None),
    current_admin: dict = Depends(get_current_admin)
):
    """Create a new product (admin only)."""
    try:
        # Verify category exists
        category_response = supabase.table("categories").select("id").eq("id", category_id).execute()
        if not category_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        
        # Handle image upload
        image_url_final = image_url
        
        if image and image.filename:
            try:
                image_bytes = await image.read()
                image_url_final = upload_image(image_bytes)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Image upload failed: {str(e)}"
                )
        
        # Prepare product data
        product_data = {
            "name": name,
            "price": price,
            "category_id": category_id,
            "description": description,
            "scent": scent,
            "image": image_url_final
        }
        
        response = supabase.table("products").insert(product_data).execute()
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/{product_id}", response_model=Product)
async def update_product(
    product_id: int,
    name: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    category_id: Optional[int] = Form(None),
    description: Optional[str] = Form(None),
    scent: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    image_url: Optional[str] = Form(None),
    current_admin: dict = Depends(get_current_admin)
):
    """Update a product (admin only)."""
    try:
        # Verify category exists if provided
        if category_id is not None:
            category_response = supabase.table("categories").select("id").eq("id", category_id).execute()
            if not category_response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Category not found"
                )
        
        # Handle image upload
        image_url_final = image_url
        
        if image and image.filename:
            try:
                image_bytes = await image.read()
                image_url_final = upload_image(image_bytes)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Image upload failed: {str(e)}"
                )
        
        # Prepare product data
        product_data = {}
        if name is not None:
            product_data["name"] = name
        if price is not None:
            product_data["price"] = price
        if category_id is not None:
            product_data["category_id"] = category_id
        if description is not None:
            product_data["description"] = description
        if scent is not None:
            product_data["scent"] = scent
        if image_url_final is not None:
            product_data["image"] = image_url_final
        
        if not product_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        response = supabase.table("products").update(product_data).eq("id", product_id).execute()
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    current_admin: dict = Depends(get_current_admin)
):
    """Delete a product (admin only)."""
    try:
        response = supabase.table("products").delete().eq("id", product_id).execute()
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

