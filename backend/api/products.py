from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from models.product import Product
from schemas.product import ProductOut

router = APIRouter()


@router.get("/products", response_model=list[ProductOut])
async def list_products(
    demographic: str | None = Query(None),
    category: str | None = Query(None),
    merchant_id: int | None = Query(None),
    sort: str = Query("price"),
    db: AsyncSession = Depends(get_db),
):
    q = select(Product).where(Product.is_active == True)
    if demographic:
        q = q.where(Product.target_demographic == demographic)
    if category:
        q = q.where(Product.category == category)
    if merchant_id:
        q = q.where(Product.merchant_id == merchant_id)
    if sort == "price":
        q = q.order_by(Product.price)
    elif sort == "price_desc":
        q = q.order_by(Product.price.desc())
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/products/{product_id}", response_model=ProductOut)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    return await db.get(Product, product_id)


@router.get("/merchants/{merchant_id}/products", response_model=list[ProductOut])
async def merchant_products(
    merchant_id: int,
    demographic: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    q = select(Product).where(Product.merchant_id == merchant_id, Product.is_active == True)
    if demographic:
        q = q.where(Product.target_demographic == demographic)
    result = await db.execute(q)
    return result.scalars().all()
