"""fix app_settings unique constraint for multi-tenant

Revision ID: 010_settings_unique
Revises: 009_billing_due_day
Create Date: 2026-04-05
"""
from alembic import op

revision = '010_settings_unique'
down_revision = '009_billing_due_day'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop old single-column unique constraint
    op.drop_constraint('app_settings_key_key', 'app_settings', type_='unique')
    # Add composite unique on (key, owner_id)
    op.create_unique_constraint('uq_app_settings_key_owner', 'app_settings', ['key', 'owner_id'])


def downgrade() -> None:
    op.drop_constraint('uq_app_settings_key_owner', 'app_settings', type_='unique')
    op.create_unique_constraint('app_settings_key_key', 'app_settings', ['key'])
