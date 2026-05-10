from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    truck_id: Mapped[str] = mapped_column(String(50), ForeignKey("trucks.truck_id"), nullable=False)
    severity: Mapped[str] = mapped_column(String(10), nullable=False)
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    truck = relationship("Truck", back_populates="alerts")