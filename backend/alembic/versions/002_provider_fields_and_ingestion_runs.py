"""Add provider fields to trucks/drivers/telemetry and create ingestion_runs

Revision ID: 002_provider_fields_and_ingestion_runs
Revises: 001_initial_schema
Create Date: 2026-05-16
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002_provider_fields_and_ingestion_runs"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── trucks ────────────────────────────────────────────────────────────
    op.add_column("trucks", sa.Column("provider", sa.String(50), nullable=True))
    op.add_column("trucks", sa.Column("provider_id", sa.String(200), nullable=True))
    op.add_column("trucks", sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(
        "uix_trucks_provider_id",
        "trucks",
        ["provider", "provider_id"],
        unique=True,
        postgresql_where=sa.text("provider IS NOT NULL"),
    )

    # ── drivers ───────────────────────────────────────────────────────────
    op.add_column("drivers", sa.Column("provider", sa.String(50), nullable=True))
    op.add_column("drivers", sa.Column("provider_id", sa.String(200), nullable=True))
    op.add_column("drivers", sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(
        "uix_drivers_provider_id",
        "drivers",
        ["provider", "provider_id"],
        unique=True,
        postgresql_where=sa.text("provider IS NOT NULL"),
    )

    # ── telemetry_events ──────────────────────────────────────────────────
    op.add_column("telemetry_events", sa.Column("provider", sa.String(50), nullable=True))
    op.add_column("telemetry_events", sa.Column("provider_id", sa.String(200), nullable=True))
    op.add_column("telemetry_events", sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(
        "uix_telemetry_provider_id",
        "telemetry_events",
        ["provider", "provider_id"],
        unique=True,
        postgresql_where=sa.text("provider IS NOT NULL"),
    )

    # ── ingestion_runs ────────────────────────────────────────────────────
    op.create_table(
        "ingestion_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("records_fetched", sa.Integer(), nullable=True),
        sa.Column("records_upserted", sa.Integer(), nullable=True),
        sa.Column("cursor_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cursor_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
    )
    op.create_index("ix_ingestion_runs_id", "ingestion_runs", ["id"])
    op.create_index(
        "idx_ingestion_runs_provider_entity",
        "ingestion_runs",
        ["provider", "entity_type", "status"],
    )


def downgrade() -> None:
    op.drop_index("idx_ingestion_runs_provider_entity", table_name="ingestion_runs")
    op.drop_index("ix_ingestion_runs_id", table_name="ingestion_runs")
    op.drop_table("ingestion_runs")

    op.drop_index("uix_telemetry_provider_id", table_name="telemetry_events")
    op.drop_column("telemetry_events", "ingested_at")
    op.drop_column("telemetry_events", "provider_id")
    op.drop_column("telemetry_events", "provider")

    op.drop_index("uix_drivers_provider_id", table_name="drivers")
    op.drop_column("drivers", "ingested_at")
    op.drop_column("drivers", "provider_id")
    op.drop_column("drivers", "provider")

    op.drop_index("uix_trucks_provider_id", table_name="trucks")
    op.drop_column("trucks", "ingested_at")
    op.drop_column("trucks", "provider_id")
    op.drop_column("trucks", "provider")
