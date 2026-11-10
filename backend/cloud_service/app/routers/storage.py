from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.storage import (
    StorageCreate, StorageUpdate, StorageResponse,
    StorageBatchCreate, StorageBatchDelete
)
from app.services.storage_service import StorageService
from app.middleware.auth import security, get_current_user
from app.utils.errors import error_response
from typing import List, Optional
import uuid

router = APIRouter(prefix="/api/storage", tags=["storage"])

@router.post("/{collection}", response_model=StorageResponse, status_code=status.HTTP_201_CREATED)
async def create_item(
    collection: str,
    item_data: StorageCreate,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Create a new item in a collection"""
    current_user = await get_current_user(request, credentials)
    
    item = StorageService.create(
        db,
        current_user["app_id"],
        current_user["user_id"],
        collection,
        item_data.data
    )
    
    return item

@router.get("/{collection}", response_model=List[StorageResponse])
async def list_items(
    collection: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    filter_field: Optional[str] = Query(None, description="Field name to filter by"),
    filter_value: Optional[str] = Query(None, description="Value to filter by"),
    sort: Optional[str] = Query(None, description="Field to sort by"),
    order: Optional[str] = Query('desc', description="Sort order: asc or desc"),
    limit: Optional[int] = Query(None, description="Max number of results"),
    offset: Optional[int] = Query(0, description="Number of results to skip"),
):
    """List items in a collection with optional filtering, sorting and pagination"""
    current_user = await get_current_user(request, credentials)

    items = StorageService.list(
        db,
        current_user["app_id"],
        current_user["user_id"],
        collection,
        filter_field=filter_field,
        filter_value=filter_value,
        sort_field=sort,
        sort_order=order,
        limit=limit,
        offset=offset
    )

    return items

@router.get("/{collection}/{item_id}", response_model=StorageResponse)
async def get_item(
    collection: str,
    item_id: uuid.UUID,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get a single item"""
    current_user = await get_current_user(request, credentials)
    
    item = StorageService.get(
        db,
        current_user["app_id"],
        current_user["user_id"],
        collection,
        item_id
    )
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("ITEM_NOT_FOUND", "Item not found")
        )
    
    return item

@router.put("/{collection}/{item_id}", response_model=StorageResponse)
async def update_item(
    collection: str,
    item_id: uuid.UUID,
    item_data: StorageUpdate,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Update an item"""
    current_user = await get_current_user(request, credentials)
    
    item = StorageService.update(
        db,
        current_user["app_id"],
        current_user["user_id"],
        collection,
        item_id,
        item_data.data
    )
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("ITEM_NOT_FOUND", "Item not found")
        )
    
    return item

@router.delete("/{collection}/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    collection: str,
    item_id: uuid.UUID,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Delete an item"""
    current_user = await get_current_user(request, credentials)
    
    success = StorageService.delete(
        db,
        current_user["app_id"],
        current_user["user_id"],
        collection,
        item_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("ITEM_NOT_FOUND", "Item not found")
        )
    
    return None

@router.post("/{collection}/batch", response_model=List[StorageResponse], status_code=status.HTTP_201_CREATED)
async def batch_create_items(
    collection: str,
    batch_data: StorageBatchCreate,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Create multiple items at once"""
    current_user = await get_current_user(request, credentials)
    
    items = StorageService.batch_create(
        db,
        current_user["app_id"],
        current_user["user_id"],
        collection,
        batch_data.items
    )
    
    return items

@router.delete("/{collection}/batch", status_code=status.HTTP_200_OK)
async def batch_delete_items(
    collection: str,
    batch_data: StorageBatchDelete,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Delete multiple items at once"""
    current_user = await get_current_user(request, credentials)
    
    deleted_count = StorageService.batch_delete(
        db,
        current_user["app_id"],
        current_user["user_id"],
        collection,
        batch_data.ids
    )
    
    return {"deleted": deleted_count}
