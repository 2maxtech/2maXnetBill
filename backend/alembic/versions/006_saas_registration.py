"""add SaaS registration fields: super_admin role, company_name, full_name, phone on users

Revision ID: 006_saas_registration
Revises: 005_feature_pack
Create Date: 2026-04-04
"""
from alembic import op
import sqlalchemy as sa

revision = '006_saas_registration'
down_revision = '005_feature_pack'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new profile columns to users table
    op.add_column('users', sa.Column('full_name', sa.String(150), nullable=True))
    op.add_column('users', sa.Column('company_name', sa.String(200), nullable=True))
    op.add_column('users', sa.Column('phone', sa.String(30), nullable=True))

    # Extend the role enum to include super_admin
    # PostgreSQL requires explicit ALTER TYPE for enum extension
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'super_admin' BEFORE 'admin'")


def downgrade() -> None:
    op.drop_column('users', 'phone')
    op.drop_column('users', 'company_name')
    op.drop_column('users', 'full_name')
    # Note: PostgreSQL does not support removing enum values; manual intervention required
