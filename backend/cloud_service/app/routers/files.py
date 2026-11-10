from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File as FastAPIFile
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.file import FileUploadResponse, FileListResponse
from app.services.file_service import FileService
from app.middleware.auth import security, get_current_user
from app.utils.errors import error_response
from typing import List
import uuid

router = APIRouter(prefix="/api/files", tags=["files"])

@router.post("/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    request: Request,
    file: UploadFile = FastAPIFile(...),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Upload a single file"""
    current_user = await get_current_user(request, credentials)
    
    # Read file data
    file_data = await file.read()
    size_bytes = len(file_data)
    
    # Validate file size (max 50MB)
    max_size = 50 * 1024 * 1024  # 50MB
    if size_bytes > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=error_response("FILE_TOO_LARGE", f"File size exceeds {max_size} bytes")
        )
    
    try:
        # Upload file
        from io import BytesIO
        file_record = FileService.upload_file(
            db,
            current_user["app_id"],
            current_user["user_id"],
            BytesIO(file_data),
            file.filename,
            file.content_type,
            size_bytes
        )
        
        return file_record
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response("UPLOAD_FAILED", str(e))
        )

@router.post("/upload/batch", response_model=List[FileUploadResponse], status_code=status.HTTP_201_CREATED)
async def upload_files(
    request: Request,
    files: List[UploadFile] = FastAPIFile(...),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Upload multiple files"""
    current_user = await get_current_user(request, credentials)
    
    # Validate number of files (max 10)
    if len(files) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response("TOO_MANY_FILES", "Maximum 10 files per batch")
        )
    
    try:
        from io import BytesIO
        files_data = []
        
        for file in files:
            file_data = await file.read()
            size_bytes = len(file_data)
            
            # Validate each file size
            max_size = 50 * 1024 * 1024
            if size_bytes > max_size:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=error_response("FILE_TOO_LARGE", f"File {file.filename} exceeds size limit")
                )
            
            files_data.append((
                BytesIO(file_data),
                file.filename,
                file.content_type,
                size_bytes
            ))
        
        # Upload all files
        uploaded = FileService.batch_upload(
            db,
            current_user["app_id"],
            current_user["user_id"],
            files_data
        )
        
        return uploaded
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response("UPLOAD_FAILED", str(e))
        )

@router.get("", response_model=List[FileListResponse])
async def list_files(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """List all user's files"""
    current_user = await get_current_user(request, credentials)
    
    files = FileService.list_files(
        db,
        current_user["app_id"],
        current_user["user_id"]
    )
    
    return files

@router.get("/{file_id}", response_model=FileUploadResponse)
async def get_file(
    file_id: uuid.UUID,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get file metadata"""
    current_user = await get_current_user(request, credentials)
    
    file_record = FileService.get_file(
        db,
        current_user["app_id"],
        current_user["user_id"],
        file_id
    )
    
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("FILE_NOT_FOUND", "File not found")
        )
    
    return file_record

@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: uuid.UUID,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Delete a file"""
    current_user = await get_current_user(request, credentials)
    
    success = FileService.delete_file(
        db,
        current_user["app_id"],
        current_user["user_id"],
        file_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("FILE_NOT_FOUND", "File not found")
        )
    
    return None
