"""
Base repository class providing common database operations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, TypeVar, Generic, Type
from datetime import datetime
import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from sqlalchemy.exc import IntegrityError

from ..database.database import SessionLocal
from ..database.models import Base

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=Base)


class BaseRepository(Generic[T], ABC):
    """Base repository providing common CRUD operations."""
    
    def __init__(self, model: Type[T]):
        """Initialize repository with model class."""
        self.model = model
        self.session_factory = SessionLocal
    
    def _get_session(self) -> Session:
        """Get database session."""
        return self.session_factory()
    
    def _get_timestamp(self) -> str:
        """Get current timestamp string."""
        return datetime.now().isoformat()
    
    def _format_datetime(self, dt) -> str:
        """Format datetime object to ISO string with timezone info."""
        if dt is None:
            return None
        return dt.isoformat() + ('Z' if dt.tzinfo is None else '')
    
    def create(self, data: Dict[str, Any]) -> Optional[T]:
        """Create a new record."""
        try:
            with self._get_session() as db:
                instance = self.model(**data)
                db.add(instance)
                db.commit()
                db.refresh(instance)
                return instance
        except Exception as e:
            logger.error(f"Error creating {self.model.__name__}: {e}")
            return None
    
    def get_by_id(self, record_id: str) -> Optional[T]:
        """Get record by primary key ID."""
        try:
            with self._get_session() as db:
                return db.query(self.model).filter(self.model.id == record_id).first()
        except Exception as e:
            logger.error(f"Error getting {self.model.__name__} by ID {record_id}: {e}")
            return None
    
    def get_by_field(self, field_name: str, value: Any) -> Optional[T]:
        """Get record by specific field."""
        try:
            with self._get_session() as db:
                field = getattr(self.model, field_name)
                return db.query(self.model).filter(field == value).first()
        except Exception as e:
            logger.error(f"Error getting {self.model.__name__} by {field_name}: {e}")
            return None
    
    def list_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """List all records with pagination."""
        try:
            with self._get_session() as db:
                return db.query(self.model).offset(offset).limit(limit).all()
        except Exception as e:
            logger.error(f"Error listing {self.model.__name__}: {e}")
            return []
    
    def update(self, record_id: str, updates: Dict[str, Any]) -> bool:
        """Update record by ID."""
        try:
            with self._get_session() as db:
                record = db.query(self.model).filter(self.model.id == record_id).first()
                if not record:
                    return False
                
                for key, value in updates.items():
                    if hasattr(record, key):
                        setattr(record, key, value)
                
                db.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating {self.model.__name__} {record_id}: {e}")
            return False
    
    def delete(self, record_id: str) -> bool:
        """Delete record by ID."""
        try:
            with self._get_session() as db:
                record = db.query(self.model).filter(self.model.id == record_id).first()
                if not record:
                    return False
                
                db.delete(record)
                db.commit()
                return True
        except Exception as e:
            logger.error(f"Error deleting {self.model.__name__} {record_id}: {e}")
            return False
    
    def count(self, filters: Dict[str, Any] = None) -> int:
        """Count records with optional filters."""
        try:
            with self._get_session() as db:
                query = db.query(self.model)
                
                if filters:
                    for field, value in filters.items():
                        if hasattr(self.model, field):
                            query = query.filter(getattr(self.model, field) == value)
                
                return query.count()
        except Exception as e:
            logger.error(f"Error counting {self.model.__name__}: {e}")
            return 0
    
    def exists(self, filters: Dict[str, Any]) -> bool:
        """Check if record exists with given filters."""
        try:
            with self._get_session() as db:
                query = db.query(self.model)
                
                for field, value in filters.items():
                    if hasattr(self.model, field):
                        query = query.filter(getattr(self.model, field) == value)
                
                return query.first() is not None
        except Exception as e:
            logger.error(f"Error checking existence in {self.model.__name__}: {e}")
            return False


class RepositoryMixin:
    """Mixin providing common repository utilities."""
    
    def to_dict(self, instance: T, exclude_fields: List[str] = None) -> Dict[str, Any]:
        """Convert model instance to dictionary."""
        if not instance:
            return None
        
        exclude_fields = exclude_fields or []
        result = {}
        
        for column in instance.__table__.columns:
            field_name = column.name
            if field_name not in exclude_fields:
                value = getattr(instance, field_name)
                
                # Handle datetime fields
                if isinstance(value, datetime):
                    result[field_name] = value.isoformat() + 'Z' if value.tzinfo is None else value.isoformat()
                else:
                    result[field_name] = value
        
        return result
    
    def to_dict_list(self, instances: List[T], exclude_fields: List[str] = None) -> List[Dict[str, Any]]:
        """Convert list of model instances to list of dictionaries."""
        return [self.to_dict(instance, exclude_fields) for instance in instances if instance]
