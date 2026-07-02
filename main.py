import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from db.connection import engine, Base, get_db
from db import crud
from schemas import (
    ProductCreate,
    ProductResponse,
    ProductDetailResponse,
    PriceHistoryResponse,
    MessageResponse,
)
from scraper import scrape_flipkart_product

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── App startup ───────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once when the server starts
    logger.info("Starting up: creating database tables if they don't exist")
    Base.metadata.create_all(bind=engine)
    yield
    # Runs once when the server shuts down
    logger.info("Shutting down")


app = FastAPI(
    title="Flipkart Price Tracker API",
    description="Track product prices on Flipkart and get alerted when they drop",
    version="1.0.0",
    lifespan=lifespan,
)


# ── CORS ──────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", response_model=MessageResponse)
def root():
    """Health check endpoint."""
    return {"message": "Flipkart Price Tracker API is running"}


@app.post(
    "/products",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_product(payload: ProductCreate, db: Session = Depends(get_db)):
    """
    Add a new product to track.
    Immediately scrapes the product page to get its title
    and stores the first price record.
    """
    # Check for duplicate before scraping
    existing = crud.get_product_by_url(db, payload.url)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"This URL is already being tracked (product id={existing.id})",
        )

    # Scrape first so we can store the title immediately
    logger.info(f"Scraping on product submission: {payload.url}")
    scraped = scrape_flipkart_product(payload.url)

    if "error" in scraped:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not scrape product: {scraped['error']}",
        )

    # Create the product row
    product = crud.create_product(
        db=db,
        url=payload.url,
        user_email=payload.user_email,
        target_price=payload.target_price,
        title=scraped.get("title"),
    )

    # Store the first price history record
    crud.add_price_history(
        db=db,
        product_id=product.id,
        price=scraped.get("price"),
        price_raw=scraped.get("price_raw"),
        availability=scraped.get("availability", "unknown"),
    )

    logger.info(f"Product added successfully: id={product.id}, title={product.title}")
    return product


@app.get("/products", response_model=list[ProductDetailResponse])
def list_products(db: Session = Depends(get_db)):
    """
    List all tracked products with their latest price.
    Used by the Streamlit dashboard to show the tracking table.
    """
    products = crud.get_all_products(db)
    result = []

    for product in products:
        latest = crud.get_latest_price(db, product.id)
        result.append(
            ProductDetailResponse(
                id=product.id,
                url=product.url,
                title=product.title,
                user_email=product.user_email,
                target_price=product.target_price,
                is_active=product.is_active,
                created_at=product.created_at,
                latest_price=latest.price if latest else None,
                latest_availability=latest.availability if latest else None,
            )
        )

    return result


@app.get("/products/{product_id}", response_model=ProductDetailResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """
    Get a single product by ID with its latest price.
    """
    product = crud.get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id={product_id} not found",
        )

    latest = crud.get_latest_price(db, product_id)
    return ProductDetailResponse(
        id=product.id,
        url=product.url,
        title=product.title,
        user_email=product.user_email,
        target_price=product.target_price,
        is_active=product.is_active,
        created_at=product.created_at,
        latest_price=latest.price if latest else None,
        latest_availability=latest.availability if latest else None,
    )


@app.get(
    "/products/{product_id}/history",
    response_model=list[PriceHistoryResponse],
)
def get_price_history(
    product_id: int,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """
    Get price history for a product.
    Used by the Streamlit dashboard to draw the price chart.
    Optional query param: ?limit=50 controls how many data points to return.
    """
    product = crud.get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id={product_id} not found",
        )

    history = crud.get_price_history(db, product_id, limit=limit)
    return history


@app.delete("/products/{product_id}", response_model=MessageResponse)
def deactivate_product(product_id: int, db: Session = Depends(get_db)):
    """
    Stop tracking a product (soft delete).
    Price history is preserved.
    """
    product = crud.get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id={product_id} not found",
        )

    crud.deactivate_product(db, product_id)
    return {"message": f"Product id={product_id} has been deactivated"}