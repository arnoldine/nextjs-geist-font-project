"""
Supplier management models.
"""

from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Numeric, Integer, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import BaseModel, TenantMixin


class Supplier(BaseModel, TenantMixin):
    """
    Supplier model for managing vendor information and relationships.
    """
    __tablename__ = "suppliers"
    
    # Basic Information
    supplier_number = Column(String(50), nullable=False, index=True)  # Auto-generated supplier number
    company_name = Column(String(255), nullable=False, index=True)
    contact_person = Column(String(255), nullable=True)
    
    # Contact Information
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    mobile = Column(String(50), nullable=True)
    fax = Column(String(50), nullable=True)
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
    
    # Financial Information
    credit_limit = Column(Numeric(10, 2), default=0, nullable=False)
    current_balance = Column(Numeric(10, 2), default=0, nullable=False)  # Amount we owe
    total_purchased = Column(Numeric(10, 2), default=0, nullable=False)  # Lifetime purchases
    
    # Payment Terms
    payment_terms = Column(String(100), nullable=True)  # e.g., "Net 30", "2/10 Net 30"
    payment_method = Column(String(50), nullable=True)  # check, bank_transfer, credit_card
    
    # Banking Information
    bank_name = Column(String(255), nullable=True)
    bank_account_number = Column(String(100), nullable=True)
    bank_routing_number = Column(String(50), nullable=True)
    
    # Supplier Details
    supplier_type = Column(String(50), default="vendor", nullable=False)  # vendor, manufacturer, distributor
    lead_time_days = Column(Integer, default=7, nullable=False)  # Default lead time
    minimum_order_amount = Column(Numeric(10, 2), default=0, nullable=False)
    
    # Status
    is_preferred = Column(Boolean, default=False, nullable=False)
    is_approved = Column(Boolean, default=True, nullable=False)
    is_blocked = Column(Boolean, default=False, nullable=False)
    blocked_reason = Column(Text, nullable=True)
    
    # Performance Metrics
    on_time_delivery_rate = Column(Numeric(5, 2), default=100, nullable=False)  # Percentage
    quality_rating = Column(Numeric(3, 1), default=5.0, nullable=False)  # 1-5 scale
    
    # Timestamps
    first_order_date = Column(DateTime(timezone=True), nullable=True)
    last_order_date = Column(DateTime(timezone=True), nullable=True)
    
    # Additional Data
    notes = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)  # Supplier tags
    custom_fields = Column(JSON, nullable=True)  # Custom fields
    
    # Relationships
    tenant = relationship("Tenant", back_populates="suppliers")
    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")
    
    def __repr__(self):
        return f"<Supplier(id={self.id}, name='{self.company_name}', number='{self.supplier_number}')>"
    
    @property
    def display_name(self):
        """Get display name for supplier."""
        return self.company_name
    
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
    
    @property
    def has_outstanding_balance(self):
        """Check if we owe money to this supplier."""
        return self.current_balance > 0
    
    @property
    def is_over_credit_limit(self):
        """Check if we're over the credit limit with this supplier."""
        return self.current_balance > self.credit_limit
    
    @property
    def available_credit(self):
        """Get available credit amount."""
        return max(0, self.credit_limit - self.current_balance)
    
    def update_purchase_history(self, purchase_amount: float, purchase_date: DateTime = None):
        """Update supplier purchase history."""
        if purchase_date is None:
            purchase_date = func.now()
        
        # Update totals
        self.total_purchased += purchase_amount
        self.current_balance += purchase_amount  # We owe more
        self.last_order_date = purchase_date
        
        # Set first order date if not set
        if self.first_order_date is None:
            self.first_order_date = purchase_date
    
    def make_payment(self, payment_amount: float):
        """Record a payment to the supplier."""
        if payment_amount > self.current_balance:
            raise ValueError("Payment amount cannot exceed outstanding balance")
        
        self.current_balance -= payment_amount
    
    def get_average_order_value(self):
        """Calculate average order value."""
        if not self.purchase_orders:
            return 0
        
        active_orders = [po for po in self.purchase_orders if po.is_active and po.status == "completed"]
        if not active_orders:
            return 0
        
        total_amount = sum(po.total_amount for po in active_orders)
        return total_amount / len(active_orders)
    
    def get_order_frequency(self):
        """Calculate average days between orders."""
        if not self.first_order_date or not self.last_order_date:
            return None
        
        # Get total number of completed orders
        completed_orders = len([po for po in self.purchase_orders if po.status == "completed"])
        if completed_orders <= 1:
            return None
        
        # Calculate days between first and last order
        days_diff = (self.last_order_date - self.first_order_date).days
        
        # Calculate average frequency
        return days_diff / (completed_orders - 1)
    
    def update_performance_metrics(self, on_time: bool, quality_score: float = None):
        """Update supplier performance metrics."""
        # Update on-time delivery rate (simple moving average)
        total_orders = len([po for po in self.purchase_orders if po.status == "completed"])
        if total_orders > 0:
            current_rate = self.on_time_delivery_rate / 100
            if on_time:
                new_rate = (current_rate * (total_orders - 1) + 1) / total_orders
            else:
                new_rate = (current_rate * (total_orders - 1)) / total_orders
            self.on_time_delivery_rate = new_rate * 100
        
        # Update quality rating if provided
        if quality_score is not None and 1 <= quality_score <= 5:
            # Simple moving average
            if total_orders > 0:
                current_rating = float(self.quality_rating)
                new_rating = (current_rating * (total_orders - 1) + quality_score) / total_orders
                self.quality_rating = round(new_rating, 1)
            else:
                self.quality_rating = quality_score
    
    def add_tag(self, tag: str):
        """Add a tag to the supplier."""
        if not self.tags:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str):
        """Remove a tag from the supplier."""
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
    
    def block_supplier(self, reason: str):
        """Block supplier with reason."""
        self.is_blocked = True
        self.blocked_reason = reason
        self.is_active = False
    
    def unblock_supplier(self):
        """Unblock supplier."""
        self.is_blocked = False
        self.blocked_reason = None
        self.is_active = True
    
    def approve_supplier(self):
        """Approve supplier for business."""
        self.is_approved = True
        self.is_active = True
    
    def get_payment_terms_days(self):
        """Extract payment terms in days."""
        if not self.payment_terms:
            return 30  # Default
        
        # Parse common payment terms
        terms_lower = self.payment_terms.lower()
        if "net 30" in terms_lower:
            return 30
        elif "net 15" in terms_lower:
            return 15
        elif "net 60" in terms_lower:
            return 60
        elif "net 90" in terms_lower:
            return 90
        elif "cod" in terms_lower or "cash on delivery" in terms_lower:
            return 0
        else:
            return 30  # Default


