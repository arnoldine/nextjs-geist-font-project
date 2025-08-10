"""
Purchase order models for supplier management.
"""

from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Numeric, Integer, DateTime, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from app.models.base import BaseModel, TenantMixin, StoreMixin


class PurchaseOrderStatus(PyEnum):
    """Enumeration for purchase order status."""
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    SENT = "sent"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PurchaseOrder(BaseModel, TenantMixin, StoreMixin):
    """
    Purchase order model for managing supplier orders.
    """
    __tablename__ = "purchase_orders"
    
    # Order Information
    po_number = Column(String(50), unique=True, nullable=False, index=True)
    supplier_id = Column(ForeignKey("suppliers.id"), nullable=False, index=True)
    
    # Order Details
    status = Column(Enum(PurchaseOrderStatus), default=PurchaseOrderStatus.DRAFT, nullable=False, index=True)
    order_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    expected_delivery_date = Column(DateTime(timezone=True), nullable=True)
    actual_delivery_date = Column(DateTime(timezone=True), nullable=True)
    
    # Amounts
    subtotal = Column(Numeric(10, 2), default=0, nullable=False)
    tax_amount = Column(Numeric(10, 2), default=0, nullable=False)
    shipping_cost = Column(Numeric(10, 2), default=0, nullable=False)
    discount_amount = Column(Numeric(10, 2), default=0, nullable=False)
    total_amount = Column(Numeric(10, 2), default=0, nullable=False)
    
    # Tax Information
    tax_rate = Column(Numeric(5, 4), nullable=True)
    tax_inclusive = Column(Boolean, default=False, nullable=False)
    
    # Shipping Information
    shipping_address_line1 = Column(String(255), nullable=True)
    shipping_address_line2 = Column(String(255), nullable=True)
    shipping_city = Column(String(100), nullable=True)
    shipping_state = Column(String(100), nullable=True)
    shipping_postal_code = Column(String(20), nullable=True)
    shipping_country = Column(String(100), nullable=True)
    
    # Payment Information
    payment_terms = Column(String(100), nullable=True)
    payment_method = Column(String(50), nullable=True)
    
    # Staff Information
    created_by_user_id = Column(ForeignKey("users.id"), nullable=True, index=True)
    approved_by_user_id = Column(ForeignKey("users.id"), nullable=True, index=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Additional Information
    notes = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)
    supplier_reference = Column(String(100), nullable=True)  # Supplier's reference number
    
    # Tracking Information
    tracking_number = Column(String(100), nullable=True)
    carrier = Column(String(100), nullable=True)
    
    # Additional Data
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    tenant = relationship("Tenant")
    store = relationship("Store")
    supplier = relationship("Supplier", back_populates="purchase_orders")
    created_by = relationship("User", foreign_keys=[created_by_user_id])
    approved_by = relationship("User", foreign_keys=[approved_by_user_id])
    po_items = relationship("PurchaseOrderItem", back_populates="purchase_order", cascade="all, delete-orphan")
    receipts = relationship("GoodsReceipt", back_populates="purchase_order", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<PurchaseOrder(id={self.id}, number='{self.po_number}', total={self.total_amount}, status='{self.status}')>"
    
    @property
    def is_fully_received(self):
        """Check if all items have been fully received."""
        for item in self.po_items:
            if item.quantity_received < item.quantity_ordered:
                return False
        return True
    
    @property
    def is_partially_received(self):
        """Check if some items have been received."""
        for item in self.po_items:
            if item.quantity_received > 0:
                return True
        return False
    
    @property
    def item_count(self):
        """Get total number of items ordered."""
        return sum(item.quantity_ordered for item in self.po_items)
    
    @property
    def unique_item_count(self):
        """Get number of unique items in order."""
        return len(self.po_items)
    
    @property
    def received_percentage(self):
        """Get percentage of items received."""
        if not self.po_items:
            return 0
        
        total_ordered = sum(item.quantity_ordered for item in self.po_items)
        total_received = sum(item.quantity_received for item in self.po_items)
        
        if total_ordered == 0:
            return 0
        
        return (total_received / total_ordered) * 100
    
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
    
    def calculate_totals(self):
        """Calculate and update purchase order totals."""
        # Calculate subtotal from items
        self.subtotal = sum(item.line_total for item in self.po_items)
        
        # Apply discount
        discounted_amount = self.subtotal - self.discount_amount
        
        # Calculate tax
        if self.tax_rate:
            if self.tax_inclusive:
                # Tax is included in the price
                self.tax_amount = discounted_amount * (self.tax_rate / (1 + self.tax_rate))
                self.total_amount = discounted_amount + self.shipping_cost
            else:
                # Tax is added to the price
                self.tax_amount = discounted_amount * self.tax_rate
                self.total_amount = discounted_amount + self.tax_amount + self.shipping_cost
        else:
            self.tax_amount = 0
            self.total_amount = discounted_amount + self.shipping_cost
    
    def add_item(self, product_id: int, variant_id: int = None, quantity: float = 1, 
                 unit_cost: float = None):
        """Add an item to the purchase order."""
        # Check if item already exists
        existing_item = None
        for item in self.po_items:
            if item.product_id == product_id and item.variant_id == variant_id:
                existing_item = item
                break
        
        if existing_item:
            # Update existing item
            existing_item.quantity_ordered += quantity
            existing_item.calculate_line_total()
        else:
            # Create new item
            po_item = PurchaseOrderItem(
                purchase_order_id=self.id,
                product_id=product_id,
                variant_id=variant_id,
                quantity_ordered=quantity,
                unit_cost=unit_cost
            )
            po_item.calculate_line_total()
            self.po_items.append(po_item)
        
        self.calculate_totals()
    
    def remove_item(self, po_item_id: int):
        """Remove an item from the purchase order."""
        self.po_items = [item for item in self.po_items if item.id != po_item_id]
        self.calculate_totals()
    
    def approve(self, user_id: int):
        """Approve the purchase order."""
        if self.status != PurchaseOrderStatus.DRAFT:
            raise ValueError("Only draft purchase orders can be approved")
        
        self.status = PurchaseOrderStatus.APPROVED
        self.approved_by_user_id = user_id
        self.approved_at = func.now()
    
    def send_to_supplier(self):
        """Mark purchase order as sent to supplier."""
        if self.status != PurchaseOrderStatus.APPROVED:
            raise ValueError("Only approved purchase orders can be sent")
        
        self.status = PurchaseOrderStatus.SENT
    
    def cancel(self, reason: str = None):
        """Cancel the purchase order."""
        if self.status in [PurchaseOrderStatus.RECEIVED, PurchaseOrderStatus.COMPLETED]:
            raise ValueError("Cannot cancel received or completed purchase orders")
        
        self.status = PurchaseOrderStatus.CANCELLED
        if reason:
            self.notes = f"Cancelled: {reason}"
    
    def update_status_based_on_receipts(self):
        """Update status based on received quantities."""
        if self.is_fully_received:
            self.status = PurchaseOrderStatus.RECEIVED
        elif self.is_partially_received:
            self.status = PurchaseOrderStatus.PARTIALLY_RECEIVED
    
    def complete(self):
        """Mark purchase order as completed."""
        if not self.is_fully_received:
            raise ValueError("Cannot complete purchase order with unreceived items")
        
        self.status = PurchaseOrderStatus.COMPLETED
        
        # Update supplier purchase history
        self.supplier.update_purchase_history(float(self.total_amount), self.order_date)


class PurchaseOrderItem(BaseModel):
    """
    Individual items within a purchase order.
    """
    __tablename__ = "purchase_order_items"
    
    purchase_order_id = Column(ForeignKey("purchase_orders.id"), nullable=False, index=True)
    product_id = Column(ForeignKey("products.id"), nullable=False, index=True)
    variant_id = Column(ForeignKey("product_variants.id"), nullable=True, index=True)
    
    # Order Details
    quantity_ordered = Column(Numeric(10, 3), nullable=False)
    quantity_received = Column(Numeric(10, 3), default=0, nullable=False)
    unit_cost = Column(Numeric(10, 4), nullable=False)
    line_total = Column(Numeric(10, 2), nullable=False)
    
    # Additional Information
    notes = Column(Text, nullable=True)
    supplier_sku = Column(String(100), nullable=True)  # Supplier's SKU for this item
    
    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="po_items")
    product = relationship("Product")
    variant = relationship("ProductVariant")
    receipt_items = relationship("GoodsReceiptItem", back_populates="po_item")
    
    def __repr__(self):
        return f"<PurchaseOrderItem(id={self.id}, product_id={self.product_id}, qty_ordered={self.quantity_ordered}, qty_received={self.quantity_received})>"
    
    @property
    def quantity_outstanding(self):
        """Get quantity still to be received."""
        return self.quantity_ordered - self.quantity_received
    
    @property
    def is_fully_received(self):
        """Check if item is fully received."""
        return self.quantity_received >= self.quantity_ordered
    
    @property
    def received_percentage(self):
        """Get percentage received."""
        if self.quantity_ordered == 0:
            return 0
        return (self.quantity_received / self.quantity_ordered) * 100
    
    def calculate_line_total(self):
        """Calculate line total."""
        self.line_total = float(self.quantity_ordered) * float(self.unit_cost)
    
    def receive_quantity(self, quantity: float):
        """Record received quantity."""
        if quantity > self.quantity_outstanding:
            raise ValueError("Cannot receive more than outstanding quantity")
        
        self.quantity_received += quantity


