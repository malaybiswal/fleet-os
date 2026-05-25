"""add carrier lead scores

Revision ID: c4e9b7d2a6f1
Revises: b1d4e7f92a03
Create Date: 2026-05-25 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4e9b7d2a6f1"
down_revision: Union[str, None] = "b1d4e7f92a03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("carriers", sa.Column("lead_score", sa.Integer(), nullable=True))
    op.create_index("ix_carriers_lead_score", "carriers", ["lead_score"])
    op.add_column(
        "carrier_snapshots",
        sa.Column("lead_score", sa.Integer(), nullable=True),
    )

    op.execute(
        """
        UPDATE carriers
        SET lead_score = LEAST(100, GREATEST(0,
            CASE
                WHEN upper(coalesce(state, '')) IN ('TX', 'CA', 'FL', 'GA', 'IL', 'OH', 'PA', 'NC', 'TN', 'AZ') THEN 15
                WHEN upper(coalesce(state, '')) IN ('IN', 'MO', 'WI', 'MI', 'NJ', 'VA', 'SC', 'KY', 'OK', 'AR') THEN 8
                ELSE 0
              END
            + CASE
                WHEN lower(coalesce(cargo_types::text, '')) LIKE ANY (ARRAY[
                    '%refrigerated_food%',
                    '%refrigerated food%',
                    '%reefer%',
                    '%fresh_produce%',
                    '%fresh produce%',
                    '%produce%',
                    '%meat%',
                    '%beverages%'
                ]) THEN 20
                WHEN lower(coalesce(cargo_types::text, '')) LIKE ANY (ARRAY[
                    '%general_freight%',
                    '%general freight%',
                    '%building_materials%',
                    '%building materials%',
                    '%paper_products%',
                    '%paper products%',
                    '%retail goods%',
                    '%retail_goods%'
                ]) THEN 10
                ELSE 0
              END
            + CASE
                WHEN power_units BETWEEN 1 AND 4 THEN 8
                WHEN power_units BETWEEN 5 AND 25 THEN 20
                WHEN power_units BETWEEN 26 AND 50 THEN 12
                WHEN power_units BETWEEN 51 AND 100 THEN 3
                ELSE 0
              END
            + CASE
                WHEN nullif(btrim(coalesce(phone, '')), '') IS NOT NULL
                 AND nullif(btrim(coalesce(email, '')), '') IS NOT NULL THEN 20
                WHEN nullif(btrim(coalesce(email, '')), '') IS NOT NULL THEN 12
                WHEN nullif(btrim(coalesce(phone, '')), '') IS NOT NULL THEN 8
                ELSE 0
              END
            + CASE
                WHEN lower(coalesce(authority_status, '')) = 'active' THEN 10
                WHEN lower(coalesce(authority_status, '')) = 'pending' THEN 3
                ELSE 0
              END
            + CASE
                WHEN authority_date IS NOT NULL
                 AND authority_date >= CURRENT_DATE - INTERVAL '365 days' THEN 15
                WHEN authority_date IS NOT NULL
                 AND authority_date >= CURRENT_DATE - INTERVAL '3 years' THEN 10
                WHEN authority_date IS NOT NULL
                 AND authority_date >= CURRENT_DATE - INTERVAL '5 years' THEN 5
                ELSE 0
              END
        ))
        """
    )

    op.execute(
        """
        UPDATE carrier_snapshots AS snapshot
        SET lead_score = LEAST(100, GREATEST(0,
            CASE
                WHEN upper(coalesce(carrier.state, '')) IN ('TX', 'CA', 'FL', 'GA', 'IL', 'OH', 'PA', 'NC', 'TN', 'AZ') THEN 15
                WHEN upper(coalesce(carrier.state, '')) IN ('IN', 'MO', 'WI', 'MI', 'NJ', 'VA', 'SC', 'KY', 'OK', 'AR') THEN 8
                ELSE 0
              END
            + CASE
                WHEN lower(coalesce(snapshot.cargo_types::text, carrier.cargo_types::text, '')) LIKE ANY (ARRAY[
                    '%refrigerated_food%',
                    '%refrigerated food%',
                    '%reefer%',
                    '%fresh_produce%',
                    '%fresh produce%',
                    '%produce%',
                    '%meat%',
                    '%beverages%'
                ]) THEN 20
                WHEN lower(coalesce(snapshot.cargo_types::text, carrier.cargo_types::text, '')) LIKE ANY (ARRAY[
                    '%general_freight%',
                    '%general freight%',
                    '%building_materials%',
                    '%building materials%',
                    '%paper_products%',
                    '%paper products%',
                    '%retail goods%',
                    '%retail_goods%'
                ]) THEN 10
                ELSE 0
              END
            + CASE
                WHEN coalesce(snapshot.power_units, carrier.power_units) BETWEEN 1 AND 4 THEN 8
                WHEN coalesce(snapshot.power_units, carrier.power_units) BETWEEN 5 AND 25 THEN 20
                WHEN coalesce(snapshot.power_units, carrier.power_units) BETWEEN 26 AND 50 THEN 12
                WHEN coalesce(snapshot.power_units, carrier.power_units) BETWEEN 51 AND 100 THEN 3
                ELSE 0
              END
            + CASE
                WHEN nullif(btrim(coalesce(carrier.phone, '')), '') IS NOT NULL
                 AND nullif(btrim(coalesce(carrier.email, '')), '') IS NOT NULL THEN 20
                WHEN nullif(btrim(coalesce(carrier.email, '')), '') IS NOT NULL THEN 12
                WHEN nullif(btrim(coalesce(carrier.phone, '')), '') IS NOT NULL THEN 8
                ELSE 0
              END
            + CASE
                WHEN lower(coalesce(snapshot.authority_status, carrier.authority_status, '')) = 'active' THEN 10
                WHEN lower(coalesce(snapshot.authority_status, carrier.authority_status, '')) = 'pending' THEN 3
                ELSE 0
              END
            + CASE
                WHEN carrier.authority_date IS NOT NULL
                 AND carrier.authority_date >= CURRENT_DATE - INTERVAL '365 days' THEN 15
                WHEN carrier.authority_date IS NOT NULL
                 AND carrier.authority_date >= CURRENT_DATE - INTERVAL '3 years' THEN 10
                WHEN carrier.authority_date IS NOT NULL
                 AND carrier.authority_date >= CURRENT_DATE - INTERVAL '5 years' THEN 5
                ELSE 0
              END
        ))
        FROM carriers AS carrier
        WHERE snapshot.carrier_id = carrier.id
        """
    )


def downgrade() -> None:
    op.drop_column("carrier_snapshots", "lead_score")
    op.drop_index("ix_carriers_lead_score", table_name="carriers")
    op.drop_column("carriers", "lead_score")
