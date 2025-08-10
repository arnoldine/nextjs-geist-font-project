"""
Tenant model for multi-tenancy support.
"""

from sqlalchemy import Column, String, Text, JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Tenant(BaseModel):
    """
    Tenant model for multi-tenant architecture.
    Each tenant represents a separate business/organization.
    """
    __tablename__ = "tenants"
    
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Contact Information
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    website = Column(String(255), nullable=True)
    
    # Address Information
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)
    
    # Business Information
    business_registration_number = Column(String(100), nullable=True)
    tax_identification_number = Column(String(100), nullable=True)
    
    # Settings (stored as JSON)
    settings = Column(JSON, nullable=True, default={})
    
    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    stores = relationship("Store", back_populates="tenant", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="tenant", cascade="all, delete-orphan")
    customers = relationship("Customer", back_populates="tenant", cascade="all, delete-orphan")
    suppliers = relationship("Supplier", back_populates="tenant", cascade="all, delete-orphan")
    accounts = relationship("Account", back_populates="tenant", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Tenant(id={self.id}, name='{self.name}', slug='{self.slug}')>"
    
    @property
    def full_address(self):
        """Get formatted full address."""
        address_parts = [
            self.address_line1,
            self.address_line2,
            self.city,
            self.state,
            self.postal_code,
            self.country
        ]
        return ", ".join([part for part in address_parts if part])
    
    def get_setting(self, key: str, default=None):
        """Get a specific setting value."""
        if not self.settings:
            return default
        return self.settings.get(key, default)
    
    def set_setting(self, key: str, value):
        """Set a specific setting value."""
        if not self.settings:
            self.settings = {}
        self.settings[key] = value
    
    def get_default_settings(self):
        """Get default tenant settings."""
        return {
            "currency": "USD",
            "currency_symbol": "$",
            "tax_rate": 0.10,
            "tax_inclusive": True,
            "date_format": "YYYY-MM-DD",
            "time_format": "24h",
            "timezone": "UTC",
            "language": "en",
            "receipt_footer": f"Thank you for shopping with {self.name}!",
            "low_stock_threshold": 10,
            "enable_loyalty_points": False,
            "loyalty_points_rate": 0.01,  # 1% of purchase amount
        }
