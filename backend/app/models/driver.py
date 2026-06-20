from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from sqlalchemy import ForeignKey, Numeric, String

class Driver(Base):
    __tablename__ = "drivers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    driver_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    fleet_id: Mapped[int | None] = mapped_column(
        ForeignKey("fleets.id"),
        nullable=True,
        index=True,
    )

    hos_hours_remaining: Mapped[float | None] = mapped_column(Numeric(4, 1), nullable=True)

    loads = relationship("Load", back_populates="driver")