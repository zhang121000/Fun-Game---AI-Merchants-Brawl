from datetime import datetime
from sqlalchemy import String, Float, DateTime, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    demographic: Mapped[str] = mapped_column(String(20))
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_star: Mapped[bool] = mapped_column(default=False)
    age_range: Mapped[str] = mapped_column(String(20))
    preferences: Mapped[dict] = mapped_column(JSON, default=dict)
    purchase_weight: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    orders: Mapped[list["Order"]] = relationship("Order", back_populates="customer")
    cart: Mapped["Cart"] = relationship("Cart", back_populates="customer", uselist=False)
