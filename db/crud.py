import logging
from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import desc

from db.models import Product, PriceHistory

logger = logging.getLogger(__name__)


# ── Product operations ────────────────────────────────────────────────────────

def create_product(
    db: Session,
    url: str,
    user_email: str,
    target_price: float,
    user_id: Optional[str] = None,
    title: Optional[str] = None,
) -> Product:
    existing = db.query(Product).filter(
        Product.url == url,
        Product.user_id == user_id,
    ).first()
    if existing:
        raise ValueError(f"URL already tracked by this user (product id={existing.id})")

    product = Product(
        url=url,
        title=title,
        user_email=user_email,
        target_price=target_price,
        user_id=user_id,
        is_active=True,
        created_at=datetime.utcnow(),
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    logger.info(f"Created product id={product.id}: {url}")
    return product


def get_product_by_id(db: Session, product_id: int) -> Optional[Product]:
    return db.query(Product).filter(Product.id == product_id).first()


def get_product_by_url(
    db: Session,
    url: str,
    user_id: Optional[str] = None,
) -> Optional[Product]:
    return db.query(Product).filter(
        Product.url == url,
        Product.user_id == user_id,
    ).first()


def get_all_products(db: Session) -> list[Product]:
    return (
        db.query(Product)
        .order_by(desc(Product.created_at))
        .all()
    )


def get_products_by_user_id(db: Session, user_id: str) -> list[Product]:
    """Return all products belonging to a specific authenticated user."""
    return (
        db.query(Product)
        .filter(Product.user_id == user_id)
        .order_by(desc(Product.created_at))
        .all()
    )


def get_active_products(db: Session) -> list[Product]:
    return (
        db.query(Product)
        .filter(Product.is_active == True)
        .order_by(desc(Product.created_at))
        .all()
    )


def deactivate_product(db: Session, product_id: int) -> Optional[Product]:
    product = get_product_by_id(db, product_id)
    if not product:
        return None
    product.is_active = False
    db.commit()
    db.refresh(product)
    return product


def update_product_title(db: Session, product_id: int, title: str) -> Optional[Product]:
    product = get_product_by_id(db, product_id)
    if not product:
        return None
    product.title = title
    db.commit()
    db.refresh(product)
    return product


# ── Price history operations ──────────────────────────────────────────────────

def add_price_history(
    db: Session,
    product_id: int,
    price: Optional[float],
    price_raw: Optional[str],
    availability: str = "unknown",
) -> PriceHistory:
    record = PriceHistory(
        product_id=product_id,
        price=price,
        price_raw=price_raw,
        availability=availability,
        scraped_at=datetime.utcnow(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    logger.info(f"Added price history for product id={product_id}: {price_raw}")
    return record


def get_price_history(
    db: Session,
    product_id: int,
    limit: int = 100,
) -> list[PriceHistory]:
    return (
        db.query(PriceHistory)
        .filter(PriceHistory.product_id == product_id)
        .order_by(desc(PriceHistory.scraped_at))
        .limit(limit)
        .all()
    )


def get_latest_price(db: Session, product_id: int) -> Optional[PriceHistory]:
    return (
        db.query(PriceHistory)
        .filter(PriceHistory.product_id == product_id)
        .order_by(desc(PriceHistory.scraped_at))
        .first()
    )


def check_price_alert(db: Session, product_id: int) -> dict:
    product = get_product_by_id(db, product_id)
    if not product:
        return {"should_alert": False, "reason": "product_not_found"}

    latest = get_latest_price(db, product_id)
    if not latest or latest.price is None:
        return {"should_alert": False, "reason": "no_price_data"}

    if latest.availability == "out_of_stock":
        return {"should_alert": False, "reason": "out_of_stock"}

    should_alert = latest.price <= product.target_price

    return {
        "should_alert": should_alert,
        "current_price": latest.price,
        "target_price": product.target_price,
        "product": product,
        "reason": "price_dropped" if should_alert else "price_above_target",
    }
    
def update_target_price(
    db: Session,
    product_id: int,
    new_target_price: float,
) -> Optional[Product]:
    """Update the target alert price for a product."""
    product = get_product_by_id(db, product_id)
    if not product:
        return None
    product.target_price = new_target_price
    db.commit()
    db.refresh(product)
    logger.info(
        f"Updated target price for product id={product_id}: ₹{new_target_price}"
    )
    return product