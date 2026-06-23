from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: str
    brand: str
    price: float
    image_url: Optional[str] = None
    gender: Optional[str] = "unisex"
    color: Optional[str] = None
    synonyms: Optional[List[str]] = []
    # Quality signals (set during seeding or manually)
    rating: Optional[float] = 0.0
    stock: Optional[int] = 100
    discount: Optional[int] = 0


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    """All fields optional for PATCH / PUT."""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    gender: Optional[str] = None
    color: Optional[str] = None
    synonyms: Optional[List[str]] = None
    rating: Optional[float] = None
    stock: Optional[int] = None
    discount: Optional[int] = None
    userRatings: Optional[List[Dict[str, Any]]] = None


class ProductResponse(ProductBase):
    id: str
    created_at: Optional[datetime] = None
    userRatings: Optional[List[Dict[str, Any]]] = []

    class Config:
        from_attributes= True
