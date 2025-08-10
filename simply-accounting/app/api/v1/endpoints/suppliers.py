"""
Supplier management endpoints.
"""

from typing import Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.v1.endpoints.auth import require_permission

router = APIRouter()


@router.get("/", response_model=List[dict])
async def get_suppliers(
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(require_permission("supplier:read")),
    db: Session = Depends(get_db)
) -> Any:
    """Get list of suppliers."""
    return []


@router.post("/", response_model=dict)
async def create_supplier(
    current_user: dict = Depends(require_permission("supplier:create")),
    db: Session = Depends(get_db)
) -> Any:
    """Create a new supplier."""
    return {}


@router.get("/{supplier_id}", response_model=dict)
async def get_supplier(
    supplier_id: int,
    current_user: dict = Depends(require_permission("supplier:read")),
    db: Session = Depends(get_db)
) -> Any:
    """Get supplier by ID."""
    return {}


@router.put("/{supplier_id}", response_model=dict)
async def update_supplier(
    supplier_id: int,
    current_user: dict = Depends(require_permission("supplier:update")),
    db: Session = Depends(get_db)
) -> Any:
    """Update supplier."""
    return {}


@router.delete("/{supplier_id}")
async def delete_supplier(
    supplier_id: int,
    current_user: dict = Depends(require_permission("supplier:delete")),
    db: Session = Depends(get_db)
) -> Any:
    """Delete supplier."""
    return {"message": "Supplier deleted successfully"}
