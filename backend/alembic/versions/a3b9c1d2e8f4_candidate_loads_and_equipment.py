"""candidate loads and equipment type

Revision ID: a3b9c1d2e8f4
Revises: a7d1e5c83f20
Create Date: 2026-06-18 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a3b9c1d2e8f4"
down_revision: Union[str, None] = "a7d1e5c83f20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("loads", "truck_id", existing_type=sa.String(50), nullable=True)
    op.alter_column("loads", "driver_id", existing_type=sa.String(50), nullable=True)
    op.add_column("loads", sa.Column("equipment_type", sa.String(30), nullable=True))
    op.add_column("drivers", sa.Column("hos_hours_remaining", sa.Numeric(4, 1), nullable=True))


def downgrade() -> None:
    op.drop_column("drivers", "hos_hours_remaining")
    op.drop_column("loads", "equipment_type")
    op.alter_column("loads", "driver_id", existing_type=sa.String(50), nullable=False)
    op.alter_column("loads", "truck_id", existing_type=sa.String(50), nullable=False)
