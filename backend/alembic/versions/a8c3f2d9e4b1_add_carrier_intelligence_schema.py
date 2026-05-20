"""add carrier intelligence schema

Revision ID: a8c3f2d9e4b1
Revises: e690caabc854
Create Date: 2026-05-20 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a8c3f2d9e4b1"
down_revision: Union[str, None] = "e690caabc854"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "carriers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("dot_number", sa.String(length=50), nullable=False),
        sa.Column("mc_number", sa.String(length=50), nullable=True),
        sa.Column("legal_name", sa.String(length=200), nullable=False),
        sa.Column("dba_name", sa.String(length=200), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("address_line1", sa.String(length=255), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("state", sa.String(length=2), nullable=True),
        sa.Column("postal_code", sa.String(length=20), nullable=True),
        sa.Column("country", sa.String(length=50), nullable=True),
        sa.Column("authority_status", sa.String(length=50), nullable=True),
        sa.Column("authority_date", sa.Date(), nullable=True),
        sa.Column("power_units", sa.Integer(), nullable=True),
        sa.Column("driver_count", sa.Integer(), nullable=True),
        sa.Column("cargo_types", sa.JSON(), nullable=True),
        sa.Column(
            "outreach_status",
            sa.String(length=30),
            server_default="not_contacted",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_carriers_dot_number", "carriers", ["dot_number"], unique=True)
    op.create_index("ix_carriers_mc_number", "carriers", ["mc_number"])
    op.create_index("ix_carriers_state", "carriers", ["state"])
    op.create_index(
        "ix_carriers_state_authority_status",
        "carriers",
        ["state", "authority_status"],
    )
    op.create_index("ix_carriers_power_units", "carriers", ["power_units"])
    op.create_index("ix_carriers_outreach_status", "carriers", ["outreach_status"])

    op.create_table(
        "carrier_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("carrier_id", sa.Integer(), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("power_units", sa.Integer(), nullable=True),
        sa.Column("driver_count", sa.Integer(), nullable=True),
        sa.Column("authority_status", sa.String(length=50), nullable=True),
        sa.Column("cargo_types", sa.JSON(), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["carrier_id"], ["carriers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("carrier_id", "snapshot_date"),
    )

    op.create_table(
        "outreach_notes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("carrier_id", sa.Integer(), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("outcome", sa.String(length=100), nullable=True),
        sa.Column("follow_up_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("contact_name", sa.String(length=100), nullable=True),
        sa.Column("dispatcher_name", sa.String(length=100), nullable=True),
        sa.Column("pain_points", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(length=100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["carrier_id"], ["carriers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_outreach_notes_follow_up_date",
        "outreach_notes",
        ["follow_up_date"],
    )

    op.create_table(
        "tags",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tags_name", "tags", ["name"], unique=True)

    op.create_table(
        "carrier_tags",
        sa.Column("carrier_id", sa.Integer(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["carrier_id"], ["carriers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("carrier_id", "tag_id"),
    )
    op.create_index(
        "ix_carrier_tags_carrier_id_tag_id",
        "carrier_tags",
        ["carrier_id", "tag_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_carrier_tags_carrier_id_tag_id", table_name="carrier_tags")
    op.drop_table("carrier_tags")

    op.drop_index("ix_tags_name", table_name="tags")
    op.drop_table("tags")

    op.drop_index("ix_outreach_notes_follow_up_date", table_name="outreach_notes")
    op.drop_table("outreach_notes")

    op.drop_table("carrier_snapshots")

    op.drop_index("ix_carriers_outreach_status", table_name="carriers")
    op.drop_index("ix_carriers_power_units", table_name="carriers")
    op.drop_index("ix_carriers_state_authority_status", table_name="carriers")
    op.drop_index("ix_carriers_state", table_name="carriers")
    op.drop_index("ix_carriers_mc_number", table_name="carriers")
    op.drop_index("ix_carriers_dot_number", table_name="carriers")
    op.drop_table("carriers")
