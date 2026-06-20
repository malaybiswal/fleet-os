from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from sqlalchemy import Column, ForeignKey, Integer

class Load(Base):
    __tablename__ = "loads"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    load_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    truck_id: Mapped[str | None] = mapped_column(String(50), ForeignKey("trucks.truck_id"), nullable=True)
    driver_id: Mapped[str | None] = mapped_column(String(50), ForeignKey("drivers.driver_id"), nullable=True)
    equipment_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    broker_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    origin: Mapped[str | None] = mapped_column(String(200), nullable=True)
    origin_lat: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    origin_lon: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    destination: Mapped[str | None] = mapped_column(String(200), nullable=True)
    revenue: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    miles: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    deadhead_miles: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    fuel_cost: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    maintenance_reserve: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    driver_cost: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    tolls: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    pickup_time: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivery_time: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    fleet_id: Mapped[int | None] = mapped_column(ForeignKey("fleets.id"), nullable=True,index=True,)

    truck = relationship("Truck", back_populates="loads")
    driver = relationship("Driver", back_populates="loads")
    dwell_events = relationship("DwellEvent", back_populates="load")
