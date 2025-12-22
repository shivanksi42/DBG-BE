"""Catalog management routes."""
from fastapi import APIRouter, HTTPException, status, Depends, File, UploadFile
from fastapi.responses import FileResponse
from typing import Optional
import os
from pathlib import Path
from app.dependencies import get_current_admin
from app.config import settings

router = APIRouter(prefix="/api/catalog", tags=["Catalog"])

# Catalog directory - adjust path as needed
CATALOG_DIR = Path(__file__).parent.parent.parent / "catalog"
CATALOG_DIR.mkdir(exist_ok=True)

@router.get("/download")
async def download_catalog():
    """Download the catalog PDF (public endpoint)."""
    try:
        # Look for catalog file
        catalog_files = list(CATALOG_DIR.glob("*.pdf"))
        if not catalog_files:
            # Try looking in my-app/catalog directory
            alt_catalog_dir = Path(__file__).parent.parent.parent.parent / "my-app" / "catalog"
            if alt_catalog_dir.exists():
                catalog_files = list(alt_catalog_dir.glob("*.pdf"))
        
        if not catalog_files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Catalog file not found"
            )
        
        # Get the most recent catalog file
        catalog_file = max(catalog_files, key=os.path.getctime)
        
        return FileResponse(
            path=str(catalog_file),
            filename=catalog_file.name,
            media_type="application/pdf"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/info")
async def get_catalog_info():
    """Get catalog file information (public endpoint)."""
    try:
        # Look for catalog file
        catalog_files = list(CATALOG_DIR.glob("*.pdf"))
        if not catalog_files:
            # Try looking in my-app/catalog directory
            alt_catalog_dir = Path(__file__).parent.parent.parent.parent / "my-app" / "catalog"
            if alt_catalog_dir.exists():
                catalog_files = list(alt_catalog_dir.glob("*.pdf"))
        
        if not catalog_files:
            return {
                "exists": False,
                "message": "No catalog file found"
            }
        
        # Get the most recent catalog file
        catalog_file = max(catalog_files, key=os.path.getctime)
        
        file_stats = catalog_file.stat()
        
        return {
            "exists": True,
            "filename": catalog_file.name,
            "size": file_stats.st_size,
            "size_mb": round(file_stats.st_size / (1024 * 1024), 2),
            "created_at": file_stats.st_ctime,
            "modified_at": file_stats.st_mtime
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/upload")
async def upload_catalog(
    file: UploadFile = File(...),
    current_admin: dict = Depends(get_current_admin)
):
    """Upload a new catalog PDF (admin only)."""
    try:
        # Validate file type
        if not file.filename.endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are allowed"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Save file
        catalog_path = CATALOG_DIR / file.filename
        
        # If file exists, create backup or overwrite
        if catalog_path.exists():
            # Create backup with timestamp
            import shutil
            from datetime import datetime
            backup_name = f"{catalog_path.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            shutil.copy2(catalog_path, CATALOG_DIR / backup_name)
        
        with open(catalog_path, "wb") as f:
            f.write(file_content)
        
        file_stats = catalog_path.stat()
        
        return {
            "message": "Catalog uploaded successfully",
            "filename": file.filename,
            "size": file_stats.st_size,
            "size_mb": round(file_stats.st_size / (1024 * 1024), 2)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

