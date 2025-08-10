"""
Product models for catalog management.
"""

from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Numeric, Integer, JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseModel, TenantMixin


class ProductCategory(BaseModel, TenantMixin):
    """
    Product category model for organizing products.
    """
    __tablename__ = "product_categories"
    
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    parent_id = Column(ForeignKey("product_categories.id"), nullable=True, index=True)
    sort_order = Column(Integer, default=0, nullable=False)
    
    # SEO and Display
    slug = Column(String(255), nullable=True, index=True)
    image_url = Column(String(500), nullable=True)
    
    # Relationships
    tenant = relationship("Tenant")
    parent = relationship("ProductCategory", remote_side="ProductCategory.id", back_populates="children")
    children = relationship("ProductCategory", back_populates="parent", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="category")
    
    def __repr__(self):
        return f"<ProductCategory(id={self.id}, name='{self.name}')>"
    
    @property
    def full_path(self):
        """Get full category path."""
        if self.parent:
            return f"{self.parent.full_path} > {self.name}"
        return self.name
    
    def get_all_children(self):
        """Get all descendant categories."""
        children = []
        for child in self.children:
            children.append(child)
            children.extend(child.get_all_children())
        return children


class Product(BaseModel, TenantMixin):
    """
    Product model for catalog management.
    """
    __tablename__ = "products"
    
    # Basic Information
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    sku = Column(String(100), nullable=False, index=True)  # Stock Keeping Unit
    barcode = Column(String(100), nullable=True, index=True)
    
    # Category
    category_id = Column(ForeignKey("product_categories.id"), nullable=True, index=True)
    
    # Pricing
    cost_price = Column(Numeric(10, 2), nullable=True)  # What we pay for it
    selling_price = Column(Numeric(10, 2), nullable=False)  # What we sell it for
    compare_at_price = Column(Numeric(10, 2), nullable=True)  # Original price for discounts
    
    # Inventory Management
    track_inventory = Column(Boolean, default=True, nullable=False)
    allow_backorder = Column(Boolean, default=False, nullable=False)
    
    # Physical Properties
    weight = Column(Numeric(8, 3), nullable=True)  # in kg
    weight_unit = Column(String(10), default="kg", nullable=False)
    
    # Tax Information
    is_taxable = Column(Boolean, default=True, nullable=False)
    tax_rate = Column(Numeric(5, 4), nullable=True)  # Override default tax rate
    
    # Product Status
    is_featured = Column(Boolean, default=False, nullable=False)
    is_digital = Column(Boolean, default=False, nullable=False)
    requires_shipping = Column(Boolean, default=True, nullable=False)
    
    # SEO and Display
    slug = Column(String(255), nullable=True, index=True)
    meta_title = Column(String(255), nullable=True)
    meta_description = Column(Text, nullable=True)
    
    # Images and Media
    image_url = Column(String(500), nullable=True)
    gallery_images = Column(JSON, nullable=True)  # Array of image URLs
    
    # Additional Data
    attributes = Column(JSON, nullable=True)  # Custom attributes
    tags = Column(JSON, nullable=True)  # Product tags
    
    # Relationships
    tenant = relationship("Tenant", back_populates="products")
    category = relationship("ProductCategory", back_populates="products")
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")
    inventory_items = relationship("InventoryItem", back_populates="product")
    sale_items = relationship("SaleItem", back_populates="product")
    
    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', sku='{self.sku}')>"
    
    @property
    def display_price(self):
        """Get formatted display price."""
        return f"${self.selling_price:.2f}"
    
    @property
    def profit_margin(self):
        """Calculate profit margin percentage."""
        if not self.cost_price or self.cost_price == 0:
            return None
        return ((self.selling_price - self.cost_price) / self.cost_price) * 100
    
    @property
    def profit_amount(self):
        """Calculate profit amount per unit."""
        if not self.cost_price:
            return None
        return self.selling_price - self.cost_price
    
    def has_variants(self):
        """Check if product has variants."""
        return len(self.variants) > 0
    
    def get_total_inventory(self):
        """Get total inventory across all stores."""
        total = 0
        for item in self.inventory_items:
            if item.is_active and not item.is_deleted:
                total += item.quantity_on_hand or 0
        return total
    
    def get_store_inventory(self, store_id: int):
        """Get inventory for a specific store."""
        for item in self.inventory_items:
            if item.store_id == store_id and item.is_active and not item.is_deleted:
                return item.quantity_on_hand or 0
        return 0
    
    def is_in_stock(self, store_id: int = None):
        """Check if product is in stock."""
        if not self.track_inventory:
            return True
        
        if store_id:
            return self.get_store_inventory(store_id) > 0
        else:
            return self.get_total_inventory() > 0
    
    def get_attribute(self, key: str, default=None):
        """Get a custom attribute value."""
        if not self.attributes:
            return default
        return self.attributes.get(key, default)
    
    def set_attribute(self, key: str, value):
        """Set a custom attribute value."""
        if not self.attributes:
            self.attributes = {}
        self.attributes[key] = value
    
    def add_tag(self, tag: str):
        """Add a tag to the product."""
        if not self.tags:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str):
        """Remove a tag from the product."""
        if self.tags and tag in self.tags:
            self.tags.remove(tag)


