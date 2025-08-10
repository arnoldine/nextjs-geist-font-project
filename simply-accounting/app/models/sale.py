"""
Sales transaction models for POS system.
"""

from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Numeric, Integer, DateTime, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from app.models.base import BaseModel, TenantMixin, StoreMixin


class SaleStatus(PyEnum):
    """Enumeration for sale status."""
    DRAFT = "draft"
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class PaymentMethod(PyEnum):
    """Enumeration for payment methods."""
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    CHECK = "check"
    BANK_TRANSFER = "bank_transfer"
    DIGITAL_WALLET = "digital_wallet"
    STORE_CREDIT = "store_credit"
    LOYALTY_POINTS = "loyalty_points"


class Sale(BaseModel, TenantMixin, StoreMixin):
    """
    Sale model for POS transactions.
    """
    __tablename__ = "sales"
    
    # Sale Information
    sale_number = Column(String(50), unique=True, nullable=False, index=True)
    receipt_number = Column(String(50), nullable=True, index=True)
    
    # Customer Information
    customer_id = Column(ForeignKey("customers.id"), nullable=True, index=True)
    
    # Sale Details
    status = Column(Enum(SaleStatus), default=SaleStatus.DRAFT, nullable=False, index=True)
    sale_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Amounts
    subtotal = Column(Numeric(10, 2), default=0, nullable=False)
    tax_amount = Column(Numeric(10, 2), default=0, nullable=False)
    discount_amount = Column(Numeric(10, 2), default=0, nullable=False)
    total_amount = Column(Numeric(10, 2), default=0, nullable=False)
    
    # Payment Information
    amount_paid = Column(Numeric(10, 2), default=0, nullable=False)
    amount_due = Column(Numeric(10, 2), default=0, nullable=False)
    change_amount = Column(Numeric(10, 2), default=0, nullable=False)
    
    # Discount Information
    discount_type = Column(String(20), nullable=True)  # percentage, fixed_amount, coupon
    discount_value = Column(Numeric(10, 4), nullable=True)
    discount_reason = Column(String(255), nullable=True)
    coupon_code = Column(String(100), nullable=True)
    
    # Tax Information
    tax_rate = Column(Numeric(5, 4), nullable=True)
    tax_inclusive = Column(Boolean, default=True, nullable=False)
    
    # Staff Information
    cashier_id = Column(ForeignKey("users.id"), nullable=True, index=True)
    
    # Additional Information
    notes = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)
    
    # Loyalty Points
    loyalty_points_earned = Column(Integer, default=0, nullable=False)
    loyalty_points_redeemed = Column(Integer, default=0, nullable=False)
    
    # Refund Information
    refunded_amount = Column(Numeric(10, 2), default=0, nullable=False)
    refund_reason = Column(Text, nullable=True)
    
    # Additional Data
    metadata = Column(JSON, nullable=True)  # Additional sale data
    
    # Relationships
    tenant = relationship("Tenant")
    store = relationship("Store", back_populates="sales")
    customer = relationship("Customer", back_populates="sales")
    cashier = relationship("User", foreign_keys=[cashier_id], back_populates="created_sales")
    sale_items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")
    payments = relationship("SalePayment", back_populates="sale", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Sale(id={self.id}, number='{self.sale_number}', total={self.total_amount}, status='{self.status}')>"
    
    @property
    def is_paid(self):
        """Check if sale is fully paid."""
        return self.amount_due <= 0
    
    @property
    def is_overpaid(self):
        """Check if sale is overpaid."""
        return self.amount_paid > self.total_amount
    
    @property
    def item_count(self):
        """Get total number of items in sale."""
        return sum(item.quantity for item in self.sale_items)
    
    @property
    def unique_item_count(self):
        """Get number of unique items in sale."""
        return len(self.sale_items)
    
    def calculate_totals(self):
        """Calculate and update sale totals."""
        # Calculate subtotal from items
        self.subtotal = sum(item.line_total for item in self.sale_items)
        
        # Apply discount
        if self.discount_type == "percentage" and self.discount_value:
            self.discount_amount = self.subtotal * (self.discount_value / 100)
        elif self.discount_type == "fixed_amount" and self.discount_value:
            self.discount_amount = min(self.discount_value, self.subtotal)
        else:
            self.discount_amount = 0
        
        # Calculate tax
        taxable_amount = self.subtotal - self.discount_amount
        if self.tax_rate:
            if self.tax_inclusive:
                # Tax is included in the price
                self.tax_amount = taxable_amount * (self.tax_rate / (1 + self.tax_rate))
                self.total_amount = taxable_amount
            else:
                # Tax is added to the price
                self.tax_amount = taxable_amount * self.tax_rate
                self.total_amount = taxable_amount + self.tax_amount
        else:
            self.tax_amount = 0
            self.total_amount = taxable_amount
        
        # Calculate amount due
        self.amount_due = self.total_amount - self.amount_paid
        
        # Calculate change
        if self.amount_paid > self.total_amount:
            self.change_amount = self.amount_paid - self.total_amount
        else:
            self.change_amount = 0
    
    def add_item(self, product_id: int, variant_id: int = None, quantity: float = 1, 
                 unit_price: float = None, discount_amount: float = 0):
        """Add an item to the sale."""
        # Check if item already exists
        existing_item = None
        for item in self.sale_items:
            if item.product_id == product_id and item.variant_id == variant_id:
                existing_item = item
                break
        
        if existing_item:
            # Update existing item
            existing_item.quantity += quantity
            existing_item.calculate_line_total()
        else:
            # Create new item
            sale_item = SaleItem(
                sale_id=self.id,
                product_id=product_id,
                variant_id=variant_id,
                quantity=quantity,
                unit_price=unit_price,
                discount_amount=discount_amount
            )
            sale_item.calculate_line_total()
            self.sale_items.append(sale_item)
        
        self.calculate_totals()
    
    def remove_item(self, sale_item_id: int):
        """Remove an item from the sale."""
        self.sale_items = [item for item in self.sale_items if item.id != sale_item_id]
        self.calculate_totals()
    
    def apply_discount(self, discount_type: str, discount_value: float, reason: str = None):
        """Apply discount to the sale."""
        self.discount_type = discount_type
        self.discount_value = discount_value
        self.discount_reason = reason
        self.calculate_totals()
    
    def add_payment(self, payment_method: PaymentMethod, amount: float, 
                   reference_number: str = None, notes: str = None):
        """Add a payment to the sale."""
        payment = SalePayment(
            sale_id=self.id,
            payment_method=payment_method,
            amount=amount,
            reference_number=reference_number,
            notes=notes
        )
        self.payments.append(payment)
        
        # Update amount paid
        self.amount_paid = sum(p.amount for p in self.payments)
        self.calculate_totals()
        
        return payment
    
    def complete_sale(self):
        """Complete the sale."""
        if self.status != SaleStatus.DRAFT:
            raise ValueError("Only draft sales can be completed")
        
        if not self.is_paid:
            raise ValueError("Sale must be fully paid to complete")
        
        self.status = SaleStatus.COMPLETED
        self.sale_date = func.now()
        
        # Update customer purchase history
        if self.customer:
            self.customer.update_purchase_history(float(self.total_amount), self.sale_date)
            
            # Add loyalty points
            if self.loyalty_points_earned > 0:
                self.customer.add_loyalty_points(self.loyalty_points_earned)
    
    def cancel_sale(self, reason: str = None):
        """Cancel the sale."""
        if self.status == SaleStatus.COMPLETED:
            raise ValueError("Completed sales cannot be cancelled")
        
        self.status = SaleStatus.CANCELLED
        if reason:
            self.notes = f"Cancelled: {reason}"
    
    def process_refund(self, refund_amount: float, reason: str = None):
        """Process a refund for the sale."""
        if self.status != SaleStatus.COMPLETED:
            raise ValueError("Only completed sales can be refunded")
        
        if refund_amount > (self.total_amount - self.refunded_amount):
            raise ValueError("Refund amount exceeds refundable amount")
        
        self.refunded_amount += refund_amount
        
        if self.refunded_amount >= self.total_amount:
            self.status = SaleStatus.REFUNDED
        else:
            self.status = SaleStatus.PARTIALLY_REFUNDED
        
        if reason:
            self.refund_reason = reason


class SaleItem(BaseModel):
    """
    Individual items within a sale.
    """
    __tablename__ = "sale_items"
    
    sale_id = Column(ForeignKey("sales.id"), nullable=False, index=True)
    product_id = Column(ForeignKey("products.id"), nullable=False, index=True)
    variant_id = Column(ForeignKey("product_variants.id"), nullable=True, index=True)
    
    # Item Details
    quantity = Column(Numeric(10, 3), nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    line_total = Column(Numeric(10, 2), nullable=False)
    
    # Discount Information
    discount_amount = Column(Numeric(10, 2), default=0, nullable=False)
    discount_percentage = Column(Numeric(5, 2), default=0, nullable=False)
    
    # Tax Information
    tax_rate = Column(Numeric(5, 4), nullable=True)
    tax_amount = Column(Numeric(10, 2), default=0, nullable=False)
    
    # Cost Information (for profit calculation)
    unit_cost = Column(Numeric(10, 4), nullable=True)
    
    # Additional Information
    notes = Column(Text, nullable=True)
    
    # Relationships
    sale = relationship("Sale", back_populates="sale_items")
    product = relationship("Product", back_populates="sale_items")
    variant = relationship("ProductVariant", back_populates="sale_items")
    
    def __repr__(self):
        return f"<SaleItem(id={self.id}, product_id={self.product_id}, qty={self.quantity}, total={self.line_total})>"
    
    @property
    def profit_amount(self):
        """Calculate profit for this line item."""
        if not self.unit_cost:
            return 0
        
        cost_total = float(self.quantity) * float(self.unit_cost)
        return float(self.line_total) - cost_total
    
    @property
    def profit_margin(self):
        """Calculate profit margin percentage."""
        if not self.unit_cost or self.line_total == 0:
            return 0
        
        return (self.profit_amount / float(self.line_total)) * 100
    
    def calculate_line_total(self):
        """Calculate line total including discounts and taxes."""
        # Base amount
        base_amount = float(self.quantity) * float(self.unit_price)
        
        # Apply discount
        discounted_amount = base_amount - float(self.discount_amount)
        
        # Apply tax if specified
        if self.tax_rate:
            self.tax_amount = discounted_amount * float(self.tax_rate)
            self.line_total = discounted_amount + float(self.tax_amount)
        else:
            self.tax_amount = 0
            self.line_total = discounted_amount
    
    def apply_discount(self, discount_amount: float = None, discount_percentage: float = None):
        """Apply discount to the item."""
        if discount_percentage:
            base_amount = float(self.quantity) * float(self.unit_price)
            self.discount_amount = base_amount * (discount_percentage / 100)
            self.discount_percentage = discount_percentage
        elif discount_amount:
            self.discount_amount = discount_amount
            base_amount = float(self.quantity) * float(self.unit_price)
            self.discount_percentage = (discount_amount / base_amount) * 100 if base_amount > 0 else 0
        
        self.calculate_line_total()


class SalePayment(BaseModel):
    """
    Payment records for sales.
    """
    __tablename__ = "sale_payments"
    
    sale_id = Column(ForeignKey("sales.id"), nullable=False, index=True)
    
    # Payment Details
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    
    # Reference Information
    reference_number = Column(String(100), nullable=True)  # Check number, card last 4 digits, etc.
    authorization_code = Column(String(100), nullable=True)  # Credit card authorization
    
    # Payment Status
    status = Column(String(20), default="completed", nullable=False)  # completed, pending, failed
    
    # Additional Information
    notes = Column(Text, nullable=True)
    
    # Relationships
    sale = relationship("Sale", back_populates="payments")
    
    def __repr__(self):
        return f"<SalePayment(id={self.id}, method='{self.payment_method}', amount={self.amount})>"
    
    def get_payment_method_display(self):
        """Get human-readable payment method."""
        method_names = {
            PaymentMethod.CASH: "Cash",
            PaymentMethod.CREDIT_CARD: "Credit Card",
            PaymentMethod.DEBIT_CARD: "Debit Card",
            PaymentMethod.CHECK: "Check",
            PaymentMethod.BANK_TRANSFER: "Bank Transfer",
            PaymentMethod.DIGITAL_WALLET: "Digital Wallet",
            PaymentMethod.STORE_CREDIT: "Store Credit",
            PaymentMethod.LOYALTY_POINTS: "Loyalty Points"
        }
        return method_names.get(self.payment_method, str(self.payment_method))
