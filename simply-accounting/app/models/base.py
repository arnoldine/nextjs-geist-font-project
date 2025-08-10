"""
Base model with common fields and functionality.
"""

from sqlalchemy import Column, Integer, DateTime, Boolean, String
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.sql import func
from app.core.database import Base


class BaseModel(Base):
    """
    Base model class with common fields for all models.
    """
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    
    @declared_attr
    def created_by(cls):
        return Column(Integer, nullable=True)
    
    @declared_attr
    def updated_by(cls):
        return Column(Integer, nullable=True)
    
    def soft_delete(self):
        """Soft delete the record."""
        self.is_deleted = True
        self.is_active = False
    
    def restore(self):
        """Restore a soft deleted record."""
        self.is_deleted = False
        self.is_active = True
    
    def to_dict(self):
        """Convert model instance to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"


class TenantMixin:
    """
    Mixin for models that belong to a tenant.
    """
    @declared_attr
    def tenant_id(cls):
        from sqlalchemy import ForeignKey
        return Column(Integer, ForeignKey('tenants.id'), nullable=False, index=True)


class StoreMixin:
    """
    Mixin for models that belong to a store.
    """
    @declared_attr
    def store_id(cls):
        from sqlalchemy import ForeignKey
        return Column(Integer, ForeignKey('stores.id'), nullable=True, index=True)
