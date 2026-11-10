from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.app import AppCreate, AppResponse, AppWithId
from app.services.app_service import AppService
from app.utils.errors import error_response
from typing import List
import uuid

router = APIRouter(prefix="/api/apps", tags=["apps"])

@router.post("/register", response_model=AppWithId, status_code=status.HTTP_201_CREATED)
async def register_app(
    app_data: AppCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new app (called by WorkersCraft when project created with backend)
    """
    try:
        app = AppService.create_app(db, app_data)
        return {"app_id": app.id}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error_response("DUPLICATE_APP", str(e))
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response("INTERNAL_ERROR", "Failed to create app")
        )

@router.get("/{app_id}", response_model=AppResponse)
async def get_app(
    app_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Get app details"""
    app = AppService.get_app_by_id(db, app_id)
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("APP_NOT_FOUND", "App not found")
        )
    return app

@router.get("/owner/{owner_id}", response_model=List[AppResponse])
async def get_owner_apps(
    owner_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Get all apps for an owner"""
    apps = AppService.get_apps_by_owner(db, owner_id)
    return apps

@router.delete("/{app_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_app(
    app_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Deactivate an app"""
    success = AppService.deactivate_app(db, app_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("APP_NOT_FOUND", "App not found")
        )
    return None
