"""
Customer management models.
"""

from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Numeric, Integer, DateTime, Date, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import BaseModel, TenantMixin


class Customer(BaseModel, TenantMixin):
    """
    Customer model for managing customer information and relationships.
    """
    __tablename__ = "customers"
    
    # Basic Information
    customer_number = Column(String(50), nullable=False, index=True)  # Auto-generated customer number
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    company_name = Column(String(255), nullable=True)
    
    # Contact Information
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    mobile = Column(String(50), nullable=True)
    
    # Address Information
    billing_address_line1 = Column(String(255), nullable=True)
    billing_address_line2 = Column(String(255), nullable=True)
    billing_city = Column(String(100), nullable=True)
    billing_state = Column(String(100), nullable=True)
    billing_postal_code = Column(String(20), nullable=True)
    billing_country = Column(String(100), nullable=True)
    
    shipping_address_line1 = Column(String(255), nullable=True)
    shipping_address_line2 = Column(String(255), nullable=True)
    shipping_city = Column(String(100), nullable=True)
    shipping_state = Column(String(100), nullable=True)
    shipping_postal_code = Column(String(20), nullable=True)
    shipping_country = Column(String(100), nullable=True)
    
    # Customer Details
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(10), nullable=True)  # male, female, other
    customer_type = Column(String(20), default="individual", nullable=False)  # individual, business
    
    # Financial Information
    credit_limit = Column(Numeric(10, 2), default=0, nullable=False)
    current_balance = Column(Numeric(10, 2), default=0, nullable=False)  # Outstanding balance
    total_spent = Column(Numeric(10, 2), default=0, nullable=False)  # Lifetime value
    
    # Loyalty Program
    loyalty_points = Column(Integer, default=0, nullable=False)
    loyalty_tier = Column(String(20), default="bronze", nullable=False)  # bronze, silver, gold, platinum
    
    # Preferences
    preferred_payment_method = Column(String(50), nullable=True)
    preferred_communication = Column(String(20), default="email", nullable=False)  # email, sms, phone
    marketing_consent = Column(Boolean, default=False, nullable=False)
    
    # Status
    is_vip = Column(Boolean, default=False, nullable=False)
    is_blocked = Column(Boolean, default=False, nullable=False)
    blocked_reason = Column(Text, nullable=True)
    
    # Timestamps
    first_purchase_date = Column(DateTime(timezone=True), nullable=True)
    last_purchase_date = Column(DateTime(timezone=True), nullable=True)
    
    # Additional Data
    notes = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)  # Customer tags
    custom_fields = Column(JSON, nullable=True)  # Custom fields
    
    # Relationships
    tenant = relationship("Tenant", back_populates="customers")
    sales = relationship("Sale", back_populates="customer")
    
    def __repr__(self):
        return f"<Customer(id={self.id}, name='{self.full_name}', number='{self.customer_number}')>"
    
    @property
    def full_name(self):
        """Get customer's full name."""
        if self.company_name:
            return f"{self.first_name} {self.last_name} ({self.company_name})"
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def display_name(self):
        """Get display name for customer."""
        if self.company_name:
            return self.company_name
        return self.full_name
    
    @property
    def billing_address(self):
        """Get formatted billing address."""
        address_parts = [
            self.billing_address_line1,
            self.billing_address_line2,
            self.billing_city,
            self.billing_state,
            self.billing_postal_code,
            self.billing_country
        ]
        return ", ".join([part for part in address_parts if part])
    
    @property
    def shipping_address(self):
        """Get formatted shipping address."""
        address_parts = [
            self.shipping_address_line1,
            self.shipping_address_line2,
            self.shipping_city,
            self.shipping_state,
            self.shipping_postal_code,
            self.shipping_country
        ]
        return ", ".join([part for part in address_parts if part])
    
    @property
    def has_outstanding_balance(self):
        """Check if customer has outstanding balance."""
        return self.current_balance > 0
    
    @property
    def is_over_credit_limit(self):
        """Check if customer is over credit limit."""
        return self.current_balance > self.credit_limit
    
    @property
    def available_credit(self):
        """Get available credit amount."""
        return max(0, self.credit_limit - self.current_balance)
    
    def add_loyalty_points(self, points: int):
        """Add loyalty points to customer."""
        self.loyalty_points += points
        self.update_loyalty_tier()
    
    def redeem_loyalty_points(self, points: int):
        """Redeem loyalty points."""
        if points > self.loyalty_points:
            raise ValueError("Insufficient loyalty points")
        
        self.loyalty_points -= points
        self.update_loyalty_tier()
    
    def update_loyalty_tier(self):
        """Update loyalty tier based on points."""
        if self.loyalty_points >= 10000:
            self.loyalty_tier = "platinum"
        elif self.loyalty_points >= 5000:
            self.loyalty_tier = "gold"
        elif self.loyalty_points >= 1000:
            self.loyalty_tier = "silver"
        else:
            self.loyalty_tier = "bronze"
    
    def calculate_loyalty_points(self, purchase_amount: float, rate: float = 0.01):
        """Calculate loyalty points for a purchase."""
        return int(purchase_amount * rate)
    
    def update_purchase_history(self, sale_amount: float, sale_date: DateTime = None):
        """Update customer purchase history."""
        if sale_date is None:
            sale_date = func.now()
        
        # Update totals
        self.total_spent += sale_amount
        self.last_purchase_date = sale_date
        
        # Set first purchase date if not set
        if self.first_purchase_date is None:
            self.first_purchase_date = sale_date
    
    def get_purchase_frequency(self):
        """Calculate average days between purchases."""
        if not self.first_purchase_date or not self.last_purchase_date:
            return None
        
        # Get total number of sales
        total_sales = len(self.sales)
        if total_sales <= 1:
            return None
        
        # Calculate days between first and last purchase
        days_diff = (self.last_purchase_date - self.first_purchase_date).days
        
        # Calculate average frequency
        return days_diff / (total_sales - 1)
    
    def get_average_order_value(self):
        """Calculate average order value."""
        if not self.sales:
            return 0
        
        total_amount = sum(sale.total_amount for sale in self.sales if sale.is_active)
        return total_amount / len([s for s in self.sales if s.is_active])
    
    def add_tag(self, tag: str):
        """Add a tag to the customer."""
        if not self.tags:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str):
        """Remove a tag from the customer."""
        if self.tags and tag in self.tags:
            self.tags.remove(tag)
    
    def get_custom_field(self, key: str, default=None):
        """Get a custom field value."""
        if not self.custom_fields:
            return default
        return self.custom_fields.get(key, default)
    
    def set_custom_field(self, key: str, value):
        """Set a custom field value."""
        if not self.custom_fields:
            self.custom_fields = {}
        self.custom_fields[key] = value
    
    def block_customer(self, reason: str):
        """Block customer with reason."""
        self.is_blocked = True
        self.blocked_reason = reason
        self.is_active = False
    
    def unblock_customer(self):
        """Unblock customer."""
        self.is_blocked = False
        self.blocked_reason = None
        self.is_active = True
    
    def copy_billing_to_shipping(self):
        """Copy billing address to shipping address."""
        self.shipping_address_line1 = self.billing_address_line1
        self.shipping_address_line2 = self.billing_address_line2
        self.shipping_city = self.billing_city
        self.shipping_state = self.billing_state
        self.shipping_postal_code = self.billing_postal_code
        self.shipping_country = self.billing_country