class ProductVariant(BaseModel):
    """
    Product variant model for products with multiple options (size, color, etc.).
    """
    __tablename__ = "product_variants"
    
    product_id = Column(ForeignKey("products.id"), nullable=False, index=True)
    
    # Variant Information
    name = Column(String(255), nullable=False)  # e.g., "Large Red"
    sku = Column(String(100), nullable=False, unique=True, index=True)
    barcode = Column(String(100), nullable=True, index=True)
    
    # Pricing (can override product pricing)
    cost_price = Column(Numeric(10, 2), nullable=True)
    selling_price = Column(Numeric(10, 2), nullable=True)
    compare_at_price = Column(Numeric(10, 2), nullable=True)
    
    # Physical Properties
    weight = Column(Numeric(8, 3), nullable=True)
    
    # Variant Options (e.g., size, color, material)
    option1_name = Column(String(100), nullable=True)  # e.g., "Size"
    option1_value = Column(String(100), nullable=True)  # e.g., "Large"
    option2_name = Column(String(100), nullable=True)  # e.g., "Color"
    option2_value = Column(String(100), nullable=True)  # e.g., "Red"
    option3_name = Column(String(100), nullable=True)  # e.g., "Material"
    option3_value = Column(String(100), nullable=True)  # e.g., "Cotton"
    
    # Display
    image_url = Column(String(500), nullable=True)
    sort_order = Column(Integer, default=0, nullable=False)
    
    # Relationships
    product = relationship("Product", back_populates="variants")
    inventory_items = relationship("InventoryItem", back_populates="variant")
    sale_items = relationship("SaleItem", back_populates="variant")
    
    def __repr__(self):
        return f"<ProductVariant(id={self.id}, name='{self.name}', sku='{self.sku}')>"
    
    @property
    def display_price(self):
        """Get display price (variant price or product price)."""
        price = self.selling_price or self.product.selling_price
        return f"${price:.2f}"
    
    @property
    def effective_cost_price(self):
        """Get effective cost price (variant or product)."""
        return self.cost_price or self.product.cost_price
    
    @property
    def effective_selling_price(self):
        """Get effective selling price (variant or product)."""
        return self.selling_price or self.product.selling_price
    
    @property
    def option_summary(self):
        """Get formatted option summary."""
        options = []
        if self.option1_name and self.option1_value:
            options.append(f"{self.option1_name}: {self.option1_value}")
        if self.option2_name and self.option2_value:
            options.append(f"{self.option2_name}: {self.option2_value}")
        if self.option3_name and self.option3_value:
            options.append(f"{self.option3_name}: {self.option3_value}")
        return " | ".join(options)
    
    def get_total_inventory(self):
        """Get total inventory for this variant across all stores."""
        total = 0
        for item in self.inventory_items:
            if item.is_active and not item.is_deleted:
                total += item.quantity_on_hand or 0
        return total
    
    def get_store_inventory(self, store_id: int):
        """Get inventory for this variant in a specific store."""
        for item in self.inventory_items:
            if item.store_id == store_id and item.is_active and not item.is_deleted:
                return item.quantity_on_hand or 0
        return 0
