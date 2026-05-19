import enum
from datetime import datetime
from sqlalchemy import String, Text, Integer, Numeric, Boolean, DateTime, JSON, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


class Demographic(str, enum.Enum):
    child = "child"
    male = "male"
    female = "female"
    elderly = "elderly"


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"))
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    ai_model: Mapped[str] = mapped_column(String(50), default="")
    target_demographic: Mapped[str] = mapped_column(String(20), default="all")
    category: Mapped[str] = mapped_column(String(100))
    price: Mapped[float] = mapped_column(Numeric(10, 2))
    original_price: Mapped[float] = mapped_column(Numeric(10, 2))
    stock: Mapped[int] = mapped_column(Integer, default=100)
    max_stock: Mapped[int] = mapped_column(Integer, default=99999)
    image_url: Mapped[str] = mapped_column(String(500), default="")
    ai_selling_points: Mapped[list] = mapped_column(JSON, default=list)
    ai_strategy_history: Mapped[list] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    merchant: Mapped["Merchant"] = relationship(back_populates="products")
    order_items: Mapped[list["OrderItem"]] = relationship(back_populates="product")
    cart_items: Mapped[list] = relationship("CartItem", back_populates="product")
