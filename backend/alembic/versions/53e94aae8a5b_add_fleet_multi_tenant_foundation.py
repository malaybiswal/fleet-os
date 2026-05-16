"""add fleet multi tenant foundation

Revision ID: 53e94aae8a5b
Revises: 001_initial_schema
Create Date: 2026-05-16 18:15:39.242224
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "53e94aae8a5b"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "fleets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_fleets_id"), "fleets", ["id"], unique=False)

    op.add_column("alerts", sa.Column("fleet_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_alerts_fleet_id"), "alerts", ["fleet_id"], unique=False)
    op.create_foreign_key(None, "alerts", "fleets", ["fleet_id"], ["id"])

    op.add_column("loads", sa.Column("fleet_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_loads_fleet_id"), "loads", ["fleet_id"], unique=False)
    op.create_foreign_key(None, "loads", "fleets", ["fleet_id"], ["id"])

    op.add_column("trucks", sa.Column("fleet_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_trucks_fleet_id"), "trucks", ["fleet_id"], unique=False)
    op.create_foreign_key(None, "trucks", "fleets", ["fleet_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint(None, "trucks", type_="foreignkey")
    op.drop_index(op.f("ix_trucks_fleet_id"), table_name="trucks")
    op.drop_column("trucks", "fleet_id")

    op.drop_constraint(None, "loads", type_="foreignkey")
    op.drop_index(op.f("ix_loads_fleet_id"), table_name="loads")
    op.drop_column("loads", "fleet_id")

    op.drop_constraint(None, "alerts", type_="foreignkey")
    op.drop_index(op.f("ix_alerts_fleet_id"), table_name="alerts")
    op.drop_column("alerts", "fleet_id")

    op.drop_index(op.f("ix_fleets_id"), table_name="fleets")
    op.drop_table("fleets")