from datetime import date, datetime
from enum import Enum

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


class OutreachStatus(str, Enum):
    not_contacted = "not_contacted"
    contacted = "contacted"
    follow_up = "follow_up"
    not_interested = "not_interested"
    converted = "converted"


# Association table for the many-to-many Carrier <-> Tag relationship.
# Each row means "this carrier has this tag"; it is not a full ORM model class.
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
    # Index speeds lookups by carrier/tag and unique=True prevents duplicate tag
    # assignments.
    Index("ix_carrier_tags_carrier_id_tag_id", "carrier_id", "tag_id", unique=True),
)


class Carrier(Base):
    __tablename__ = "carriers"
    __table_args__ = (
        # Indexes make common WHERE filters faster; unique=True also enforces one
        # carrier per DOT number.
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

    # Relationships describe how SQLAlchemy loads linked rows; cascade deletes
    # child rows with the carrier.
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
        # secondary tells SQLAlchemy to connect carriers and tags through the
        # carrier_tags table.
        secondary=carrier_tags,
        back_populates="carriers",
    )


class CarrierSnapshot(Base):
    __tablename__ = "carrier_snapshots"
    __table_args__ = (
        # One snapshot per carrier per day; upsert code depends on this pairing
        # being unique.
        UniqueConstraint("carrier_id", "snapshot_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    carrier_id: Mapped[int] = mapped_column(
        # ForeignKey links this row to carriers.id; CASCADE deletes snapshots
        # when carrier is deleted.
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
        # ForeignKey links this row to carriers.id; CASCADE deletes notes when
        # carrier is deleted.
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
        # Same many-to-many link as Carrier.tags, viewed from the Tag side.
        secondary=carrier_tags,
        back_populates="tags",
    )
