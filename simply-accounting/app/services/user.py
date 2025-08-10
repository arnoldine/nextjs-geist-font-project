"""
User service for user management operations.
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash


class UserService:
    """Service for user management operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user.
        """
        # Check if username already exists
        existing_user = await self.get_user_by_username(user_data.username)
        if existing_user:
            raise ValueError("Username already exists")
        
        # Check if email already exists
        existing_email = await self.get_user_by_email(user_data.email)
        if existing_email:
            raise ValueError("Email already exists")
        
        # Hash password
        hashed_password = get_password_hash(user_data.password)
        
        # Create user
        user = User(
            username=user_data.username.lower(),
            email=user_data.email.lower(),
            hashed_password=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            phone=user_data.phone,
            role=user_data.role,
            tenant_id=user_data.tenant_id,
            is_active=user_data.is_active,
            preferred_language=user_data.preferred_language,
            timezone=user_data.timezone
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Get user by ID.
        """
        return self.db.query(User).filter(
            and_(User.id == user_id, User.is_active == True, User.is_deleted == False)
        ).first()
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username.
        """
        return self.db.query(User).filter(
            and_(
                User.username == username.lower(),
                User.is_active == True,
                User.is_deleted == False
            )
        ).first()
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email.
        """
        return self.db.query(User).filter(
            and_(
                User.email == email.lower(),
                User.is_active == True,
                User.is_deleted == False
            )
        ).first()
    
    async def get_users(
        self,
        tenant_id: Optional[int] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """
        Get list of users with filters.
        """
        query = self.db.query(User).filter(User.is_deleted == False)
        
        if tenant_id:
            query = query.filter(User.tenant_id == tenant_id)
        
        if role:
            query = query.filter(User.role == role)
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    User.username.ilike(search_term),
                    User.email.ilike(search_term),
                    User.first_name.ilike(search_term),
                    User.last_name.ilike(search_term)
                )
            )
        
        return query.offset(skip).limit(limit).all()
    
    async def get_users_count(
        self,
        tenant_id: Optional[int] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> int:
        """
        Get count of users with filters.
        """
        query = self.db.query(User).filter(User.is_deleted == False)
        
        if tenant_id:
            query = query.filter(User.tenant_id == tenant_id)
        
        if role:
            query = query.filter(User.role == role)
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    User.username.ilike(search_term),
                    User.email.ilike(search_term),
                    User.first_name.ilike(search_term),
                    User.last_name.ilike(search_term)
                )
            )
        
        return query.count()
    
    async def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """
        Update user information.
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            return None
        
        # Check if email is being changed and is available
        if user_data.email and user_data.email.lower() != user.email:
            existing_email = await self.get_user_by_email(user_data.email)
            if existing_email:
                raise ValueError("Email already exists")
            user.email = user_data.email.lower()
        
        # Update fields
        update_data = user_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field != 'email':  # Email already handled above
                setattr(user, field, value)
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    async def delete_user(self, user_id: int) -> bool:
        """
        Soft delete a user.
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        user.soft_delete()
        self.db.commit()
        
        return True
    
    async def activate_user(self, user_id: int) -> bool:
        """
        Activate a user.
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        user.is_active = True
        if user.is_deleted:
            user.restore()
        
        self.db.commit()
        
        return True
    
    async def deactivate_user(self, user_id: int) -> bool:
        """
        Deactivate a user.
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        user.is_active = False
        self.db.commit()
        
        return True
    
    async def change_user_role(self, user_id: int, new_role: str) -> bool:
        """
        Change user role.
        """
        allowed_roles = ['admin', 'manager', 'supervisor', 'cashier', 'auditor']
        if new_role not in allowed_roles:
            raise ValueError(f"Invalid role. Must be one of: {', '.join(allowed_roles)}")
        
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        user.role = new_role
        self.db.commit()
        
        return True
    
    async def get_users_by_tenant(self, tenant_id: int) -> List[User]:
        """
        Get all users for a specific tenant.
        """
        return self.db.query(User).filter(
            and_(
                User.tenant_id == tenant_id,
                User.is_active == True,
                User.is_deleted == False
            )
        ).all()
    
    async def get_users_by_role(self, role: str, tenant_id: Optional[int] = None) -> List[User]:
        """
        Get all users with a specific role.
        """
        query = self.db.query(User).filter(
            and_(
                User.role == role,
                User.is_active == True,
                User.is_deleted == False
            )
        )
        
        if tenant_id:
            query = query.filter(User.tenant_id == tenant_id)
        
        return query.all()
    
    async def get_user_stats(self, tenant_id: Optional[int] = None) -> dict:
        """
        Get user statistics.
        """
        query = self.db.query(User).filter(User.is_deleted == False)
        
        if tenant_id:
            query = query.filter(User.tenant_id == tenant_id)
        
        total_users = query.count()
        active_users = query.filter(User.is_active == True).count()
        inactive_users = query.filter(User.is_active == False).count()
        
        # Users by role
        users_by_role = {}
        for role in ['admin', 'manager', 'supervisor', 'cashier', 'auditor']:
            count = query.filter(User.role == role).count()
            users_by_role[role] = count
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': inactive_users,
            'users_by_role': users_by_role
        }
    
    async def search_users(self, search_term: str, tenant_id: Optional[int] = None, limit: int = 10) -> List[User]:
        """
        Search users by name, username, or email.
        """
        search_pattern = f"%{search_term}%"
        query = self.db.query(User).filter(
            and_(
                User.is_active == True,
                User.is_deleted == False,
                or_(
                    User.username.ilike(search_pattern),
                    User.email.ilike(search_pattern),
                    User.first_name.ilike(search_pattern),
                    User.last_name.ilike(search_pattern)
                )
            )
        )
        
        if tenant_id:
            query = query.filter(User.tenant_id == tenant_id)
        
        return query.limit(limit).all()
    
    async def is_username_available(self, username: str, exclude_user_id: Optional[int] = None) -> bool:
        """
        Check if username is available.
        """
        query = self.db.query(User).filter(
            and_(
                User.username == username.lower(),
                User.is_deleted == False
            )
        )
        
        if exclude_user_id:
            query = query.filter(User.id != exclude_user_id)
        
        return query.first() is None
    
    async def is_email_available(self, email: str, exclude_user_id: Optional[int] = None) -> bool:
        """
        Check if email is available.
        """
        query = self.db.query(User).filter(
            and_(
                User.email == email.lower(),
                User.is_deleted == False
            )
        )
        
        if exclude_user_id:
            query = query.filter(User.id != exclude_user_id)
        
        return query.first() is None
