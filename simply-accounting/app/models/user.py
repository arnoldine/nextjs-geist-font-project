"""
User model for authentication and authorization.
"""

from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import BaseModel, TenantMixin


class User(BaseModel, TenantMixin):
    """
    User model for system authentication and authorization.
    """
    __tablename__ = "users"
    
    # Basic Information
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    
    # Personal Information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(50), nullable=True)
    
    # Role and Permissions
    role = Column(String(50), nullable=False, default="cashier")  # admin, manager, supervisor, cashier, auditor
    
    # Account Status
    is_verified = Column(Boolean, default=False, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
    # Login Information
    last_login = Column(DateTime(timezone=True), nullable=True)
    login_count = Column(String(10), default="0", nullable=False)
    
    # Profile Information
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    
    # Settings
    preferred_language = Column(String(10), default="en", nullable=False)
    timezone = Column(String(50), default="UTC", nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    created_sales = relationship("Sale", foreign_keys="Sale.created_by", back_populates="cashier")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
    
    @property
    def full_name(self):
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def display_name(self):
        """Get display name (full name or username)."""
        full_name = self.full_name
        return full_name if full_name else self.username
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        from app.core.security import PermissionChecker
        return PermissionChecker.has_permission(self.role, permission)
    
    def get_permissions(self) -> list:
        """Get all permissions for this user."""
        from app.core.security import PermissionChecker
        return PermissionChecker.get_role_permissions(self.role)
    
    def is_admin(self) -> bool:
        """Check if user is an admin."""
        return self.role == "admin" or self.is_superuser
    
    def is_manager(self) -> bool:
        """Check if user is a manager or higher."""
        return self.role in ["admin", "manager"] or self.is_superuser
    
    def is_supervisor(self) -> bool:
        """Check if user is a supervisor or higher."""
        return self.role in ["admin", "manager", "supervisor"] or self.is_superuser
    
    def can_access_store(self, store_id: int) -> bool:
        """Check if user can access a specific store."""
        # For now, all users can access all stores within their tenant
        # This can be extended to support store-specific permissions
        return True
    
    def update_last_login(self):
        """Update last login timestamp and increment login count."""
        self.last_login = func.now()
        try:
            count = int(self.login_count)
            self.login_count = str(count + 1)
        except (ValueError, TypeError):
            self.login_count = "1"
    
    def to_dict(self, include_sensitive=False):
        """Convert user to dictionary, optionally excluding sensitive data."""
        data = super().to_dict()
        
        if not include_sensitive:
            # Remove sensitive fields
            data.pop('hashed_password', None)
        
        # Add computed fields
        data['full_name'] = self.full_name
        data['display_name'] = self.display_name
        data['permissions'] = self.get_permissions()
        
        return data


class UserSession(BaseModel):
    """
    Model to track user sessions for security purposes.
    """
    __tablename__ = "user_sessions"
    
    user_id = Column(ForeignKey("users.id"), nullable=False, index=True)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"
    
    def is_expired(self):
        """Check if session is expired."""
        from datetime import datetime
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self):
        """Check if session is valid (not expired and not revoked)."""
        return not self.is_expired() and not self.is_revoked and self.is_active
    
    def revoke(self):
        """Revoke the session."""
        self.is_revoked = True
        self.is_active = False
