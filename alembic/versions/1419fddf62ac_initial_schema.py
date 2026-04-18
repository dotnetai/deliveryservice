"""initial_schema

Revision ID: 1419fddf62ac
Revises: 
Create Date: 2026-04-16 01:09:20.021717

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1419fddf62ac'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables for the schema (public or tenant)."""
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=25), nullable=True),
        sa.Column('email', sa.String(length=70), nullable=True),
        sa.Column('password', sa.Text(), nullable=True),
        sa.Column('is_staff', sa.Boolean(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username'),
    )
    op.create_table(
        'products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=True),
        sa.Column('price', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('order_statuses', sa.String(length=20), nullable=True, server_default='PENDING'),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('product_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('orders')
    op.drop_table('products')
    op.drop_table('users')
