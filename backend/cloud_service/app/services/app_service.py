from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.app import App
from app.schemas.app import AppCreate
from typing import Optional
import uuid

class AppService:
    @staticmethod
    def create_app(db: Session, app_data: AppCreate) -> App:
        """Create a new app (tenant)"""
        app = App(
            id=uuid.uuid4(),
            project_id=app_data.project_id,
            name=app_data.name,
            owner_id=app_data.owner_id,
            is_active=True
        )
        
        try:
            db.add(app)
            db.commit()
            db.refresh(app)
            return app
        except IntegrityError:
            db.rollback()
            raise ValueError("App with this project_id already exists")
    
    @staticmethod
    def get_app_by_id(db: Session, app_id: uuid.UUID) -> Optional[App]:
        """Get app by ID"""
        return db.query(App).filter(App.id == app_id, App.is_active == True).first()
    
    @staticmethod
    def get_app_by_project_id(db: Session, project_id: uuid.UUID) -> Optional[App]:
        """Get app by project ID"""
        return db.query(App).filter(App.project_id == project_id, App.is_active == True).first()
    
    @staticmethod
    def get_apps_by_owner(db: Session, owner_id: uuid.UUID):
        """Get all apps for an owner"""
        return db.query(App).filter(App.owner_id == owner_id, App.is_active == True).all()
    
    @staticmethod
    def deactivate_app(db: Session, app_id: uuid.UUID) -> bool:
        """Deactivate an app (soft delete)"""
        app = db.query(App).filter(App.id == app_id).first()
        if app:
            app.is_active = False
            db.commit()
            return True
        return False
