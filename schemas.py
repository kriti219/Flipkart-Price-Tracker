from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


class ProductCreate(BaseModel):
    url: str
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


class PriceHistoryResponse(BaseModel):
    id: int
    product_id: int
    price: Optional[float]
    price_raw: Optional[str]
    availability: str
    scraped_at: datetime
    model_config = {"from_attributes": True}


class ProductResponse(BaseModel):
    id: int
    url: str
    title: Optional[str]
    user_email: str
    target_price: float
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class ProductDetailResponse(ProductResponse):
    latest_price: Optional[float] = None
    latest_availability: Optional[str] = None


class MessageResponse(BaseModel):
    message: str
    
class TargetPriceUpdate(BaseModel):
    target_price: float

    @field_validator("target_price")
    @classmethod
    def must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("target_price must be greater than zero")
        return v