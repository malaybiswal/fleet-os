"""backfill loads.source = 'demo' for pre-DAT rows

Revision ID: e1a2b3c4d5e6
Revises: d9f0a1b2c3d4
Create Date: 2026-06-26 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op


revision: str = "e1a2b3c4d5e6"
down_revision: Union[str, None] = "d9f0a1b2c3d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # All rows that predate the DAT integration are the scripted demo seed.
    # Tag them so they stay distinguishable from ingested DAT loads.
    op.execute("UPDATE loads SET source = 'demo' WHERE source IS NULL")


def downgrade() -> None:
    # Best-effort revert: only the rows we tagged in upgrade().
    op.execute("UPDATE loads SET source = NULL WHERE source = 'demo'")
