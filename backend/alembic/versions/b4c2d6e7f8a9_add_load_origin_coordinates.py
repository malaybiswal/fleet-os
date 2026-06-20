"""add load origin coordinates

Revision ID: b4c2d6e7f8a9
Revises: a3b9c1d2e8f4
Create Date: 2026-06-18 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b4c2d6e7f8a9"
down_revision: Union[str, None] = "a3b9c1d2e8f4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("loads", sa.Column("origin_lat", sa.Numeric(9, 6), nullable=True))
    op.add_column("loads", sa.Column("origin_lon", sa.Numeric(9, 6), nullable=True))


def downgrade() -> None:
    op.drop_column("loads", "origin_lon")
    op.drop_column("loads", "origin_lat")