class CustomerGroup(BaseModel, TenantMixin):
    """
    Customer group model for organizing customers and applying group-specific pricing.
    """
    __tablename__ = "customer_groups"
    
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Pricing
    discount_percentage = Column(Numeric(5, 2), default=0, nullable=False)  # Group discount
    
    # Settings
    is_default = Column(Boolean, default=False, nullable=False)
    color = Column(String(7), nullable=True)  # Hex color for UI
    
    # Relationships
    tenant = relationship("Tenant")
    
    def __repr__(self):
        return f"<CustomerGroup(id={self.id}, name='{self.name}')>"
    
    @property
    def customer_count(self):
        """Get number of customers in this group."""
        # This would need to be implemented with a many-to-many relationship
        # or a customer_group_id field in the Customer model
        return 0


class CustomerNote(BaseModel):
    """
    Customer notes model for tracking customer interactions and history.
    """
    __tablename__ = "customer_notes"
    
    customer_id = Column(ForeignKey("customers.id"), nullable=False, index=True)
    
    # Note Information
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    note_type = Column(String(50), default="general", nullable=False)  # general, complaint, compliment, follow_up
    
    # Visibility
    is_internal = Column(Boolean, default=True, nullable=False)  # Internal notes vs customer-visible
    is_important = Column(Boolean, default=False, nullable=False)
    
    # Follow-up
    follow_up_date = Column(DateTime(timezone=True), nullable=True)
    is_completed = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    customer = relationship("Customer")
    
    def __repr__(self):
        return f"<CustomerNote(id={self.id}, customer_id={self.customer_id}, type='{self.note_type}')>"
    
    @property
    def is_overdue(self):
        """Check if follow-up is overdue."""
        if not self.follow_up_date or self.is_completed:
            return False
        
        from datetime import datetime
        return datetime.utcnow() > self.follow_up_date
    
    def mark_completed(self):
        """Mark follow-up as completed."""
        self.is_completed = True
