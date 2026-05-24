"""enable pg_trgm and add GIN indexes for fuzzy carrier search

Revision ID: b1d4e7f92a03
Revises: 3ac2852cd6cc
Create Date: 2026-05-24 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op

revision: str = "b1d4e7f92a03"
down_revision: Union[str, None] = "3ac2852cd6cc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute(
        "CREATE INDEX ix_carriers_legal_name_trgm "
        "ON carriers USING GIN (legal_name gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX ix_carriers_dba_name_trgm "
        "ON carriers USING GIN (dba_name gin_trgm_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_carriers_legal_name_trgm")
    op.execute("DROP INDEX IF EXISTS ix_carriers_dba_name_trgm")
    # pg_trgm extension is intentionally left in place —
    # other tables or indexes may depend on it.
