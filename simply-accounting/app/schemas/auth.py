"""
Authentication schemas.
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, validator
from .user import UserResponse


class UserLogin(BaseModel):
    """Schema for user login."""
    username: str
    password: str
    
    @validator('username')
    def username_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Username cannot be empty')
        return v.strip()
    
    @validator('password')
    def password_must_not_be_empty(cls, v):
        if not v:
            raise ValueError('Password cannot be empty')
        return v


class UserRegister(BaseModel):
    """Schema for user registration."""
    username: str
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    tenant_id: Optional[int] = None
    role: str = "cashier"
    
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


class Token(BaseModel):
    """Schema for authentication token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class TokenRefresh(BaseModel):
    """Schema for token refresh request."""
    refresh_token: str
    
    @validator('refresh_token')
    def refresh_token_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Refresh token cannot be empty')
        return v.strip()


class PasswordReset(BaseModel):
    """Schema for password reset request."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""
    token: str
    new_password: str
    
    @validator('new_password')
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


class PasswordChange(BaseModel):
    """Schema for password change."""
    current_password: str
    new_password: str
    
    @validator('current_password')
    def current_password_must_not_be_empty(cls, v):
        if not v:
            raise ValueError('Current password cannot be empty')
        return v
    
    @validator('new_password')
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


class LoginResponse(BaseModel):
    """Schema for login response."""
    success: bool
    message: str
    token: Optional[Token] = None
    user: Optional[UserResponse] = None


class LogoutResponse(BaseModel):
    """Schema for logout response."""
    success: bool
    message: str


class AuthStatus(BaseModel):
    """Schema for authentication status."""
    authenticated: bool
    user: Optional[UserResponse] = None
    permissions: Optional[list] = None
    expires_at: Optional[int] = None
