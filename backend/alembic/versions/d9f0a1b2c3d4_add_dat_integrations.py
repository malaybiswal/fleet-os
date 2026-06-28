"""add DAT integrations

Revision ID: d9f0a1b2c3d4
Revises: b4c2d6e7f8a9
Create Date: 2026-06-26 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d9f0a1b2c3d4"
down_revision: Union[str, None] = "b4c2d6e7f8a9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "fleet_integrations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("fleet_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("encrypted_credentials", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["fleet_id"], ["fleets.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("fleet_id", "provider", name="uq_fleet_integrations_fleet_provider"),
    )
    op.create_index(op.f("ix_fleet_integrations_id"), "fleet_integrations", ["id"], unique=False)
    op.create_index(op.f("ix_fleet_integrations_fleet_id"), "fleet_integrations", ["fleet_id"], unique=False)

    op.add_column("loads", sa.Column("source", sa.String(length=40), nullable=True))
    op.add_column("loads", sa.Column("external_ref", sa.String(length=120), nullable=True))
    op.add_column("loads", sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f("ix_loads_source"), "loads", ["source"], unique=False)
    op.create_index(op.f("ix_loads_external_ref"), "loads", ["external_ref"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_loads_external_ref"), table_name="loads")
    op.drop_index(op.f("ix_loads_source"), table_name="loads")
    op.drop_column("loads", "last_synced_at")
    op.drop_column("loads", "external_ref")
    op.drop_column("loads", "source")

    op.drop_index(op.f("ix_fleet_integrations_fleet_id"), table_name="fleet_integrations")
    op.drop_index(op.f("ix_fleet_integrations_id"), table_name="fleet_integrations")
    op.drop_table("fleet_integrations")
