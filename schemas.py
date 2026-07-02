from pydantic import BaseModel, HttpUrl, EmailStr, field_validator
from typing import Optional
from datetime import datetime


# ── Request schemas (what the API receives) ───────────────────────────────────

class ProductCreate(BaseModel):
    """Schema for POST /products request body."""
    url: str
    user_email: EmailStr
    target_price: float

    @field_validator("target_price")
    @classmethod
    def target_price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("target_price must be greater than zero")
        return v

    @field_validator("url")
    @classmethod
    def url_must_be_flipkart(cls, v):
        if "flipkart.com" not in v:
            raise ValueError("Only Flipkart URLs are supported")
        return v


# ── Response schemas (what the API returns) ───────────────────────────────────

class PriceHistoryResponse(BaseModel):
    """Schema for a single price history record."""
    id: int
    product_id: int
    price: Optional[float]
    price_raw: Optional[str]
    availability: str
    scraped_at: datetime

    model_config = {"from_attributes": True}


class ProductResponse(BaseModel):
    """Schema for a single product in API responses."""
    id: int
    url: str
    title: Optional[str]
    user_email: str
    target_price: float
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ProductDetailResponse(ProductResponse):
    """Extended product response that includes latest price."""
    latest_price: Optional[float] = None
    latest_availability: Optional[str] = None


class MessageResponse(BaseModel):
    """Generic response for success/info messages."""
    message: str