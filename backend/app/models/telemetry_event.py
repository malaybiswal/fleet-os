from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TelemetryEvent(Base):
    __tablename__ = "telemetry_events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    truck_id: Mapped[str] = mapped_column(String(50), ForeignKey("trucks.truck_id"), nullable=False)
    timestamp: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    speed: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    rpm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    engine_temp: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    fuel_level: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    gps_lat: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    gps_lon: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    idle_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reefer_temp: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    load_weight: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)

    truck = relationship("Truck", back_populates="telemetry_events")