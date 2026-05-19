from pydantic import BaseModel
from datetime import datetime


class StrategyOut(BaseModel):
    id: int
    merchant_id: int
    strategy_type: str
    title: str
    description: str
    proposed_changes: dict
    status: str
    ai_reasoning: str
    admin_comment: str
    created_at: datetime | None = None
    reviewed_at: datetime | None = None

    class Config:
        from_attributes = True


class ApproveRequest(BaseModel):
    comment: str = ""


class RejectRequest(BaseModel):
    comment: str = ""
