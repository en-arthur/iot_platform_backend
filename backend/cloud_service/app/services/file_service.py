from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.file import File
from app.services.r2_service import r2_service
from typing import List, Optional, BinaryIO
import uuid

class FileService:
    @staticmethod
    def upload_file(
        db: Session,
        app_id: uuid.UUID,
        user_id: uuid.UUID,
        file_data: BinaryIO,
        filename: str,
        content_type: str,
        size_bytes: int,
        metadata: dict = None
    ) -> File:
        """Upload file to R2 and save metadata to database"""
        # Upload to R2
        r2_result = r2_service.upload_file(
            file_data,
            filename,
            app_id,
            user_id,
            content_type
        )
        
        # Save metadata to database
        file_record = File(
            id=uuid.uuid4(),
            app_id=app_id,
            user_id=user_id,
            filename=filename,
            r2_key=r2_result["key"],
            mime_type=content_type,
            size_bytes=size_bytes,
            url=r2_result["url"],
            metadata=metadata
        )
        
        db.add(file_record)
        db.commit()
        db.refresh(file_record)
        
        return file_record
    
    @staticmethod
    def list_files(db: Session, app_id: uuid.UUID, user_id: uuid.UUID) -> List[File]:
        """List all files for a user"""
        return db.query(File).filter(
            and_(
                File.app_id == app_id,
                File.user_id == user_id
            )
        ).order_by(File.created_at.desc()).all()
    
    @staticmethod
    def get_file(db: Session, app_id: uuid.UUID, user_id: uuid.UUID, file_id: uuid.UUID) -> Optional[File]:
        """Get file metadata"""
        return db.query(File).filter(
            and_(
                File.id == file_id,
                File.app_id == app_id,
                File.user_id == user_id
            )
        ).first()
    
    @staticmethod
    def get_all_by_app(db: Session, app_id: uuid.UUID) -> List[File]:
        """Get all files for an app (admin)"""
        return db.query(File).filter(File.app_id == app_id).order_by(File.created_at.desc()).all()

    @staticmethod
    def delete_by_id(db: Session, app_id: uuid.UUID, file_id: uuid.UUID) -> bool:
        """Delete file by id (admin)"""
        file_record = db.query(File).filter(File.id == file_id, File.app_id == app_id).first()
        if not file_record:
            return False
        r2_service.delete_file(file_record.r2_key)
        db.delete(file_record)
        db.commit()
        return True

    @staticmethod
    def delete_file(db: Session, app_id: uuid.UUID, user_id: uuid.UUID, file_id: uuid.UUID) -> bool:
        """Delete file from R2 and database"""
        file_record = FileService.get_file(db, app_id, user_id, file_id)
        
        if not file_record:
            return False
        
        # Delete from R2
        r2_service.delete_file(file_record.r2_key)
        
        # Delete from database
        db.delete(file_record)
        db.commit()
        
        return True
    
    @staticmethod
    def batch_upload(
        db: Session,
        app_id: uuid.UUID,
        user_id: uuid.UUID,
        files: List[tuple]  # [(file_data, filename, content_type, size)]
    ) -> List[File]:
        """Upload multiple files at once"""
        uploaded_files = []
        
        for file_data, filename, content_type, size_bytes in files:
            file_record = FileService.upload_file(
                db, app_id, user_id, file_data, filename, content_type, size_bytes
            )
            uploaded_files.append(file_record)
        
        return uploaded_files
