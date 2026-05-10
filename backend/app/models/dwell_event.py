from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DwellEvent(Base):
    __tablename__ = "dwell_events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    load_id: Mapped[str] = mapped_column(String(50), ForeignKey("loads.load_id"), nullable=False)
    facility_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    broker_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    appointment_time: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    arrival_time: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    loading_start: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    loading_end: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    departure_time: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    detention_pay: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    driver_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    load = relationship("Load", back_populates="dwell_events")