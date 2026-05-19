import enum
from datetime import datetime
from sqlalchemy import String, Text, Integer, Float, DateTime, JSON, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


class StrategyType(str, enum.Enum):
    price_adjustment = "price_adjustment"
    promotion = "promotion"
    bundle = "bundle"
    recommendation_update = "recommendation_update"


class StrategyStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class MarketingStrategy(Base):
    __tablename__ = "marketing_strategies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"))
    strategy_type: Mapped[str] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    proposed_changes: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(20), default=StrategyStatus.pending.value)
    ai_reasoning: Mapped[str] = mapped_column(Text, default="")
    admin_comment: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    merchant: Mapped["Merchant"] = relationship(back_populates="marketing_strategies")


class PurchaseSimulationConfig(Base):
    __tablename__ = "purchase_simulation_config"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    demographic: Mapped[str] = mapped_column(String(20), unique=True)
    base_purchase_rate: Mapped[float] = mapped_column(default=0.05)
    category_preferences: Mapped[dict] = mapped_column(JSON, default=dict)
    price_sensitivity: Mapped[float] = mapped_column(default=0.5)
    brand_loyalty: Mapped[float] = mapped_column(default=0.3)
    time_pattern: Mapped[dict] = mapped_column(JSON, default=dict)


# ============ 新增：日期推进式模拟系统模型 ============

class SimulationState(Base):
    """模拟全局状态"""
    __tablename__ = "simulation_state"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    current_day: Mapped[int] = mapped_column(Integer, default=0)
    is_running: Mapped[bool] = mapped_column(default=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class DailyDecision(Base):
    """每日AI商家决策记录"""
    __tablename__ = "daily_decisions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    day: Mapped[int] = mapped_column(Integer)
    merchant_ai: Mapped[str] = mapped_column(String(50))  # GLM/gpt/MiniMax/Kimi/qwen
    category: Mapped[str] = mapped_column(String(100))
    product_name: Mapped[str] = mapped_column(String(200), default="")

    # AI决策
    price: Mapped[float] = mapped_column(Float)
    promotion: Mapped[str] = mapped_column(Text, default="")
    target_focus: Mapped[str] = mapped_column(String(50), default="")
    description_update: Mapped[str] = mapped_column(Text, default="")
    reasoning: Mapped[str] = mapped_column(Text, default="")

    # 平台分配
    traffic_received: Mapped[int] = mapped_column(Integer, default=0)

    # 结果
    units_sold: Mapped[int] = mapped_column(Integer, default=0)
    revenue: Mapped[float] = mapped_column(Float, default=0.0)
    rank: Mapped[int] = mapped_column(Integer, default=0)

    # 研发
    research_product: Mapped[str] = mapped_column(String(200), default="")
    research_days_remaining: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class PlatformAllocation(Base):
    """平台AI每日流量分配记录"""
    __tablename__ = "platform_allocations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    day: Mapped[int] = mapped_column(Integer)
    merchant_ai: Mapped[str] = mapped_column(String(50))
    demographic: Mapped[str] = mapped_column(String(20))
    traffic_count: Mapped[int] = mapped_column(Integer, default=0)
    reasoning: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ResearchProject(Base):
    """研发项目"""
    __tablename__ = "research_projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    merchant_ai: Mapped[str] = mapped_column(String(50))
    category: Mapped[str] = mapped_column(String(100))
    product_name: Mapped[str] = mapped_column(String(200))
    new_description: Mapped[str] = mapped_column(Text, default="")
    new_price: Mapped[float] = mapped_column(Float, default=0.0)
    days_total: Mapped[int] = mapped_column(Integer, default=3)
    days_remaining: Mapped[int] = mapped_column(Integer, default=3)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active/completed
    started_day: Mapped[int] = mapped_column(Integer)
    completed_day: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
