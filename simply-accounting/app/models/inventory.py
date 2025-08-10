"""
Inventory management models.
"""

from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Numeric, Integer, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from app.models.base import BaseModel, TenantMixin, StoreMixin


class MovementType(PyEnum):
    """Enumeration for stock movement types."""
    SALE = "sale"
    PURCHASE = "purchase"
    ADJUSTMENT = "adjustment"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"
    RETURN = "return"
    DAMAGE = "damage"
    EXPIRED = "expired"
    INITIAL = "initial"


class InventoryItem(BaseModel, TenantMixin, StoreMixin):
    """
    Inventory item model tracking stock levels for products/variants in stores.
    """
    __tablename__ = "inventory_items"
    
    # Product References
    product_id = Column(ForeignKey("products.id"), nullable=False, index=True)
    variant_id = Column(ForeignKey("product_variants.id"), nullable=True, index=True)
    
    # Stock Levels
    quantity_on_hand = Column(Numeric(10, 3), default=0, nullable=False)
    quantity_reserved = Column(Numeric(10, 3), default=0, nullable=False)  # Reserved for orders
    quantity_available = Column(Numeric(10, 3), default=0, nullable=False)  # Available for sale
    
    # Reorder Information
    reorder_point = Column(Numeric(10, 3), nullable=True)  # When to reorder
    reorder_quantity = Column(Numeric(10, 3), nullable=True)  # How much to reorder
    max_stock_level = Column(Numeric(10, 3), nullable=True)  # Maximum stock level
    
    # Cost Information
    unit_cost = Column(Numeric(10, 4), nullable=True)  # Average unit cost
    last_cost = Column(Numeric(10, 4), nullable=True)  # Last purchase cost
    
    # Location Information
    bin_location = Column(String(100), nullable=True)  # Physical location in store
    
    # Batch/Lot Tracking
    lot_number = Column(String(100), nullable=True, index=True)
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    tenant = relationship("Tenant")
    store = relationship("Store", back_populates="inventory_items")
    product = relationship("Product", back_populates="inventory_items")
    variant = relationship("ProductVariant", back_populates="inventory_items")
    stock_movements = relationship("StockMovement", back_populates="inventory_item", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<InventoryItem(id={self.id}, product_id={self.product_id}, store_id={self.store_id}, qty={self.quantity_on_hand})>"
    
    @property
    def is_low_stock(self):
        """Check if item is below reorder point."""
        if self.reorder_point is None:
            return False
        return self.quantity_available <= self.reorder_point
    
    @property
    def is_out_of_stock(self):
        """Check if item is out of stock."""
        return self.quantity_available <= 0
    
    @property
    def is_overstocked(self):
        """Check if item is overstocked."""
        if self.max_stock_level is None:
            return False
        return self.quantity_on_hand > self.max_stock_level
    
    @property
    def total_value(self):
        """Calculate total inventory value."""
        if self.unit_cost is None:
            return 0
        return float(self.quantity_on_hand) * float(self.unit_cost)
    
    def update_available_quantity(self):
        """Update available quantity based on on-hand and reserved."""
        self.quantity_available = self.quantity_on_hand - self.quantity_reserved
    
    def reserve_quantity(self, quantity: float):
        """Reserve quantity for an order."""
        if quantity > self.quantity_available:
            raise ValueError("Cannot reserve more than available quantity")
        
        self.quantity_reserved += quantity
        self.update_available_quantity()
    
    def release_reservation(self, quantity: float):
        """Release reserved quantity."""
        if quantity > self.quantity_reserved:
            raise ValueError("Cannot release more than reserved quantity")
        
        self.quantity_reserved -= quantity
        self.update_available_quantity()
    
    def adjust_quantity(self, new_quantity: float, reason: str = "Manual adjustment"):
        """Adjust inventory quantity and create movement record."""
        old_quantity = self.quantity_on_hand
        difference = new_quantity - old_quantity
        
        self.quantity_on_hand = new_quantity
        self.update_available_quantity()
        
        # Create stock movement record
        movement = StockMovement(
            tenant_id=self.tenant_id,
            store_id=self.store_id,
            inventory_item_id=self.id,
            product_id=self.product_id,
            variant_id=self.variant_id,
            movement_type=MovementType.ADJUSTMENT,
            quantity=difference,
            unit_cost=self.unit_cost,
            reference_number=None,
            notes=reason
        )
        
        return movement
    
    def update_cost(self, new_cost: float, quantity: float = 0):
        """Update unit cost using weighted average method."""
        if self.unit_cost is None or self.quantity_on_hand == 0:
            self.unit_cost = new_cost
        else:
            # Weighted average cost
            total_value = (float(self.quantity_on_hand) * float(self.unit_cost)) + (quantity * new_cost)
            total_quantity = float(self.quantity_on_hand) + quantity
            
            if total_quantity > 0:
                self.unit_cost = total_value / total_quantity
        
        self.last_cost = new_cost


class StockMovement(BaseModel, TenantMixin, StoreMixin):
    """
    Stock movement model for tracking all inventory changes.
    """
    __tablename__ = "stock_movements"
    
    # References
    inventory_item_id = Column(ForeignKey("inventory_items.id"), nullable=False, index=True)
    product_id = Column(ForeignKey("products.id"), nullable=False, index=True)
    variant_id = Column(ForeignKey("product_variants.id"), nullable=True, index=True)
    
    # Movement Details
    movement_type = Column(Enum(MovementType), nullable=False, index=True)
    quantity = Column(Numeric(10, 3), nullable=False)  # Positive for in, negative for out
    unit_cost = Column(Numeric(10, 4), nullable=True)
    
    # Reference Information
    reference_type = Column(String(50), nullable=True)  # sale, purchase_order, adjustment, etc.
    reference_id = Column(Integer, nullable=True)  # ID of the related record
    reference_number = Column(String(100), nullable=True, index=True)  # Human-readable reference
    
    # Additional Information
    notes = Column(Text, nullable=True)
    batch_number = Column(String(100), nullable=True)
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    
    # Balances after movement
    quantity_before = Column(Numeric(10, 3), nullable=True)
    quantity_after = Column(Numeric(10, 3), nullable=True)
    
    # Relationships
    tenant = relationship("Tenant")
    store = relationship("Store", back_populates="stock_movements")
    inventory_item = relationship("InventoryItem", back_populates="stock_movements")
    product = relationship("Product")
    variant = relationship("ProductVariant")
    
    def __repr__(self):
        return f"<StockMovement(id={self.id}, type={self.movement_type}, qty={self.quantity})>"
    
    @property
    def total_value(self):
        """Calculate total value of the movement."""
        if self.unit_cost is None:
            return 0
        return float(self.quantity) * float(self.unit_cost)
    
    @property
    def is_inbound(self):
        """Check if movement is inbound (increases stock)."""
        return self.quantity > 0
    
    @property
    def is_outbound(self):
        """Check if movement is outbound (decreases stock)."""
        return self.quantity < 0
    
    def get_movement_description(self):
        """Get human-readable movement description."""
        descriptions = {
            MovementType.SALE: "Sale",
            MovementType.PURCHASE: "Purchase",
            MovementType.ADJUSTMENT: "Stock Adjustment",
            MovementType.TRANSFER_IN: "Transfer In",
            MovementType.TRANSFER_OUT: "Transfer Out",
            MovementType.RETURN: "Return",
            MovementType.DAMAGE: "Damaged Stock",
            MovementType.EXPIRED: "Expired Stock",
            MovementType.INITIAL: "Initial Stock"
        }
        return descriptions.get(self.movement_type, str(self.movement_type))


class StockAdjustment(BaseModel, TenantMixin, StoreMixin):
    """
    Stock adjustment model for bulk inventory adjustments.
    """
    __tablename__ = "stock_adjustments"
    
    # Adjustment Information
    adjustment_number = Column(String(100), unique=True, nullable=False, index=True)
    reason = Column(String(255), nullable=False)
    notes = Column(Text, nullable=True)
    
    # Status
    status = Column(String(20), default="draft", nullable=False)  # draft, approved, applied
    
    # Approval Information
    approved_by = Column(ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Application Information
    applied_by = Column(ForeignKey("users.id"), nullable=True)
    applied_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    tenant = relationship("Tenant")
    store = relationship("Store")
    adjustment_items = relationship("StockAdjustmentItem", back_populates="adjustment", cascade="all, delete-orphan")
    approved_by_user = relationship("User", foreign_keys=[approved_by])
    applied_by_user = relationship("User", foreign_keys=[applied_by])
    
    def __repr__(self):
        return f"<StockAdjustment(id={self.id}, number='{self.adjustment_number}', status='{self.status}')>"
    
    @property
    def total_items(self):
        """Get total number of items in adjustment."""
        return len(self.adjustment_items)
    
    @property
    def total_value_impact(self):
        """Calculate total value impact of adjustment."""
        total = 0
        for item in self.adjustment_items:
            total += item.value_impact
        return total
    
    def can_be_approved(self):
        """Check if adjustment can be approved."""
        return self.status == "draft" and len(self.adjustment_items) > 0
    
    def can_be_applied(self):
        """Check if adjustment can be applied."""
        return self.status == "approved"
    
    def approve(self, user_id: int):
        """Approve the adjustment."""
        if not self.can_be_approved():
            raise ValueError("Adjustment cannot be approved")
        
        self.status = "approved"
        self.approved_by = user_id
        self.approved_at = func.now()
    
    def apply(self, user_id: int):
        """Apply the adjustment to inventory."""
        if not self.can_be_applied():
            raise ValueError("Adjustment cannot be applied")
        
        movements = []
        for item in self.adjustment_items:
            # Update inventory
            inventory_item = item.inventory_item
            old_quantity = inventory_item.quantity_on_hand
            inventory_item.quantity_on_hand = item.new_quantity
            inventory_item.update_available_quantity()
            
            # Create stock movement
            movement = StockMovement(
                tenant_id=self.tenant_id,
                store_id=self.store_id,
                inventory_item_id=item.inventory_item_id,
                product_id=inventory_item.product_id,
                variant_id=inventory_item.variant_id,
                movement_type=MovementType.ADJUSTMENT,
                quantity=item.quantity_difference,
                unit_cost=inventory_item.unit_cost,
                reference_type="stock_adjustment",
                reference_id=self.id,
                reference_number=self.adjustment_number,
                notes=f"Stock adjustment: {self.reason}",
                quantity_before=old_quantity,
                quantity_after=item.new_quantity
            )
            movements.append(movement)
        
        self.status = "applied"
        self.applied_by = user_id
        self.applied_at = func.now()
        
        return movements


class StockAdjustmentItem(BaseModel):
    """
    Individual items within a stock adjustment.
    """
    __tablename__ = "stock_adjustment_items"
    
    adjustment_id = Column(ForeignKey("stock_adjustments.id"), nullable=False, index=True)
    inventory_item_id = Column(ForeignKey("inventory_items.id"), nullable=False, index=True)
    
    # Quantities
    current_quantity = Column(Numeric(10, 3), nullable=False)
    new_quantity = Column(Numeric(10, 3), nullable=False)
    
    # Cost Information
    unit_cost = Column(Numeric(10, 4), nullable=True)
    
    # Reason for this specific item
    reason = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Relationships
    adjustment = relationship("StockAdjustment", back_populates="adjustment_items")
    inventory_item = relationship("InventoryItem")
    
    def __repr__(self):
        return f"<StockAdjustmentItem(id={self.id}, current={self.current_quantity}, new={self.new_quantity})>"
    
    @property
    def quantity_difference(self):
        """Calculate quantity difference."""
        return self.new_quantity - self.current_quantity
    
    @property
    def value_impact(self):
        """Calculate value impact of the adjustment."""
        if self.unit_cost is None:
            return 0
        return float(self.quantity_difference) * float(self.unit_cost)
    
    @property
    def is_increase(self):
        """Check if adjustment increases quantity."""
        return self.quantity_difference > 0
    
    @property
    def is_decrease(self):
        """Check if adjustment decreases quantity."""
        return self.quantity_difference < 0
