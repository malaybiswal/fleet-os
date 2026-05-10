"""Initial Fleet OS schema

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-05-10
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "trucks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("truck_id", sa.String(length=50), nullable=False, unique=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("current_location", sa.String(length=200), nullable=True),
        sa.Column("current_lat", sa.Numeric(9, 6), nullable=True),
        sa.Column("current_lon", sa.Numeric(9, 6), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_trucks_id", "trucks", ["id"])
    op.create_index("ix_trucks_truck_id", "trucks", ["truck_id"])

    op.create_table(
        "drivers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("driver_id", sa.String(length=50), nullable=False, unique=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
    )
    op.create_index("ix_drivers_id", "drivers", ["id"])
    op.create_index("ix_drivers_driver_id", "drivers", ["driver_id"])

    op.create_table(
        "loads",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("load_id", sa.String(length=50), nullable=False, unique=True),
        sa.Column("truck_id", sa.String(length=50), nullable=False),
        sa.Column("driver_id", sa.String(length=50), nullable=False),
        sa.Column("broker_name", sa.String(length=100), nullable=True),
        sa.Column("origin", sa.String(length=200), nullable=True),
        sa.Column("destination", sa.String(length=200), nullable=True),
        sa.Column("revenue", sa.Numeric(10, 2), nullable=True),
        sa.Column("miles", sa.Numeric(10, 2), nullable=True),
        sa.Column("deadhead_miles", sa.Numeric(10, 2), nullable=True),
        sa.Column("fuel_cost", sa.Numeric(10, 2), nullable=True),
        sa.Column("maintenance_reserve", sa.Numeric(10, 2), nullable=True),
        sa.Column("driver_cost", sa.Numeric(10, 2), nullable=True),
        sa.Column("tolls", sa.Numeric(10, 2), nullable=True),
        sa.Column("pickup_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivery_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(["truck_id"], ["trucks.truck_id"]),
        sa.ForeignKeyConstraint(["driver_id"], ["drivers.driver_id"]),
    )
    op.create_index("ix_loads_id", "loads", ["id"])
    op.create_index("ix_loads_load_id", "loads", ["load_id"])
    op.create_index("idx_loads_pickup", "loads", ["pickup_time"])

    op.create_table(
        "dwell_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("load_id", sa.String(length=50), nullable=False),
        sa.Column("facility_name", sa.String(length=200), nullable=True),
        sa.Column("broker_name", sa.String(length=100), nullable=True),
        sa.Column("appointment_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("arrival_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("loading_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("loading_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("departure_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("detention_pay", sa.Numeric(10, 2), nullable=True),
        sa.Column("driver_notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["load_id"], ["loads.load_id"]),
    )
    op.create_index("ix_dwell_events_id", "dwell_events", ["id"])
    op.create_index("idx_dwell_arrival", "dwell_events", ["arrival_time"])

    op.create_table(
        "telemetry_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("truck_id", sa.String(length=50), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("speed", sa.Numeric(5, 2), nullable=True),
        sa.Column("rpm", sa.Integer(), nullable=True),
        sa.Column("engine_temp", sa.Numeric(5, 2), nullable=True),
        sa.Column("fuel_level", sa.Numeric(5, 2), nullable=True),
        sa.Column("gps_lat", sa.Numeric(9, 6), nullable=True),
        sa.Column("gps_lon", sa.Numeric(9, 6), nullable=True),
        sa.Column("idle_minutes", sa.Integer(), nullable=True),
        sa.Column("reefer_temp", sa.Numeric(5, 2), nullable=True),
        sa.Column("load_weight", sa.Numeric(10, 2), nullable=True),
        sa.ForeignKeyConstraint(["truck_id"], ["trucks.truck_id"]),
    )
    op.create_index("ix_telemetry_events_id", "telemetry_events", ["id"])
    op.create_index("idx_telemetry_truck_time", "telemetry_events", ["truck_id", "timestamp"])

    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("truck_id", sa.String(length=50), nullable=False),
        sa.Column("severity", sa.String(length=10), nullable=False),
        sa.Column("alert_type", sa.String(length=50), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("resolved", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.ForeignKeyConstraint(["truck_id"], ["trucks.truck_id"]),
    )
    op.create_index("ix_alerts_id", "alerts", ["id"])
    op.create_index("idx_alerts_date_resolved", "alerts", ["created_at", "resolved"])


def downgrade() -> None:
    op.drop_index("idx_alerts_date_resolved", table_name="alerts")
    op.drop_index("ix_alerts_id", table_name="alerts")
    op.drop_table("alerts")

    op.drop_index("idx_telemetry_truck_time", table_name="telemetry_events")
    op.drop_index("ix_telemetry_events_id", table_name="telemetry_events")
    op.drop_table("telemetry_events")

    op.drop_index("idx_dwell_arrival", table_name="dwell_events")
    op.drop_index("ix_dwell_events_id", table_name="dwell_events")
    op.drop_table("dwell_events")

    op.drop_index("idx_loads_pickup", table_name="loads")
    op.drop_index("ix_loads_load_id", table_name="loads")
    op.drop_index("ix_loads_id", table_name="loads")
    op.drop_table("loads")

    op.drop_index("ix_drivers_driver_id", table_name="drivers")
    op.drop_index("ix_drivers_id", table_name="drivers")
    op.drop_table("drivers")

    op.drop_index("ix_trucks_truck_id", table_name="trucks")
    op.drop_index("ix_trucks_id", table_name="trucks")
    op.drop_table("trucks")