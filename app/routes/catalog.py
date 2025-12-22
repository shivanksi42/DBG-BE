"""Catalog management routes."""
from fastapi import APIRouter, HTTPException, status, Depends, File, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel
from typing import Optional
import os
from pathlib import Path
from app.dependencies import get_current_admin
from app.config import settings
from app.database.supabase_client import supabase

router = APIRouter(prefix="/api/catalog", tags=["Catalog"])

class CatalogLinkUpdate(BaseModel):
    """Model for updating catalog Google Drive link."""
    google_drive_link: str

def get_catalog_link():
    """Get catalog Google Drive link from database."""
    try:
        # Try to get catalog link from a settings table or use a simple key-value approach
        # For now, we'll use a simple approach: store in a 'catalog_settings' table
        # If table doesn't exist, we'll handle it gracefully
        response = supabase.table("catalog_settings").select("google_drive_link").limit(1).execute()
        if response.data and len(response.data) > 0:
            link = response.data[0].get("google_drive_link")
            if link:
                return link
    except Exception:
        # Table might not exist, that's okay - we'll fall back to file-based
        pass
    return None

def set_catalog_link(link: str):
    """Set catalog Google Drive link in database."""
    try:
        # Check if record exists
        existing = supabase.table("catalog_settings").select("id").limit(1).execute()
        
        if existing.data and len(existing.data) > 0:
            # Update existing record
            supabase.table("catalog_settings").update({"google_drive_link": link}).eq("id", existing.data[0]["id"]).execute()
        else:
            # Create new record
            supabase.table("catalog_settings").insert({"google_drive_link": link}).execute()
    except Exception as e:
        # If table doesn't exist, we could create it, but for now just raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save catalog link: {str(e)}. Please ensure 'catalog_settings' table exists in Supabase."
        )

def get_catalog_dirs():
    """Get possible catalog directory paths, prioritizing repository-based locations.
    
    The catalog folder should be placed at: DBG-BE/catalog/
    This will be included in the repository and available in Vercel deployments.
    """
    dirs = []
    
    # Priority 1: Catalog folder in DBG-BE directory (repository-based, best for Vercel)
    # Path: DBG-BE/catalog/
    # From app/routes/catalog.py: parent.parent.parent = DBG-BE directory
    repo_catalog_dir = Path(__file__).parent.parent.parent / "catalog"
    if repo_catalog_dir.exists():
        dirs.append(repo_catalog_dir)
    
    # Priority 2: Catalog folder at project root (if DBG-BE is in a parent directory)
    root_catalog_dir = Path(__file__).parent.parent.parent.parent / "catalog"
    if root_catalog_dir.exists():
        dirs.append(root_catalog_dir)
    
    # Priority 3: my-app/catalog directory (if catalog is in frontend folder)
    alt_catalog_dir = Path(__file__).parent.parent.parent.parent / "my-app" / "catalog"
    if alt_catalog_dir.exists():
        dirs.append(alt_catalog_dir)
    
    # Priority 4: For serverless environments, use /tmp (writable, but temporary)
    tmp_dir = Path("/tmp") / "catalog"
    if tmp_dir.exists():
        dirs.append(tmp_dir)
    
    return dirs

def get_upload_dir():
    """Get directory for uploading catalog files (writable location)."""
    # In serverless, use /tmp which is writable
    if os.path.exists("/tmp"):
        upload_dir = Path("/tmp") / "catalog"
        try:
            upload_dir.mkdir(parents=True, exist_ok=True)
            return upload_dir
        except:
            pass
    
    # Fallback to project directory if writable
    catalog_dir = Path(__file__).parent.parent.parent / "catalog"
    try:
        catalog_dir.mkdir(parents=True, exist_ok=True)
        return catalog_dir
    except:
        pass
    
    # Last resort: try my-app/catalog
    alt_catalog_dir = Path(__file__).parent.parent.parent.parent / "my-app" / "catalog"
    try:
        alt_catalog_dir.mkdir(parents=True, exist_ok=True)
        return alt_catalog_dir
    except:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cannot access writable directory for catalog uploads"
        )

