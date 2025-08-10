"""
Authentication service for user management and authentication.
"""

from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.security import verify_password, get_password_hash
from app.models.user import User
from app.schemas.auth import UserRegister
from app.services.user import UserService


class AuthService:
    """Service for authentication operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.user_service = UserService(db)
    
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate user with username/email and password.
        """
        # Try to find user by username or email
        user = self.db.query(User).filter(
            or_(
                User.username == username.lower(),
                User.email == username.lower()
            )
        ).first()
        
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        return user
    
    async def register_user(self, user_data: UserRegister) -> User:
        """
        Register a new user.
        """
        # Check if username already exists
        existing_user = self.db.query(User).filter(
            User.username == user_data.username.lower()
        ).first()
        
        if existing_user:
            raise ValueError("Username already registered")
        
        # Check if email already exists
        existing_email = self.db.query(User).filter(
            User.email == user_data.email.lower()
        ).first()
        
        if existing_email:
            raise ValueError("Email already registered")
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        
        user = User(
            username=user_data.username.lower(),
            email=user_data.email.lower(),
            hashed_password=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            role=user_data.role,
            tenant_id=user_data.tenant_id,
            is_verified=False,  # Require email verification
            is_active=True
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    async def change_password(self, user: User, current_password: str, new_password: str) -> bool:
        """
        Change user password.
        """
        # Verify current password
        if not verify_password(current_password, user.hashed_password):
            raise ValueError("Current password is incorrect")
        
        # Update password
        user.hashed_password = get_password_hash(new_password)
        self.db.commit()
        
        return True
    
    async def reset_password(self, email: str) -> bool:
        """
        Initiate password reset process.
        """
        user = self.db.query(User).filter(User.email == email.lower()).first()
        
        if not user:
            # Don't reveal if email exists or not
            return True
        
        # In a real implementation, you would:
        # 1. Generate a secure reset token
        # 2. Store it in the database with expiration
        # 3. Send email with reset link
        
        return True
    
    async def verify_email(self, user: User, verification_token: str) -> bool:
        """
        Verify user email address.
        """
        # In a real implementation, you would:
        # 1. Verify the token
        # 2. Check if it's not expired
        # 3. Mark user as verified
        
        user.is_verified = True
        self.db.commit()
        
        return True
    
    async def deactivate_user(self, user: User) -> bool:
        """
        Deactivate user account.
        """
        user.is_active = False
        self.db.commit()
        
        return True
    
    async def activate_user(self, user: User) -> bool:
        """
        Activate user account.
        """
        user.is_active = True
        self.db.commit()
        
        return True
    
    async def update_last_login(self, user: User) -> None:
        """
        Update user's last login timestamp.
        """
        user.update_last_login()
        self.db.commit()
    
    def check_user_permissions(self, user: User, required_permission: str) -> bool:
        """
        Check if user has required permission.
        """
        return user.has_permission(required_permission)
    
    def check_user_role(self, user: User, required_role: str) -> bool:
        """
        Check if user has required role or higher.
        """
        role_hierarchy = {
            'cashier': 1,
            'supervisor': 2,
            'manager': 3,
            'admin': 4
        }
        
        user_level = role_hierarchy.get(user.role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        return user_level >= required_level or user.is_superuser
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username.
        """
        return self.db.query(User).filter(
            User.username == username.lower()
        ).first()
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email.
        """
        return self.db.query(User).filter(
            User.email == email.lower()
        ).first()
    
    async def is_username_available(self, username: str, exclude_user_id: Optional[int] = None) -> bool:
        """
        Check if username is available.
        """
        query = self.db.query(User).filter(User.username == username.lower())
        
        if exclude_user_id:
            query = query.filter(User.id != exclude_user_id)
        
        return query.first() is None
    
    async def is_email_available(self, email: str, exclude_user_id: Optional[int] = None) -> bool:
        """
        Check if email is available.
        """
        query = self.db.query(User).filter(User.email == email.lower())
        
        if exclude_user_id:
            query = query.filter(User.id != exclude_user_id)
        
        return query.first() is None
