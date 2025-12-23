"""Product management routes."""
from fastapi import APIRouter, HTTPException, status, Depends, File, UploadFile, Form
from typing import List, Optional
import json
from app.models.product import Product, ProductCreate, ProductUpdate
from app.database.supabase_client import supabase
from app.dependencies import get_current_admin
from app.utils.cloudinary import upload_image

router = APIRouter(prefix="/api/products", tags=["Products"])

@router.get("", response_model=List[Product])
async def get_products(
    category_id: Optional[int] = None,
    scent: Optional[str] = None,
    admin: Optional[bool] = False
):
    """Get all products, optionally filtered by category, scent, and admin mode."""
    try:
        query = supabase.table("products").select("*, categories(*)")
        
        if category_id:
            query = query.eq("category_id", category_id)
        
        if scent:
            query = query.eq("scent", scent)
        
        # If not admin mode, only show active products
        if not admin:
            query = query.eq("is_active", True)
        
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
    quantity: Optional[int] = Form(0),
    is_active: Optional[str] = Form("true"),
    banner: Optional[str] = Form(None),
    discount_percentage: Optional[float] = Form(0),
    gallery_images: Optional[str] = Form(None),
    current_admin: dict = Depends(get_current_admin)
):
    """Create a new product (admin only)."""
    try:
        # Verify category exists and get category name
        category_response = supabase.table("categories").select("id, name").eq("id", category_id).execute()
        if not category_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        
        category_name = category_response.data[0]["name"]
        
        # Handle main image upload
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
        
        # Handle gallery images (from JSON string)
        gallery_images_list = []
        if gallery_images:
            try:
                gallery_images_list = json.loads(gallery_images)
            except:
                gallery_images_list = []
        
        # Parse is_active
        is_active_bool = is_active.lower() == "true" if is_active else True
        
        # Prepare product data
        product_data = {
            "name": name,
            "price": price,
            "category_id": category_id,
            "category": category_name,  # Required by database schema
            "description": description,
            "scent": scent,
            "image": image_url_final,
            "quantity": quantity or 0,
            "is_active": is_active_bool,
            "banner": banner,
            "discount_percentage": discount_percentage or 0,
            "gallery_images": gallery_images_list if gallery_images_list else None
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
    quantity: Optional[int] = Form(None),
    is_active: Optional[str] = Form(None),
    banner: Optional[str] = Form(None),
    discount_percentage: Optional[float] = Form(None),
    gallery_images: Optional[str] = Form(None),
    current_admin: dict = Depends(get_current_admin)
):
    """Update a product (admin only)."""
    try:
        # Verify category exists if provided and get category name
        category_name = None
        if category_id is not None:
            category_response = supabase.table("categories").select("id, name").eq("id", category_id).execute()
            if not category_response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Category not found"
                )
            category_name = category_response.data[0]["name"]
        
        # Handle main image upload
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
        
        # Handle gallery images (from JSON string)
        gallery_images_list = None
        if gallery_images is not None:
            if gallery_images == "":
                gallery_images_list = []
            else:
                try:
                    gallery_images_list = json.loads(gallery_images)
                except:
                    gallery_images_list = []
        
        # Prepare product data
        product_data = {}
        if name is not None:
            product_data["name"] = name
        if price is not None:
            product_data["price"] = price
        if category_id is not None:
            product_data["category_id"] = category_id
            # Update category name when category_id changes
            if category_name:
                product_data["category"] = category_name
        if description is not None:
            product_data["description"] = description
        if scent is not None:
            product_data["scent"] = scent
        if image_url_final is not None:
            product_data["image"] = image_url_final
        if quantity is not None:
            product_data["quantity"] = quantity
        if is_active is not None:
            product_data["is_active"] = is_active.lower() == "true"
        if banner is not None:
            product_data["banner"] = banner if banner else None
        if discount_percentage is not None:
            product_data["discount_percentage"] = discount_percentage
        if gallery_images_list is not None:
            product_data["gallery_images"] = gallery_images_list
        
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