@router.get("/download")
async def download_catalog():
    """Download the catalog PDF (public endpoint).
    
    Priority:
    1. Google Drive link (if set in database)
    2. Local PDF files in repository
    """
    try:
        # First, check for Google Drive link
        drive_link = get_catalog_link()
        if drive_link:
            # Convert Google Drive sharing link to direct download link
            # Format: https://drive.google.com/file/d/FILE_ID/view -> https://drive.google.com/uc?export=download&id=FILE_ID
            if "drive.google.com" in drive_link:
                # Extract file ID from various Google Drive link formats
                file_id = None
                if "/file/d/" in drive_link:
                    file_id = drive_link.split("/file/d/")[1].split("/")[0]
                elif "id=" in drive_link:
                    file_id = drive_link.split("id=")[1].split("&")[0]
                
                if file_id:
                    # Redirect to direct download link
                    direct_link = f"https://drive.google.com/uc?export=download&id={file_id}"
                    return RedirectResponse(url=direct_link, status_code=302)
                else:
                    # If we can't parse, just redirect to the original link
                    return RedirectResponse(url=drive_link, status_code=302)
            else:
                # Not a Google Drive link, redirect as-is
                return RedirectResponse(url=drive_link, status_code=302)
        
        # Fallback: Look for catalog file in all possible directories
        catalog_files = []
        for catalog_dir in get_catalog_dirs():
            if catalog_dir.exists():
                catalog_files.extend(list(catalog_dir.glob("*.pdf")))
        
        if not catalog_files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Catalog file not found. Please set a Google Drive link or add a PDF file to the catalog folder."
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
        # First, check for Google Drive link
        drive_link = get_catalog_link()
        if drive_link:
            return {
                "exists": True,
                "type": "google_drive",
                "link": drive_link,
                "message": "Catalog is available via Google Drive link"
            }
        
        # Fallback: Look for catalog file in all possible directories
        catalog_files = []
        for catalog_dir in get_catalog_dirs():
            if catalog_dir.exists():
                catalog_files.extend(list(catalog_dir.glob("*.pdf")))
        
        if not catalog_files:
            return {
                "exists": False,
                "message": "No catalog file found. Please set a Google Drive link or add a PDF file to the catalog folder."
            }
        
        # Get the most recent catalog file
        catalog_file = max(catalog_files, key=os.path.getctime)
        
        file_stats = catalog_file.stat()
        
        return {
            "exists": True,
            "type": "file",
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

@router.put("/link")
async def update_catalog_link(
    link_data: CatalogLinkUpdate,
    current_admin: dict = Depends(get_current_admin)
):
    """Update the catalog Google Drive link (admin only).
    
    This is the recommended approach for managing catalogs:
    - No need to store large PDF files in repository
    - Easy to update - just change the link
    - No redeployment needed when catalog changes
    """
    try:
        # Validate URL format
        link = link_data.google_drive_link.strip()
        if not link.startswith(("http://", "https://")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid URL format. Must start with http:// or https://"
            )
        
        # Save the link
        set_catalog_link(link)
        
        return {
            "message": "Catalog link updated successfully",
            "link": link,
            "note": "The catalog will now be served from this Google Drive link"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/link")
async def get_catalog_link_endpoint(current_admin: dict = Depends(get_current_admin)):
    """Get the current catalog Google Drive link (admin only)."""
    try:
        link = get_catalog_link()
        if link:
            return {
                "exists": True,
                "link": link
            }
        else:
            return {
                "exists": False,
                "message": "No catalog link set"
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
    """Upload a new catalog PDF (admin only).
    
    Note: In serverless environments (Vercel), uploaded files are temporary.
    For production, it's recommended to use Google Drive link instead (PUT /api/catalog/link).
    """
    try:
        # Validate file type
        if not file.filename.endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are allowed"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Get writable directory (for serverless, this will be /tmp)
        upload_dir = get_upload_dir()
        catalog_path = upload_dir / file.filename
        
        # If file exists, create backup or overwrite
        if catalog_path.exists():
            # Create backup with timestamp
            import shutil
            from datetime import datetime
            backup_name = f"{catalog_path.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            try:
                shutil.copy2(catalog_path, upload_dir / backup_name)
            except:
                pass  # If backup fails, just overwrite
        
        with open(catalog_path, "wb") as f:
            f.write(file_content)
        
        file_stats = catalog_path.stat()
        
        return {
            "message": "Catalog uploaded successfully",
            "filename": file.filename,
            "size": file_stats.st_size,
            "size_mb": round(file_stats.st_size / (1024 * 1024), 2),
            "warning": "In serverless environments, files stored in /tmp are temporary and will be lost. For production, use Google Drive link (PUT /api/catalog/link) instead."
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

