from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from models.merchant import Merchant
from schemas.product import MerchantOut

router = APIRouter()


@router.get("/merchants", response_model=list[MerchantOut])
async def list_merchants(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Merchant).where(Merchant.is_active == True))
    return result.scalars().all()


@router.get("/merchants/{merchant_id}", response_model=MerchantOut)
async def get_merchant(merchant_id: int, db: AsyncSession = Depends(get_db)):
    merchant = await db.get(Merchant, merchant_id)
    return merchant
