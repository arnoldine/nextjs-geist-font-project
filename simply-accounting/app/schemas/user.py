"""
User schemas.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, validator


class UserBase(BaseModel):
    """Base user schema."""
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    phone: Optional[str] = None
    role: str = "cashier"
    is_active: bool = True
    preferred_language: str = "en"
    timezone: str = "UTC"


class UserCreate(UserBase):
    """Schema for creating a user."""
    password: str
    tenant_id: int
    
    @validator('username')
    def username_validation(cls, v):
        if not v or len(v.strip()) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, hyphens, and underscores')
        return v.strip().lower()
    
    @validator('password')
    def password_validation(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    @validator('first_name', 'last_name')
    def name_validation(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        if len(v.strip()) < 2:
            raise ValueError('Name must be at least 2 characters long')
        return v.strip().title()
    
    @validator('role')
    def role_validation(cls, v):
        allowed_roles = ['admin', 'manager', 'supervisor', 'cashier', 'auditor']
        if v not in allowed_roles:
            raise ValueError(f'Role must be one of: {", ".join(allowed_roles)}')
        return v
    
    @validator('phone')
    def phone_validation(cls, v):
        if v and len(v.strip()) < 10:
            raise ValueError('Phone number must be at least 10 characters long')
        return v.strip() if v else None


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    preferred_language: Optional[str] = None
    timezone: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    
    @validator('first_name', 'last_name')
    def name_validation(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError('Name cannot be empty')
            if len(v.strip()) < 2:
                raise ValueError('Name must be at least 2 characters long')
            return v.strip().title()
        return v
    
    @validator('role')
    def role_validation(cls, v):
        if v is not None:
            allowed_roles = ['admin', 'manager', 'supervisor', 'cashier', 'auditor']
            if v not in allowed_roles:
                raise ValueError(f'Role must be one of: {", ".join(allowed_roles)}')
        return v
    
    @validator('phone')
    def phone_validation(cls, v):
        if v is not None and v.strip() and len(v.strip()) < 10:
            raise ValueError('Phone number must be at least 10 characters long')
        return v.strip() if v else None


class UserResponse(BaseModel):
    """Schema for user response."""
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    full_name: str
    display_name: str
    phone: Optional[str] = None
    role: str
    is_active: bool
    is_verified: bool
    is_superuser: bool
    tenant_id: int
    last_login: Optional[datetime] = None
    login_count: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    preferred_language: str
    timezone: str
    permissions: List[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Schema for user list response."""
    users: List[UserResponse]
    total: int
    page: int
    per_page: int
    pages: int


class UserProfile(BaseModel):
    """Schema for user profile."""
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    full_name: str
    display_name: str
    phone: Optional[str] = None
    role: str
    tenant_id: int
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    preferred_language: str
    timezone: str
    last_login: Optional[datetime] = None
    login_count: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    """Schema for updating user profile."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    preferred_language: Optional[str] = None
    timezone: Optional[str] = None
    
    @validator('first_name', 'last_name')
    def name_validation(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError('Name cannot be empty')
            if len(v.strip()) < 2:
                raise ValueError('Name must be at least 2 characters long')
            return v.strip().title()
        return v
    
    @validator('phone')
    def phone_validation(cls, v):
        if v is not None and v.strip() and len(v.strip()) < 10:
            raise ValueError('Phone number must be at least 10 characters long')
        return v.strip() if v else None


class UserStats(BaseModel):
    """Schema for user statistics."""
    total_users: int
    active_users: int
    inactive_users: int
    users_by_role: dict
    recent_logins: int
    new_users_this_month: int


class UserActivity(BaseModel):
    """Schema for user activity."""
    user_id: int
    username: str
    full_name: str
    activity_type: str
    description: str
    timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    class Config:
        from_attributes = True


class UserSession(BaseModel):
    """Schema for user session."""
    id: int
    user_id: int
    session_token: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    expires_at: datetime
    is_revoked: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserPermissions(BaseModel):
    """Schema for user permissions."""
    user_id: int
    role: str
    permissions: List[str]
    can_access_admin: bool
    can_manage_users: bool
    can_manage_inventory: bool
    can_process_sales: bool
    can_view_reports: bool
