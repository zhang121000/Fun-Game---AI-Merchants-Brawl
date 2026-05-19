import enum
from datetime import datetime
from sqlalchemy import String, Text, Boolean, DateTime, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


class AIModel(str, enum.Enum):
    deepseek = "deepseek"
    doubao = "doubao"
    gpt = "gpt"
    mimo = "mimo"
    qwen = "qwen"


class Merchant(Base):
    __tablename__ = "merchants"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    ai_model: Mapped[str] = mapped_column(String(50))
    main_category: Mapped[str] = mapped_column(String(50), default="")
    persona_prompt: Mapped[str] = mapped_column(Text, default="")
    brand_color: Mapped[str] = mapped_column(String(20), default="#1890ff")
    brand_style: Mapped[dict] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    products: Mapped[list] = relationship("Product", back_populates="merchant", lazy="selectin")
    marketing_strategies: Mapped[list] = relationship("MarketingStrategy", back_populates="merchant", lazy="selectin")
    orders: Mapped[list] = relationship("Order", back_populates="merchant")
