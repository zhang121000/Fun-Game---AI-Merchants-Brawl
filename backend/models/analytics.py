from datetime import date
from sqlalchemy import String, Integer, Numeric, Float, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base


class AnalyticsSnapshot(Base):
    __tablename__ = "analytics_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    snapshot_date: Mapped[date] = mapped_column(Date)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"))
    demographic: Mapped[str] = mapped_column(String(20))
    total_orders: Mapped[int] = mapped_column(Integer, default=0)
    total_revenue: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    avg_order_value: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    conversion_rate: Mapped[float] = mapped_column(Float, default=0)
    top_product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"), nullable=True)
