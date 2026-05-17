"""add fleet id to drivers telemetry dwell

Revision ID: e690caabc854
Revises: 53e94aae8a5b
Create Date: 2026-05-17 17:02:48.155875

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e690caabc854'
down_revision: Union[str, None] = '53e94aae8a5b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("drivers", sa.Column("fleet_id", sa.Integer(), nullable=True))
    op.create_index(
        op.f("ix_drivers_fleet_id"),
        "drivers",
        ["fleet_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_drivers_fleet_id_fleets",
        "drivers",
        "fleets",
        ["fleet_id"],
        ["id"],
    )

    op.add_column("dwell_events", sa.Column("fleet_id", sa.Integer(), nullable=True))
    op.create_index(
        op.f("ix_dwell_events_fleet_id"),
        "dwell_events",
        ["fleet_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_dwell_events_fleet_id_fleets",
        "dwell_events",
        "fleets",
        ["fleet_id"],
        ["id"],
    )

    op.add_column("telemetry_events", sa.Column("fleet_id", sa.Integer(), nullable=True))
    op.create_index(
        op.f("ix_telemetry_events_fleet_id"),
        "telemetry_events",
        ["fleet_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_telemetry_events_fleet_id_fleets",
        "telemetry_events",
        "fleets",
        ["fleet_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_telemetry_events_fleet_id_fleets",
        "telemetry_events",
        type_="foreignkey",
    )
    op.drop_index(op.f("ix_telemetry_events_fleet_id"), table_name="telemetry_events")
    op.drop_column("telemetry_events", "fleet_id")

    op.drop_constraint(
        "fk_dwell_events_fleet_id_fleets",
        "dwell_events",
        type_="foreignkey",
    )
    op.drop_index(op.f("ix_dwell_events_fleet_id"), table_name="dwell_events")
    op.drop_column("dwell_events", "fleet_id")

    op.drop_constraint(
        "fk_drivers_fleet_id_fleets",
        "drivers",
        type_="foreignkey",
    )
    op.drop_index(op.f("ix_drivers_fleet_id"), table_name="drivers")
    op.drop_column("drivers", "fleet_id")