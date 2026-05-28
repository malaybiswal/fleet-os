from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TelemetryEvent(Base):
    __tablename__ = "telemetry_events"
    __table_args__ = (
        Index("idx_telemetry_truck_time", "truck_id", "timestamp"),
        Index("idx_telemetry_fleet_time", "fleet_id", "timestamp"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    truck_id: Mapped[str] = mapped_column(String(50), ForeignKey("trucks.truck_id"), nullable=False)
    fleet_id: Mapped[int | None] = mapped_column(
        ForeignKey("fleets.id"),
        nullable=True,
        index=True,
    )
    timestamp: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    speed: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    heading: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rpm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    engine_temp: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    fuel_level: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    gps_lat: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    gps_lon: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    idle_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reefer_temp: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    load_weight: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)

    truck = relationship("Truck", back_populates="telemetry_events")
