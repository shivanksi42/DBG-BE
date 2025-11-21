from fastapi import FastAPI, HTTPException, Depends, Response, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
import os
from supabase import create_client, Client
import resend
import cloudinary
import cloudinary.uploader

# Initialize FastAPI
app = FastAPI(title="Dori by Gouri API")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend domain
    allow_credentials=False,  # Must be False when allow_origins=["*"]
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Environment Variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
OWNER_EMAIL = "shivam@yopmail.com"

# Cloudinary Configuration
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

# Initialize Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize Resend
resend.api_key = RESEND_API_KEY

# Initialize Cloudinary
cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET
)

# Pydantic Models
class Product(BaseModel):
    id: Optional[int] = None
    name: str
    price: float
    category: str
    description: Optional[str] = None
    image: Optional[str] = None
    created_at: Optional[datetime] = None

class ProductCreate(BaseModel):
    name: str
    price: float
    category: str
    description: Optional[str] = None
    image: Optional[str] = None
    password: Optional[str] = None  # For admin authentication

class OrderRequest(BaseModel):
    product_name: str
    product_price: float
    customer_name: str
    customer_email: EmailStr
    customer_phone: str
    delivery_address: str
    quantity: int
    message: Optional[str] = None

class AdminAuth(BaseModel):
    password: str


"""
CREATE TABLE products (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    image TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE orders (
    id BIGSERIAL PRIMARY KEY,
    product_name TEXT NOT NULL,
    product_price DECIMAL(10, 2) NOT NULL,
    customer_name TEXT NOT NULL,
    customer_email TEXT NOT NULL,
    customer_phone TEXT NOT NULL,
    delivery_address TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    message TEXT,
    total DECIMAL(10, 2) NOT NULL,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
"""

def verify_admin(password: str):
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid admin password")
    return True

# Routes
@app.get("/")
def read_root():
    return {"message": "Dori by Gouri API is running"}

# Product Routes
@app.get("/products", response_model=List[Product])
@app.get("/api/products", response_model=List[Product])
def get_products(category: Optional[str] = None):
    try:
        query = supabase.table("products").select("*")
        if category:
            query = query.eq("category", category)
        response = query.execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/products/{product_id}", response_model=Product)
def get_product(product_id: int):
    try:
        response = supabase.table("products").select("*").eq("id", product_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Product not found")
        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Explicit OPTIONS handlers for CORS preflight (must be before POST routes)
@app.options("/products")
@app.options("/api/products")
async def options_products():
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Max-Age": "3600",
        }
    )

@app.post("/products", response_model=Product)
@app.post("/api/products", response_model=Product)
async def create_product(
    name: str = Form(...),
    price: float = Form(...),
    category: str = Form(...),
    description: Optional[str] = Form(None),
    password: str = Form(...),
    image: Optional[UploadFile] = File(None),
    image_url: Optional[str] = Form(None)  # For backward compatibility
):
    # Verify admin
    if not password:
        raise HTTPException(status_code=401, detail="Admin password required")
    verify_admin(password)
    
    # Handle image upload
    image_url_final = image_url  # Use provided URL if available
    
    if image and image.filename:
        try:
            # Read image file
            image_bytes = await image.read()
            
            # Upload to Cloudinary
            upload_result = cloudinary.uploader.upload(
                image_bytes,
                folder="dori-products",  # Organize images in a folder
                resource_type="image"
            )
            image_url_final = upload_result.get("secure_url")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")
    
    # Prepare product data
    product_data = {
        "name": name,
        "price": price,
        "category": category,
        "description": description,
        "image": image_url_final
    }
    
    try:
        response = supabase.table("products").insert(product_data).execute()
        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/products/{product_id}", response_model=Product)
@app.put("/api/products/{product_id}", response_model=Product)
async def update_product(
    product_id: int,
    name: str = Form(...),
    price: float = Form(...),
    category: str = Form(...),
    description: Optional[str] = Form(None),
    password: str = Form(...),
    image: Optional[UploadFile] = File(None),
    image_url: Optional[str] = Form(None)  # For backward compatibility
):
    # Verify admin
    if not password:
        raise HTTPException(status_code=401, detail="Admin password required")
    verify_admin(password)
    
    # Handle image upload
    image_url_final = image_url  # Use provided URL if available
    
    if image and image.filename:
        try:
            # Read image file
            image_bytes = await image.read()
            
            # Upload to Cloudinary
            upload_result = cloudinary.uploader.upload(
                image_bytes,
                folder="dori-products",  # Organize images in a folder
                resource_type="image"
            )
            image_url_final = upload_result.get("secure_url")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")
    
    # Prepare product data
    product_data = {
        "name": name,
        "price": price,
        "category": category,
        "description": description
    }
    
    # Only update image if a new one was provided
    if image_url_final is not None:
        product_data["image"] = image_url_final
    
    try:
        response = supabase.table("products").update(product_data).eq("id", product_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Product not found")
        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/products/{product_id}")
@app.delete("/api/products/{product_id}")
def delete_product(product_id: int, auth: AdminAuth):
    verify_admin(auth.password)
    try:
        response = supabase.table("products").delete().eq("id", product_id).execute()
        return {"message": "Product deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Order Routes
@app.options("/api/orders")
async def options_orders():
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Max-Age": "3600",
        }
    )

@app.post("/api/orders")
async def create_order(order: OrderRequest):
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
            "to": OWNER_EMAIL,
            "subject": f"New Order: {order.product_name} - {order.customer_name}",
            "html": email_content
        })
        
        return {
            "message": "Order request sent successfully",
            "order_id": db_response.data[0]["id"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/orders")
def get_orders(auth: AdminAuth, status: Optional[str] = None):
    verify_admin(auth.password)
    try:
        query = supabase.table("orders").select("*").order("created_at", desc=True)
        if status:
            query = query.eq("status", status)
        response = query.execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/categories")
def get_categories():
    try:
        response = supabase.table("products").select("category").execute()
        categories = list(set([item["category"] for item in response.data]))
        return {"categories": categories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health Check
@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Catch-all OPTIONS handler for any other routes
@app.options("/{full_path:path}")
async def options_catch_all(full_path: str):
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Max-Age": "3600",
        }
    )