from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from models.order import Order, OrderItem
from models.cart import Cart, CartItem
from models.product import Product
from schemas.order import OrderOut

router = APIRouter()


@router.post("/orders", response_model=OrderOut)
async def create_order(customer_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Cart).where(Cart.customer_id == customer_id))
    cart = result.scalar_one_or_none()
    if not cart or not cart.items:
        raise HTTPException(400, "购物车为空")

    merchant_ids = set()
    for item in cart.items:
        product = await db.get(Product, item.product_id)
        if product:
            merchant_ids.add(product.merchant_id)

    orders = []
    for mid in merchant_ids:
        items_in_merchant = [
            i for i in cart.items
            if (await db.get(Product, i.product_id)).merchant_id == mid
        ]
        total = 0
        order = Order(customer_id=customer_id, merchant_id=mid, total_amount=0, status="paid", is_simulated=False)
        db.add(order)
        await db.flush()
        for ci in items_in_merchant:
            product = await db.get(Product, ci.product_id)
            db.add(OrderItem(order_id=order.id, product_id=ci.product_id, quantity=ci.quantity, unit_price=float(product.price)))
            total += float(product.price) * ci.quantity
            product.stock -= ci.quantity
        order.total_amount = total
        orders.append(order)

    for ci in list(cart.items):
        await db.delete(ci)

    await db.flush()
    return orders[0] if len(orders) == 1 else orders[0]


@router.get("/orders", response_model=list[OrderOut])
async def list_orders(customer_id: int | None = None, db: AsyncSession = Depends(get_db)):
    q = select(Order).order_by(Order.created_at.desc())
    if customer_id:
        q = q.where(Order.customer_id == customer_id)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/orders/{order_id}", response_model=OrderOut)
async def get_order(order_id: int, db: AsyncSession = Depends(get_db)):
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(404, "订单不存在")
    return order
