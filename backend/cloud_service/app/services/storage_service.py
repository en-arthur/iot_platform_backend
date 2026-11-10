from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.storage import Storage
from app.models.file import File
from app.services.r2_service import r2_service
from typing import List, Optional
import uuid
from datetime import datetime
import re

# UUID pattern to detect file IDs embedded in URLs or data values
_UUID_RE = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', re.IGNORECASE)

def _extract_uuids(value) -> set:
    """Recursively extract all UUID strings from a JSONB value."""
    found = set()
    if isinstance(value, str):
        found.update(_UUID_RE.findall(value))
    elif isinstance(value, dict):
        for v in value.values():
            found.update(_extract_uuids(v))
    elif isinstance(value, list):
        for v in value:
            found.update(_extract_uuids(v))
    return found

def _cascade_delete_files(db: Session, app_id: uuid.UUID, data: dict):
    """Delete any files referenced in a storage record's data."""
    candidate_ids = _extract_uuids(data)
    if not candidate_ids:
        return
    try:
        parsed = [uuid.UUID(uid) for uid in candidate_ids]
    except ValueError:
        return
    files = db.query(File).filter(File.id.in_(parsed), File.app_id == app_id).all()
    for f in files:
        try:
            r2_service.delete_file(f.r2_key)
        except Exception:
            pass
        db.delete(f)
    if files:
        db.flush()


class StorageService:
    @staticmethod
    def create(db: Session, app_id: uuid.UUID, user_id: uuid.UUID, collection: str, data: dict) -> Storage:
        """Create a new storage item"""
        item = Storage(
            id=uuid.uuid4(),
            app_id=app_id,
            user_id=user_id,
            collection=collection,
            data=data
        )
        
        db.add(item)
        db.commit()
        db.refresh(item)
        return item
    
    @staticmethod
    def list(db: Session, app_id: uuid.UUID, user_id: uuid.UUID, collection: str,
             filter_field: str = None, filter_value: str = None,
             sort_field: str = None, sort_order: str = 'desc',
             limit: int = None, offset: int = 0) -> List[Storage]:
        """List items in a collection with optional filtering, sorting and pagination"""
        query = db.query(Storage).filter(
            and_(
                Storage.app_id == app_id,
                Storage.user_id == user_id,
                Storage.collection == collection
            )
        )

        # Filter by JSON field: data->>'field' = 'value'
        if filter_field and filter_value is not None:
            query = query.filter(
                Storage.data[filter_field].astext == str(filter_value)
            )

        # Sort by JSON field or created_at
        if sort_field:
            col = Storage.data[sort_field].astext
            query = query.order_by(col.asc() if sort_order == 'asc' else col.desc())
        else:
            query = query.order_by(Storage.created_at.desc() if sort_order == 'desc' else Storage.created_at.asc())

        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)

        return query.all()
    
    @staticmethod
    def get(db: Session, app_id: uuid.UUID, user_id: uuid.UUID, collection: str, item_id: uuid.UUID) -> Optional[Storage]:
        """Get a single item"""
        return db.query(Storage).filter(
            and_(
                Storage.id == item_id,
                Storage.app_id == app_id,
                Storage.user_id == user_id,
                Storage.collection == collection
            )
        ).first()
    
    @staticmethod
    def update(db: Session, app_id: uuid.UUID, user_id: uuid.UUID, collection: str, item_id: uuid.UUID, data: dict) -> Optional[Storage]:
        """Update an item"""
        item = StorageService.get(db, app_id, user_id, collection, item_id)
        
        if not item:
            return None
        
        item.data = data
        item.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(item)
        return item
    
    @staticmethod
    def delete(db: Session, app_id: uuid.UUID, user_id: uuid.UUID, collection: str, item_id: uuid.UUID) -> bool:
        """Delete an item and cascade-delete any referenced files."""
        item = StorageService.get(db, app_id, user_id, collection, item_id)
        if not item:
            return False
        _cascade_delete_files(db, app_id, item.data or {})
        db.delete(item)
        db.commit()
        return True
    
    @staticmethod
    def batch_create(db: Session, app_id: uuid.UUID, user_id: uuid.UUID, collection: str, items: List[dict]) -> List[Storage]:
        """Create multiple items at once"""
        storage_items = []
        
        for data in items:
            item = Storage(
                id=uuid.uuid4(),
                app_id=app_id,
                user_id=user_id,
                collection=collection,
                data=data
            )
            storage_items.append(item)
        
        db.add_all(storage_items)
        db.commit()
        
        for item in storage_items:
            db.refresh(item)
        
        return storage_items
    
    @staticmethod
    def get_all_by_app(db: Session, app_id: uuid.UUID, collection: str = None) -> List[Storage]:
        """Get all storage records for an app (admin)"""
        query = db.query(Storage).filter(Storage.app_id == app_id)
        if collection:
            query = query.filter(Storage.collection == collection)
        return query.order_by(Storage.created_at.desc()).all()

    @staticmethod
    def delete_by_id(db: Session, app_id: uuid.UUID, item_id: uuid.UUID) -> bool:
        """Delete a storage record by id (admin) and cascade-delete any referenced files."""
        item = db.query(Storage).filter(Storage.id == item_id, Storage.app_id == app_id).first()
        if not item:
            return False
        _cascade_delete_files(db, app_id, item.data or {})
        db.delete(item)
        db.commit()
        return True

    @staticmethod
    def batch_delete(db: Session, app_id: uuid.UUID, user_id: uuid.UUID, collection: str, item_ids: List[uuid.UUID]) -> int:
        """Delete multiple items at once"""
        deleted = db.query(Storage).filter(
            and_(
                Storage.id.in_(item_ids),
                Storage.app_id == app_id,
                Storage.user_id == user_id,
                Storage.collection == collection
            )
        ).delete(synchronize_session=False)
        
        db.commit()
        return deleted
