"""Phase 7: Add deal alerts and notification preferences tables

Revision ID: phase_7_001
Revises: 6b2c8f91d4a2
Create Date: 2025-10-30

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'phase_7_001'
down_revision = '6b2c8f91d4a2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create deal_alert_rules table
    op.create_table(
        'deal_alert_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('keywords', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('exclude_keywords', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('categories', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('condition', sa.String(length=50), nullable=True),
        sa.Column('min_price', sa.Float(), nullable=True),
        sa.Column('max_price', sa.Float(), nullable=True),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('radius_mi', sa.Integer(), nullable=True),
        sa.Column('min_deal_score', sa.Float(), nullable=True),
        sa.Column('notification_channels', sa.JSON(), nullable=False, server_default='["email"]'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('last_triggered_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_deal_alert_rules_user_id'), 'deal_alert_rules', ['user_id'], unique=False)
    op.create_index(op.f('ix_deal_alert_rules_enabled'), 'deal_alert_rules', ['enabled'], unique=False)

    # Create notification_preferences table
    op.create_table(
        'notification_preferences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('channels', sa.JSON(), nullable=False, server_default='["email"]'),
        sa.Column('frequency', sa.String(length=50), nullable=False, server_default='immediate'),
        sa.Column('digest_time', sa.String(length=5), nullable=False, server_default='09:00'),
        sa.Column('quiet_hours_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('quiet_hours_start', sa.String(length=5), nullable=True),
        sa.Column('quiet_hours_end', sa.String(length=5), nullable=True),
        sa.Column('category_filters', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('max_per_day', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('phone_number', sa.String(length=20), nullable=True),
        sa.Column('phone_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('discord_webhook_url', sa.String(length=500), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_notification_preferences_user_id')
    )

    # Create watchlist_items table
    op.create_table(
        'watchlist_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('listing_id', sa.Integer(), nullable=False),
        sa.Column('price_alert_threshold', sa.Float(), nullable=True),
        sa.Column('alert_sent', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('last_price', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['listing_id'], ['listings.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_watchlist_items_user_id'), 'watchlist_items', ['user_id'], unique=False)
    op.create_index(op.f('ix_watchlist_items_listing_id'), 'watchlist_items', ['listing_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_watchlist_items_listing_id'), table_name='watchlist_items')
    op.drop_index(op.f('ix_watchlist_items_user_id'), table_name='watchlist_items')
    op.drop_table('watchlist_items')
    op.drop_table('notification_preferences')
    op.drop_index(op.f('ix_deal_alert_rules_enabled'), table_name='deal_alert_rules')
    op.drop_index(op.f('ix_deal_alert_rules_user_id'), table_name='deal_alert_rules')
    op.drop_table('deal_alert_rules')
