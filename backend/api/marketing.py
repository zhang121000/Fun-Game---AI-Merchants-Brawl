from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from models.marketing import MarketingStrategy, StrategyStatus
from schemas.marketing import StrategyOut, ApproveRequest, RejectRequest

router = APIRouter()


@router.get("/marketing/strategies", response_model=list[StrategyOut])
async def list_strategies(
    status: str | None = None,
    merchant_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(MarketingStrategy).order_by(MarketingStrategy.created_at.desc())
    if status:
        q = q.where(MarketingStrategy.status == status)
    if merchant_id:
        q = q.where(MarketingStrategy.merchant_id == merchant_id)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/marketing/strategies/{strategy_id}", response_model=StrategyOut)
async def get_strategy(strategy_id: int, db: AsyncSession = Depends(get_db)):
    s = await db.get(MarketingStrategy, strategy_id)
    if not s:
        raise HTTPException(404, "策略不存在")
    return s


@router.post("/marketing/strategies/{strategy_id}/approve", response_model=StrategyOut)
async def approve_strategy(strategy_id: int, body: ApproveRequest, db: AsyncSession = Depends(get_db)):
    s = await db.get(MarketingStrategy, strategy_id)
    if not s:
        raise HTTPException(404, "策略不存在")
    if s.status != StrategyStatus.pending.value:
        raise HTTPException(400, "该策略不在待审批状态")
    s.status = StrategyStatus.approved.value
    s.admin_comment = body.comment
    s.reviewed_at = datetime.utcnow()
    return s


@router.post("/marketing/strategies/{strategy_id}/reject", response_model=StrategyOut)
async def reject_strategy(strategy_id: int, body: RejectRequest, db: AsyncSession = Depends(get_db)):
    s = await db.get(MarketingStrategy, strategy_id)
    if not s:
        raise HTTPException(404, "策略不存在")
    if s.status != StrategyStatus.pending.value:
        raise HTTPException(400, "该策略不在待审批状态")
    s.status = StrategyStatus.rejected.value
    s.admin_comment = body.comment
    s.reviewed_at = datetime.utcnow()
    return s
