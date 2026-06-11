"""add facilities table and dwell_events.facility_id

Revision ID: a7d1e5c83f20
Revises: f57b2d4c9a11
Create Date: 2026-06-11 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "a7d1e5c83f20"
down_revision: Union[str, None] = "f57b2d4c9a11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "facilities",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("fleet_id", sa.Integer(), sa.ForeignKey("fleets.id"), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("normalized_name", sa.String(length=200), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("state", sa.String(length=2), nullable=True),
        sa.Column("latitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("longitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("facility_type", sa.String(length=50), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "fleet_id", "normalized_name", name="uq_facilities_fleet_normalized_name"
        ),
    )
    op.create_index("idx_facilities_fleet_id", "facilities", ["fleet_id"])

    op.add_column(
        "dwell_events",
        sa.Column("facility_id", sa.Integer(), sa.ForeignKey("facilities.id"), nullable=True),
    )
    op.create_index("idx_dwell_events_facility_id", "dwell_events", ["facility_id"])

    # Backfill facilities from existing dwell_events.facility_name values.
    # Fleet is resolved through the loads join because dwell_events.fleet_id is nullable.
    op.execute(
        """
        INSERT INTO facilities (fleet_id, name, normalized_name)
        SELECT DISTINCT ON (COALESCE(de.fleet_id, l.fleet_id), lower(regexp_replace(trim(de.facility_name), '\\s+', ' ', 'g')))
            COALESCE(de.fleet_id, l.fleet_id),
            de.facility_name,
            lower(regexp_replace(trim(de.facility_name), '\\s+', ' ', 'g'))
        FROM dwell_events de
        JOIN loads l ON l.load_id = de.load_id
        WHERE de.facility_name IS NOT NULL
          AND COALESCE(de.fleet_id, l.fleet_id) IS NOT NULL
        """
    )
    op.execute(
        """
        UPDATE dwell_events de
        SET facility_id = f.id
        FROM loads l, facilities f
        WHERE l.load_id = de.load_id
          AND de.facility_name IS NOT NULL
          AND f.fleet_id = COALESCE(de.fleet_id, l.fleet_id)
          AND f.normalized_name = lower(regexp_replace(trim(de.facility_name), '\\s+', ' ', 'g'))
        """
    )


def downgrade() -> None:
    op.drop_index("idx_dwell_events_facility_id", table_name="dwell_events")
    op.drop_column("dwell_events", "facility_id")
    op.drop_index("idx_facilities_fleet_id", table_name="facilities")
    op.drop_table("facilities")