class SupplierContact(BaseModel):
    """
    Additional contacts for suppliers.
    """
    __tablename__ = "supplier_contacts"
    
    supplier_id = Column(ForeignKey("suppliers.id"), nullable=False, index=True)
    
    # Contact Information
    name = Column(String(255), nullable=False)
    title = Column(String(100), nullable=True)
    department = Column(String(100), nullable=True)
    
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    mobile = Column(String(50), nullable=True)
    
    # Contact Type
    contact_type = Column(String(50), default="general", nullable=False)  # general, sales, support, billing
    is_primary = Column(Boolean, default=False, nullable=False)
    
    # Additional Information
    notes = Column(Text, nullable=True)
    
    # Relationships
    supplier = relationship("Supplier")
    
    def __repr__(self):
        return f"<SupplierContact(id={self.id}, name='{self.name}', type='{self.contact_type}')>"


class SupplierNote(BaseModel):
    """
    Supplier notes model for tracking supplier interactions and history.
    """
    __tablename__ = "supplier_notes"
    
    supplier_id = Column(ForeignKey("suppliers.id"), nullable=False, index=True)
    
    # Note Information
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    note_type = Column(String(50), default="general", nullable=False)  # general, issue, negotiation, follow_up
    
    # Visibility
    is_internal = Column(Boolean, default=True, nullable=False)
    is_important = Column(Boolean, default=False, nullable=False)
    
    # Follow-up
    follow_up_date = Column(DateTime(timezone=True), nullable=True)
    is_completed = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    supplier = relationship("Supplier")
    
    def __repr__(self):
        return f"<SupplierNote(id={self.id}, supplier_id={self.supplier_id}, type='{self.note_type}')>"
    
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
