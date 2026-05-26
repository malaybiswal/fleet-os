"""add_heading_to_telemetry_events

Revision ID: dd2284423348
Revises: c4e9b7d2a6f1
Create Date: 2026-05-26 03:10:44.091311

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "dd2284423348"
down_revision: Union[str, None] = "c4e9b7d2a6f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "telemetry_events",
        sa.Column("heading", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("telemetry_events", "heading")
