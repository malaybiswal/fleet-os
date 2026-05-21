"""add users table

Revision ID: 3ac2852cd6cc
Revises: a8c3f2d9e4b1
Create Date: 2026-05-21 05:01:27.885131

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3ac2852cd6cc'
down_revision: Union[str, None] = 'a8c3f2d9e4b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('firebase_uid', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('fleet_id', sa.Integer(), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['fleet_id'], ['fleets.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_index(
        op.f('ix_users_email'),
        'users',
        ['email'],
        unique=True,
    )

    op.create_index(
        op.f('ix_users_firebase_uid'),
        'users',
        ['firebase_uid'],
        unique=True,
    )

    op.create_index(
        op.f('ix_users_fleet_id'),
        'users',
        ['fleet_id'],
        unique=False,
    )

    op.create_index(
        op.f('ix_users_id'),
        'users',
        ['id'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_fleet_id'), table_name='users')
    op.drop_index(op.f('ix_users_firebase_uid'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')