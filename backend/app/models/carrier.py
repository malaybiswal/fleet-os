from datetime import date, datetime

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


carrier_tags = Table(
    "carrier_tags",
    Base.metadata,
    Column(
        "carrier_id",
        ForeignKey("carriers.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "created_at",
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    ),
    Index("ix_carrier_tags_carrier_id_tag_id", "carrier_id", "tag_id", unique=True),
)


class Carrier(Base):
    __tablename__ = "carriers"
    __table_args__ = (
        Index("ix_carriers_dot_number", "dot_number", unique=True),
        Index("ix_carriers_state_authority_status", "state", "authority_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    dot_number: Mapped[str] = mapped_column(String(50), nullable=False)
    mc_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )
    legal_name: Mapped[str] = mapped_column(String(200), nullable=False)
    dba_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address_line1: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(2), nullable=True, index=True)
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    country: Mapped[str | None] = mapped_column(String(50), nullable=True)
    authority_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    authority_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    power_units: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    driver_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cargo_types: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    outreach_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        server_default="not_contacted",
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    snapshots: Mapped[list["CarrierSnapshot"]] = relationship(
        "CarrierSnapshot",
        back_populates="carrier",
        cascade="all, delete-orphan",
    )
    outreach_notes: Mapped[list["OutreachNote"]] = relationship(
        "OutreachNote",
        back_populates="carrier",
        cascade="all, delete-orphan",
    )
    tags: Mapped[list["Tag"]] = relationship(
        "Tag",
        secondary=carrier_tags,
        back_populates="carriers",
    )


class CarrierSnapshot(Base):
    __tablename__ = "carrier_snapshots"
    __table_args__ = (
        UniqueConstraint("carrier_id", "snapshot_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    carrier_id: Mapped[int] = mapped_column(
        ForeignKey("carriers.id", ondelete="CASCADE"),
        nullable=False,
    )
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    power_units: Mapped[int | None] = mapped_column(Integer, nullable=True)
    driver_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    authority_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    cargo_types: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    raw_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    carrier: Mapped[Carrier] = relationship("Carrier", back_populates="snapshots")


class OutreachNote(Base):
    __tablename__ = "outreach_notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    carrier_id: Mapped[int] = mapped_column(
        ForeignKey("carriers.id", ondelete="CASCADE"),
        nullable=False,
    )
    note: Mapped[str] = mapped_column(Text, nullable=False)
    outcome: Mapped[str | None] = mapped_column(String(100), nullable=True)
    follow_up_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    contact_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    dispatcher_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    pain_points: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    carrier: Mapped[Carrier] = relationship("Carrier", back_populates="outreach_notes")


class Tag(Base):
    __tablename__ = "tags"
    __table_args__ = (
        Index("ix_tags_name", "name", unique=True),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    carriers: Mapped[list[Carrier]] = relationship(
        "Carrier",
        secondary=carrier_tags,
        back_populates="tags",
    )
