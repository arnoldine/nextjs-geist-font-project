"""
Pydantic schemas for API request/response validation.
"""

from .auth import Token, TokenRefresh, UserLogin, UserRegister
from .user import UserResponse, UserCreate, UserUpdate
from .tenant import TenantResponse, TenantCreate, TenantUpdate
from .store import StoreResponse, StoreCreate, StoreUpdate
from .product import ProductResponse, ProductCreate, ProductUpdate
from .customer import CustomerResponse, CustomerCreate, CustomerUpdate
from .supplier import SupplierResponse, SupplierCreate, SupplierUpdate
from .sale import SaleResponse, SaleCreate, SaleUpdate
from .inventory import InventoryItemResponse, StockMovementResponse

__all__ = [
    "Token",
    "TokenRefresh", 
    "UserLogin",
    "UserRegister",
    "UserResponse",
    "UserCreate",
    "UserUpdate",
    "TenantResponse",
    "TenantCreate", 
    "TenantUpdate",
    "StoreResponse",
    "StoreCreate",
    "StoreUpdate",
    "ProductResponse",
    "ProductCreate",
    "ProductUpdate",
    "CustomerResponse",
    "CustomerCreate",
    "CustomerUpdate",
    "SupplierResponse",
    "SupplierCreate",
    "SupplierUpdate",
    "SaleResponse",
    "SaleCreate",
    "SaleUpdate",
    "InventoryItemResponse",
    "StockMovementResponse",
]