class GoodsReceipt(BaseModel, TenantMixin, StoreMixin):
    """
    Goods receipt model for recording received inventory.
    """
    __tablename__ = "goods_receipts"
    
    # Receipt Information
    receipt_number = Column(String(50), unique=True, nullable=False, index=True)
    purchase_order_id = Column(ForeignKey("purchase_orders.id"), nullable=False, index=True)
    
    # Receipt Details
    receipt_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    received_by_user_id = Column(ForeignKey("users.id"), nullable=True, index=True)
    
    # Status
    status = Column(String(20), default="draft", nullable=False)  # draft, completed
    
    # Additional Information
    notes = Column(Text, nullable=True)
    delivery_note_number = Column(String(100), nullable=True)
    carrier = Column(String(100), nullable=True)
    tracking_number = Column(String(100), nullable=True)
    
    # Quality Check
    quality_check_passed = Column(Boolean, default=True, nullable=False)
    quality_notes = Column(Text, nullable=True)
    
    # Relationships
    tenant = relationship("Tenant")
    store = relationship("Store")
    purchase_order = relationship("PurchaseOrder", back_populates="receipts")
    received_by = relationship("User")
    receipt_items = relationship("GoodsReceiptItem", back_populates="goods_receipt", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<GoodsReceipt(id={self.id}, number='{self.receipt_number}', po_id={self.purchase_order_id})>"
    
    @property
    def total_items_received(self):
        """Get total quantity of items received."""
        return sum(item.quantity_received for item in self.receipt_items)
    
    def complete_receipt(self):
        """Complete the goods receipt and update inventory."""
        if self.status != "draft":
            raise ValueError("Only draft receipts can be completed")
        
        stock_movements = []
        
        for item in self.receipt_items:
            # Update purchase order item
            item.po_item.receive_quantity(item.quantity_received)
            
            # Update inventory
            inventory_item = self.get_or_create_inventory_item(
                item.po_item.product_id, 
                item.po_item.variant_id
            )
            
            # Update inventory quantities
            old_quantity = inventory_item.quantity_on_hand
            inventory_item.quantity_on_hand += item.quantity_received
            inventory_item.update_available_quantity()
            
            # Update cost using weighted average
            inventory_item.update_cost(float(item.unit_cost), float(item.quantity_received))
            
            # Create stock movement
            from app.models.inventory import StockMovement, MovementType
            movement = StockMovement(
                tenant_id=self.tenant_id,
                store_id=self.store_id,
                inventory_item_id=inventory_item.id,
                product_id=item.po_item.product_id,
                variant_id=item.po_item.variant_id,
                movement_type=MovementType.PURCHASE,
                quantity=item.quantity_received,
                unit_cost=item.unit_cost,
                reference_type="goods_receipt",
                reference_id=self.id,
                reference_number=self.receipt_number,
                notes=f"Goods receipt from PO {self.purchase_order.po_number}",
                quantity_before=old_quantity,
                quantity_after=inventory_item.quantity_on_hand
            )
            stock_movements.append(movement)
        
        self.status = "completed"
        
        # Update purchase order status
        self.purchase_order.update_status_based_on_receipts()
        
        return stock_movements
    
    def get_or_create_inventory_item(self, product_id: int, variant_id: int = None):
        """Get or create inventory item for the product/variant in this store."""
        from app.models.inventory import InventoryItem
        from sqlalchemy.orm import Session
        
        # This would need to be implemented with proper session handling
        # For now, it's a placeholder
        pass


class GoodsReceiptItem(BaseModel):
    """
    Individual items within a goods receipt.
    """
    __tablename__ = "goods_receipt_items"
    
    goods_receipt_id = Column(ForeignKey("goods_receipts.id"), nullable=False, index=True)
    po_item_id = Column(ForeignKey("purchase_order_items.id"), nullable=False, index=True)
    
    # Receipt Details
    quantity_received = Column(Numeric(10, 3), nullable=False)
    unit_cost = Column(Numeric(10, 4), nullable=False)
    
    # Quality Information
    quality_status = Column(String(20), default="good", nullable=False)  # good, damaged, expired
    quality_notes = Column(Text, nullable=True)
    
    # Batch/Lot Information
    batch_number = Column(String(100), nullable=True)
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    
    # Additional Information
    notes = Column(Text, nullable=True)
    
    # Relationships
    goods_receipt = relationship("GoodsReceipt", back_populates="receipt_items")
    po_item = relationship("PurchaseOrderItem", back_populates="receipt_items")
    
    def __repr__(self):
        return f"<GoodsReceiptItem(id={self.id}, po_item_id={self.po_item_id}, qty={self.quantity_received})>"
    
    @property
    def line_total(self):
        """Calculate line total value."""
        return float(self.quantity_received) * float(self.unit_cost)
    
    @property
    def is_damaged(self):
        """Check if item is damaged."""
        return self.quality_status == "damaged"
    
    @property
    def is_expired(self):
        """Check if item is expired."""
        return self.quality_status == "expired"
