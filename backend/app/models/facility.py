from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def normalize_facility_name(name: str) -> str:
    return " ".join(name.lower().split())


class Facility(Base):
    __tablename__ = "facilities"
    __table_args__ = (
        UniqueConstraint("fleet_id", "normalized_name", name="uq_facilities_fleet_normalized_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    fleet_id: Mapped[int] = mapped_column(ForeignKey("fleets.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(200), nullable=False)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(2), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    facility_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    dwell_events = relationship("DwellEvent", back_populates="facility")
