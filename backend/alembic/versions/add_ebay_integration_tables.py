"""Add seller integrations and crosspost results tables

Revision ID: add_ebay_integration_tables
Revises: phase_7_add_deal_alerts_and_notifications
Create Date: 2025-11-06 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_ebay_integration_tables'
down_revision = 'phase_7_add_deal_alerts_and_notifications'
branch_labels = None
depends_on = None


def upgrade():
    # Create seller_integrations table
    op.create_table(
        'seller_integrations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('seller_id', sa.Integer(), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('access_token', sa.Text(), nullable=False),
        sa.Column('refresh_token', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('marketplace_id', sa.String(length=50), nullable=True),
        sa.Column('location_key', sa.String(length=255), nullable=True),
        sa.Column('payment_policy_id', sa.String(length=255), nullable=True),
        sa.Column('fulfillment_policy_id', sa.String(length=255), nullable=True),
        sa.Column('return_policy_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['seller_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('seller_id', 'provider', name='uq_seller_provider')
    )
    op.create_index(op.f('ix_seller_integrations_seller_id'), 'seller_integrations', ['seller_id'], unique=False)
    op.create_index(op.f('ix_seller_integrations_provider'), 'seller_integrations', ['provider'], unique=False)

    # Create crosspost_results table
    op.create_table(
        'crosspost_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('listing_id', sa.Integer(), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('provider_offer_id', sa.String(length=255), nullable=True),
        sa.Column('provider_item_id', sa.String(length=255), nullable=True),
        sa.Column('provider_url', sa.String(length=500), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('raw_response', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['listing_id'], ['listings.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_crosspost_results_listing_id'), 'crosspost_results', ['listing_id'], unique=False)
    op.create_index(op.f('ix_crosspost_results_provider'), 'crosspost_results', ['provider'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_crosspost_results_provider'), table_name='crosspost_results')
    op.drop_index(op.f('ix_crosspost_results_listing_id'), table_name='crosspost_results')
    op.drop_table('crosspost_results')

    op.drop_index(op.f('ix_seller_integrations_provider'), table_name='seller_integrations')
    op.drop_index(op.f('ix_seller_integrations_seller_id'), table_name='seller_integrations')
    op.drop_table('seller_integrations')
