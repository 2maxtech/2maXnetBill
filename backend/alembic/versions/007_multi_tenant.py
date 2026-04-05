"""add owner_id column to all data tables for multi-tenant isolation

Revision ID: 007_multi_tenant
Revises: 006_saas_registration
Create Date: 2026-04-04
"""
from alembic import op
import sqlalchemy as sa

revision = '007_multi_tenant'
down_revision = '006_saas_registration'
branch_labels = None
depends_on = None

# All tables that need an owner_id column
TABLES = [
    'customers',
    'plans',
    'invoices',
    'payments',
    'routers',
    'areas',
    'expenses',
    'vouchers',
    'tickets',
    'ticket_messages',
    'ip_pools',
    'audit_logs',
    'app_settings',
    'notifications',
    'disconnect_logs',
]


def upgrade() -> None:
    for table in TABLES:
        op.add_column(
            table,
            sa.Column('owner_id', sa.UUID(), sa.ForeignKey('users.id'), nullable=True),
        )


def downgrade() -> None:
    for table in TABLES:
        op.drop_column(table, 'owner_id')
