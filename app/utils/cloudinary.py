"""Cloudinary configuration and utilities."""
import cloudinary
import cloudinary.uploader
from urllib.parse import urlparse
from app.config import settings

def init_cloudinary():
    """Initialize Cloudinary with configuration from environment variables."""
    if settings.CLOUDINARY_URL:
        # Parse the Cloudinary URL: cloudinary://api_key:api_secret@cloud_name
        parsed = urlparse(settings.CLOUDINARY_URL)
        cloudinary.config(
            cloud_name=parsed.hostname,
            api_key=parsed.username,
            api_secret=parsed.password
        )
    else:
        # Fallback to individual environment variables
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET
        )

def upload_image(image_bytes: bytes, folder: str = "dori-products") -> str:
    """Upload an image to Cloudinary and return the secure URL."""
    upload_result = cloudinary.uploader.upload(
        image_bytes,
        folder=folder,
        resource_type="image"
    )
    return upload_result.get("secure_url")

# Initialize Cloudinary on module import
init_cloudinary()

