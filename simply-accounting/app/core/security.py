"""
Security utilities for authentication and authorization.
"""

from datetime import datetime, timedelta
from typing import Optional, Union, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[str]:
    """
    Verify and decode a JWT token.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            return None
        return username
    except JWTError:
        return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password.
    """
    return pwd_context.hash(password)


def create_refresh_token(subject: Union[str, Any]) -> str:
    """
    Create a JWT refresh token with longer expiration.
    """
    expire = datetime.utcnow() + timedelta(days=7)  # 7 days for refresh token
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_refresh_token(token: str) -> Optional[str]:
    """
    Verify and decode a JWT refresh token.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if username is None or token_type != "refresh":
            return None
        return username
    except JWTError:
        return None


class PermissionChecker:
    """
    Class to check user permissions for different operations.
    """
    
    # Define permission levels
    PERMISSIONS = {
        "admin": [
            "user:create", "user:read", "user:update", "user:delete",
            "tenant:create", "tenant:read", "tenant:update", "tenant:delete",
            "store:create", "store:read", "store:update", "store:delete",
            "product:create", "product:read", "product:update", "product:delete",
            "inventory:create", "inventory:read", "inventory:update", "inventory:delete",
            "sale:create", "sale:read", "sale:update", "sale:delete",
            "customer:create", "customer:read", "customer:update", "customer:delete",
            "supplier:create", "supplier:read", "supplier:update", "supplier:delete",
            "accounting:create", "accounting:read", "accounting:update", "accounting:delete",
            "report:read", "report:export",
            "system:configure"
        ],
        "manager": [
            "user:read", "user:update",
            "store:read", "store:update",
            "product:create", "product:read", "product:update", "product:delete",
            "inventory:create", "inventory:read", "inventory:update", "inventory:delete",
            "sale:create", "sale:read", "sale:update", "sale:delete",
            "customer:create", "customer:read", "customer:update", "customer:delete",
            "supplier:create", "supplier:read", "supplier:update", "supplier:delete",
            "accounting:create", "accounting:read", "accounting:update",
            "report:read", "report:export"
        ],
        "supervisor": [
            "product:read", "product:update",
            "inventory:read", "inventory:update",
            "sale:create", "sale:read", "sale:update", "sale:delete",
            "customer:create", "customer:read", "customer:update",
            "accounting:read",
            "report:read"
        ],
        "cashier": [
            "product:read",
            "inventory:read",
            "sale:create", "sale:read",
            "customer:read", "customer:update"
        ],
        "auditor": [
            "product:read",
            "inventory:read",
            "sale:read",
            "customer:read",
            "supplier:read",
            "accounting:read",
            "report:read", "report:export"
        ]
    }
    
    @classmethod
    def has_permission(cls, user_role: str, permission: str) -> bool:
        """
        Check if a user role has a specific permission.
        """
        role_permissions = cls.PERMISSIONS.get(user_role.lower(), [])
        return permission in role_permissions
    
    @classmethod
    def get_role_permissions(cls, user_role: str) -> list:
        """
        Get all permissions for a specific role.
        """
        return cls.PERMISSIONS.get(user_role.lower(), [])


def check_permission(required_permission: str):
    """
    Decorator to check if user has required permission.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # This will be implemented with the actual user context
            # For now, it's a placeholder
            return func(*args, **kwargs)
        return wrapper
    return decorator
