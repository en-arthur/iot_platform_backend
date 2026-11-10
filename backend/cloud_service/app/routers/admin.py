from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.app_service import AppService
from app.services.auth_service import AuthService
from app.services.storage_service import StorageService
from app.services.file_service import FileService
from app.middleware.auth import security, verify_admin_token
from app.utils.jwt import create_admin_token
from app.utils.errors import error_response
import uuid

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/apps/{app_id}/token")
async def get_admin_token(
    app_id: uuid.UUID,
    owner_id: str,
    db: Session = Depends(get_db)
):
    """Generate admin token for app owner (called server-side by WorkersCraft)"""
    app = AppService.get_app_by_id(db, app_id)
    if not app:
        raise HTTPException(status_code=404, detail=error_response("APP_NOT_FOUND", "App not found"))

    if str(app.owner_id) != owner_id:
        raise HTTPException(status_code=403, detail=error_response("FORBIDDEN", "Not the app owner"))

    token = create_admin_token(str(app_id), owner_id)
    return {"admin_token": token}


@router.get("/apps/{app_id}/users")
async def list_users(
    app_id: uuid.UUID,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """List all users for an app"""
    await verify_admin_token(app_id, credentials)
    users = AuthService.get_users_by_app(db, app_id)
    return {"users": [{"user_id": u.id, "email": u.email, "created_at": u.created_at, "is_active": u.is_active} for u in users]}


@router.get("/apps/{app_id}/storage")
async def list_storage(
    app_id: uuid.UUID,
    collection: str = None,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """List all storage records for an app, optionally filtered by collection"""
    await verify_admin_token(app_id, credentials)
    records = StorageService.get_all_by_app(db, app_id, collection)
    return {"records": [{"id": r.id, "user_id": r.user_id, "collection": r.collection, "data": r.data, "created_at": r.created_at} for r in records]}


@router.delete("/apps/{app_id}/users/{user_id}")
async def delete_user(
    app_id: uuid.UUID,
    user_id: uuid.UUID,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Delete a user from an app"""
    await verify_admin_token(app_id, credentials)
    success = AuthService.delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail=error_response("USER_NOT_FOUND", "User not found"))
    return {"success": True}


@router.delete("/apps/{app_id}/storage/{record_id}")
async def delete_record(
    app_id: uuid.UUID,
    record_id: uuid.UUID,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Delete a storage record"""
    await verify_admin_token(app_id, credentials)
    success = StorageService.delete_by_id(db, app_id, record_id)
    if not success:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", "Record not found"))
    return {"success": True}


@router.get("/apps/{app_id}/files")
async def list_files(
    app_id: uuid.UUID,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """List all files for an app"""
    await verify_admin_token(app_id, credentials)
    files = FileService.get_all_by_app(db, app_id)
    return {"files": [{"id": f.id, "user_id": f.user_id, "filename": f.filename, "mime_type": f.mime_type, "size_bytes": f.size_bytes, "url": f.url, "created_at": f.created_at} for f in files]}


@router.delete("/apps/{app_id}/files/{file_id}")
async def delete_file(
    app_id: uuid.UUID,
    file_id: uuid.UUID,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Delete a file"""
    await verify_admin_token(app_id, credentials)
    success = FileService.delete_by_id(db, app_id, file_id)
    if not success:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", "File not found"))
    return {"success": True}
