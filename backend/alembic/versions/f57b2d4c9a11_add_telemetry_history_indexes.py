"""add telemetry history indexes

Revision ID: f57b2d4c9a11
Revises: dd2284423348
Create Date: 2026-05-27 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op


revision: str = "f57b2d4c9a11"
down_revision: Union[str, None] = "dd2284423348"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "idx_telemetry_fleet_time",
        "telemetry_events",
        ["fleet_id", "timestamp"],
        unique=False,
    )
    op.create_index(
        "idx_alerts_fleet_created_at",
        "alerts",
        ["fleet_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_alerts_fleet_created_at", table_name="alerts")
    op.drop_index("idx_telemetry_fleet_time", table_name="telemetry_events")
