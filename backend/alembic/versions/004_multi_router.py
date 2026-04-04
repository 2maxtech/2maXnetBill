"""add routers and areas tables, link customers

Revision ID: 004_multi_router
Revises: 003_mikrotik
Create Date: 2026-04-04
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '004_multi_router'
down_revision = '003_mikrotik'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'routers',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('url', sa.String(255), nullable=False),
        sa.Column('username', sa.String(100), nullable=False, server_default='admin'),
        sa.Column('password', sa.String(255), nullable=False, server_default=''),
        sa.Column('location', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        'areas',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('router_id', UUID(as_uuid=True), sa.ForeignKey('routers.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.add_column('customers', sa.Column('router_id', UUID(as_uuid=True), sa.ForeignKey('routers.id'), nullable=True))
    op.add_column('customers', sa.Column('area_id', UUID(as_uuid=True), sa.ForeignKey('areas.id'), nullable=True))


def downgrade() -> None:
    op.drop_column('customers', 'area_id')
    op.drop_column('customers', 'router_id')
    op.drop_table('areas')
    op.drop_table('routers')
