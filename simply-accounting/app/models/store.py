"""
Store model for multi-store support.
"""

from sqlalchemy import Column, String, Text, Boolean, ForeignKey, JSON, Numeric
from sqlalchemy.orm import relationship
from app.models.base import BaseModel, TenantMixin


class Store(BaseModel, TenantMixin):
    """
    Store model for multi-store operations within a tenant.
    """
    __tablename__ = "stores"
    
    # Basic Information
    name = Column(String(255), nullable=False, index=True)
    code = Column(String(50), nullable=False, index=True)  # Unique store code within tenant
    description = Column(Text, nullable=True)
    
    # Contact Information
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    
    # Address Information
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)
    
    # Business Information
    manager_name = Column(String(255), nullable=True)
    opening_hours = Column(JSON, nullable=True)  # Store opening hours
    
    # Store Settings
    is_main_store = Column(Boolean, default=False, nullable=False)
    allow_negative_inventory = Column(Boolean, default=False, nullable=False)
    auto_reorder_enabled = Column(Boolean, default=True, nullable=False)
    
    # Financial Settings
    default_tax_rate = Column(Numeric(5, 4), nullable=True)  # e.g., 0.1000 for 10%
    currency = Column(String(3), default="USD", nullable=False)
    
    # Store-specific settings
    settings = Column(JSON, nullable=True, default={})
    
    # Relationships
    tenant = relationship("Tenant", back_populates="stores")
    inventory_items = relationship("InventoryItem", back_populates="store", cascade="all, delete-orphan")
    sales = relationship("Sale", back_populates="store", cascade="all, delete-orphan")
    stock_movements = relationship("StockMovement", back_populates="store", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Store(id={self.id}, name='{self.name}', code='{self.code}')>"
    
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
        """Get a specific store setting."""
        if not self.settings:
            return default
        return self.settings.get(key, default)
    
    def set_setting(self, key: str, value):
        """Set a specific store setting."""
        if not self.settings:
            self.settings = {}
        self.settings[key] = value
    
    def get_opening_hours(self, day: str = None):
        """Get opening hours for a specific day or all days."""
        if not self.opening_hours:
            return None
        
        if day:
            return self.opening_hours.get(day.lower())
        return self.opening_hours
    
    def set_opening_hours(self, day: str, open_time: str, close_time: str):
        """Set opening hours for a specific day."""
        if not self.opening_hours:
            self.opening_hours = {}
        
        self.opening_hours[day.lower()] = {
            "open": open_time,
            "close": close_time,
            "is_open": True
        }
    
    def set_closed(self, day: str):
        """Mark store as closed for a specific day."""
        if not self.opening_hours:
            self.opening_hours = {}
        
        self.opening_hours[day.lower()] = {
            "open": None,
            "close": None,
            "is_open": False
        }
    
    def is_open_on_day(self, day: str) -> bool:
        """Check if store is open on a specific day."""
        hours = self.get_opening_hours(day)
        if not hours:
            return True  # Default to open if no hours set
        return hours.get("is_open", True)
    
    def get_default_opening_hours(self):
        """Get default opening hours template."""
        return {
            "monday": {"open": "09:00", "close": "18:00", "is_open": True},
            "tuesday": {"open": "09:00", "close": "18:00", "is_open": True},
            "wednesday": {"open": "09:00", "close": "18:00", "is_open": True},
            "thursday": {"open": "09:00", "close": "18:00", "is_open": True},
            "friday": {"open": "09:00", "close": "18:00", "is_open": True},
            "saturday": {"open": "10:00", "close": "16:00", "is_open": True},
            "sunday": {"open": None, "close": None, "is_open": False}
        }
    
    def get_inventory_value(self):
        """Calculate total inventory value for this store."""
        total_value = 0
        for item in self.inventory_items:
            if item.is_active and not item.is_deleted:
                total_value += (item.quantity_on_hand or 0) * (item.unit_cost or 0)
        return total_value
    
    def get_low_stock_items(self, threshold: int = None):
        """Get items with low stock in this store."""
        if threshold is None:
            threshold = self.get_setting("low_stock_threshold", 10)
        
        low_stock_items = []
        for item in self.inventory_items:
            if (item.is_active and not item.is_deleted and 
                item.quantity_on_hand is not None and 
                item.quantity_on_hand <= threshold):
                low_stock_items.append(item)
        
        return low_stock_items
