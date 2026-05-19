from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from models.cart import Cart, CartItem
from models.product import Product
from models.customer import Customer
from schemas.order import CartOut, AddToCartRequest, UpdateCartRequest

router = APIRouter()


async def _get_or_create_cart(customer_id: int, db: AsyncSession) -> Cart:
    result = await db.execute(select(Cart).where(Cart.customer_id == customer_id))
    cart = result.scalar_one_or_none()
    if not cart:
        cart = Cart(customer_id=customer_id)
        db.add(cart)
        await db.flush()
    return cart


@router.get("/cart", response_model=CartOut)
async def get_cart(customer_id: int, db: AsyncSession = Depends(get_db)):
    cart = await _get_or_create_cart(customer_id, db)
    return cart


@router.post("/cart/items", response_model=CartOut)
async def add_to_cart(body: AddToCartRequest, customer_id: int, db: AsyncSession = Depends(get_db)):
    product = await db.get(Product, body.product_id)
    if not product or not product.is_active:
        raise HTTPException(404, "商品不存在或已下架")
    cart = await _get_or_create_cart(customer_id, db)
    existing = [i for i in cart.items if i.product_id == body.product_id]
    if existing:
        existing[0].quantity += body.quantity
    else:
        db.add(CartItem(cart_id=cart.id, product_id=body.product_id, quantity=body.quantity))
    await db.flush()
    return cart


@router.put("/cart/items/{item_id}", response_model=CartOut)
async def update_cart_item(item_id: int, body: UpdateCartRequest, customer_id: int, db: AsyncSession = Depends(get_db)):
    item = await db.get(CartItem, item_id)
    if not item:
        raise HTTPException(404, "购物车项不存在")
    if body.quantity <= 0:
        await db.delete(item)
    else:
        item.quantity = body.quantity
    await db.flush()
    cart = await _get_or_create_cart(customer_id, db)
    return cart


@router.delete("/cart/items/{item_id}", response_model=CartOut)
async def remove_cart_item(item_id: int, customer_id: int, db: AsyncSession = Depends(get_db)):
    item = await db.get(CartItem, item_id)
    if not item:
        raise HTTPException(404, "购物车项不存在")
    await db.delete(item)
    await db.flush()
    cart = await _get_or_create_cart(customer_id, db)
    return cart
