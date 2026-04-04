"""feature pack: expenses, settings, vouchers, tickets, ip_pools, audit_logs, plan FUP, customer geo, payment methods, router maintenance

Revision ID: 005_feature_pack
Revises: 004_multi_router
Create Date: 2026-04-04
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '005_feature_pack'
down_revision = '004_multi_router'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Expenses
    op.create_table(
        'expenses',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('category', sa.String(20), nullable=False),
        sa.Column('description', sa.String(255), nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('receipt_number', sa.String(100), nullable=True),
        sa.Column('recorded_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # App Settings
    op.create_table(
        'app_settings',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('key', sa.String(100), unique=True, nullable=False),
        sa.Column('value', sa.Text(), nullable=False, server_default=''),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Vouchers
    op.create_table(
        'vouchers',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(20), unique=True, nullable=False),
        sa.Column('plan_id', UUID(as_uuid=True), sa.ForeignKey('plans.id'), nullable=False),
        sa.Column('duration_days', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='unused'),
        sa.Column('customer_id', UUID(as_uuid=True), sa.ForeignKey('customers.id'), nullable=True),
        sa.Column('activated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('batch_id', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Tickets
    op.create_table(
        'tickets',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', UUID(as_uuid=True), sa.ForeignKey('customers.id'), nullable=False),
        sa.Column('subject', sa.String(200), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='open'),
        sa.Column('priority', sa.String(20), nullable=False, server_default='medium'),
        sa.Column('assigned_to', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        'ticket_messages',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('ticket_id', UUID(as_uuid=True), sa.ForeignKey('tickets.id'), nullable=False),
        sa.Column('sender_type', sa.String(10), nullable=False),
        sa.Column('sender_id', UUID(as_uuid=True), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # IP Pools
    op.create_table(
        'ip_pools',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('router_id', UUID(as_uuid=True), sa.ForeignKey('routers.id'), nullable=False),
        sa.Column('range_start', sa.String(15), nullable=False),
        sa.Column('range_end', sa.String(15), nullable=False),
        sa.Column('subnet', sa.String(18), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Audit Logs
    op.create_table(
        'audit_logs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', UUID(as_uuid=True), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Plan: add FUP fields
    op.add_column('plans', sa.Column('data_cap_gb', sa.Integer(), nullable=True))
    op.add_column('plans', sa.Column('fup_download_mbps', sa.Integer(), nullable=True))
    op.add_column('plans', sa.Column('fup_upload_mbps', sa.Integer(), nullable=True))

    # Customer: add geo fields
    op.add_column('customers', sa.Column('latitude', sa.Float(), nullable=True))
    op.add_column('customers', sa.Column('longitude', sa.Float(), nullable=True))

    # Router: add maintenance fields
    op.add_column('routers', sa.Column('maintenance_mode', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('routers', sa.Column('maintenance_message', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('routers', 'maintenance_message')
    op.drop_column('routers', 'maintenance_mode')
    op.drop_column('customers', 'longitude')
    op.drop_column('customers', 'latitude')
    op.drop_column('plans', 'fup_upload_mbps')
    op.drop_column('plans', 'fup_download_mbps')
    op.drop_column('plans', 'data_cap_gb')
    op.drop_table('audit_logs')
    op.drop_table('ip_pools')
    op.drop_table('ticket_messages')
    op.drop_table('tickets')
    op.drop_table('vouchers')
    op.drop_table('app_settings')
    op.drop_table('expenses')
