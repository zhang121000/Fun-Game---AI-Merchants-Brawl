from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from models.customer import Customer
from schemas.customer import CustomerOut

router = APIRouter()

_current_customer_id: int = 1


@router.get("/customers", response_model=list[CustomerOut])
async def list_customers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Customer).where(Customer.is_star == True)
    )
    return result.scalars().all()


@router.get("/customers/current", response_model=CustomerOut)
async def get_current_customer(db: AsyncSession = Depends(get_db)):
    global _current_customer_id
    customer = await db.get(Customer, _current_customer_id)
    if not customer:
        raise HTTPException(404, "当前顾客不存在")
    return customer


@router.post("/customers/switch/{customer_id}", response_model=CustomerOut)
async def switch_customer(customer_id: int, db: AsyncSession = Depends(get_db)):
    global _current_customer_id
    customer = await db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(404, "顾客不存在")
    _current_customer_id = customer_id
    return customer
