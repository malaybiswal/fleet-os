from sqlalchemy import DateTime, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from sqlalchemy import DateTime, ForeignKey, Numeric, String, func

class Truck(Base):
    __tablename__ = "trucks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    truck_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    current_location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    current_lat: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    current_lon: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    last_seen_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    fleet_id: Mapped[int | None] = mapped_column(ForeignKey("fleets.id"), nullable=True,index=True,)

    loads = relationship("Load", back_populates="truck")
    telemetry_events = relationship("TelemetryEvent", back_populates="truck")
    alerts = relationship("Alert", back_populates="truck")
