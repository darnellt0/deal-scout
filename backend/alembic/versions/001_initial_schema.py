"""Initial schema creation.

Revision ID: 001_initial_schema
Revises: 000_create_users_table
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = '000_create_users_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all tables from models."""
    # This migration uses SQLAlchemy's metadata.create_all
    # In production, you may want to break this into smaller migrations
    # or generate more explicit migrations using autogenerate

    # Create enum types
    op.execute("""
        CREATE TYPE condition_enum AS ENUM (
            'poor', 'fair', 'good', 'great', 'excellent'
        )
    """)

    # Create listings table
    op.create_table(
        'listings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(50), nullable=False),
        sa.Column('source_id', sa.String(120), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('condition', sa.Enum('poor', 'fair', 'good', 'great', 'excellent', name='condition_enum'), nullable=True),
        sa.Column('category', sa.String(120), nullable=True),
        sa.Column('url', sa.String(500), nullable=False),
        sa.Column('thumbnail_url', sa.String(500), nullable=True),
        sa.Column('location', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_seen_at', sa.DateTime(), nullable=False),
        sa.Column('available', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source_id', name='uq_source_id'),
    )
    op.create_index('ix_listings_source', 'listings', ['source'])
    op.create_index('ix_listings_source_id', 'listings', ['source_id'])
    op.create_index('ix_listings_category', 'listings', ['category'])

    # Create listing_scores table
    op.create_table(
        'listing_scores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('listing_id', sa.Integer(), nullable=False),
        sa.Column('metric', sa.String(50), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('snapshot', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['listing_id'], ['listings.id']),
        sa.UniqueConstraint('listing_id', 'metric', name='uq_listing_metric'),
    )
    op.create_index('ix_listing_scores_listing_id', 'listing_scores', ['listing_id'])

    # Create comps table
    op.create_table(
        'comps',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(120), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('condition', sa.Enum('poor', 'fair', 'good', 'great', 'excellent', name='condition_enum'), nullable=True),
        sa.Column('source', sa.String(50), nullable=False),
        sa.Column('observed_at', sa.DateTime(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_comps_category', 'comps', ['category'])

    # Create user_prefs table
    op.create_table(
        'user_prefs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(64), nullable=False),
        sa.Column('radius_mi', sa.Integer(), nullable=False),
        sa.Column('city', sa.String(255), nullable=False),
        sa.Column('min_condition', sa.Enum('poor', 'fair', 'good', 'great', 'excellent', name='condition_enum'), nullable=False),
        sa.Column('max_price_couch', sa.Float(), nullable=False),
        sa.Column('max_price_kitchen_island', sa.Float(), nullable=False),
        sa.Column('keywords_include', sa.JSON(), nullable=False),
        sa.Column('notify_channels', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )

    # Create notifications table
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('listing_id', sa.Integer(), nullable=True),
        sa.Column('channel', sa.String(50), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['listing_id'], ['listings.id']),
    )

    # Create my_items table
    op.create_table(
        'my_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('category', sa.String(120), nullable=False),
        sa.Column('attributes', sa.JSON(), nullable=False),
        sa.Column('condition', sa.Enum('poor', 'fair', 'good', 'great', 'excellent', name='condition_enum'), nullable=True),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create marketplace_accounts table
    op.create_table(
        'marketplace_accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('connected', sa.Boolean(), nullable=False),
        sa.Column('credentials', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create cross_posts table
    op.create_table(
        'cross_posts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('my_item_id', sa.Integer(), nullable=False),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('external_id', sa.String(120), nullable=True),
        sa.Column('listing_url', sa.String(500), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['my_item_id'], ['my_items.id']),
    )
    op.create_index('ix_cross_posts_my_item_id', 'cross_posts', ['my_item_id'])

    # Create orders table
    op.create_table(
        'orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cross_post_id', sa.Integer(), nullable=False),
        sa.Column('platform_order_id', sa.String(120), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('total', sa.Float(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['cross_post_id'], ['cross_posts.id']),
    )

    # Create snap_jobs table
    op.create_table(
        'snap_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('source', sa.String(50), nullable=False),
        sa.Column('input_photos', sa.JSON(), nullable=False),
        sa.Column('processed_images', sa.JSON(), nullable=False),
        sa.Column('detected_category', sa.String(120), nullable=True),
        sa.Column('detected_attributes', sa.JSON(), nullable=False),
        sa.Column('condition_guess', sa.String(50), nullable=True),
        sa.Column('price_suggestion_cents', sa.Integer(), nullable=True),
        sa.Column('suggested_price', sa.Float(), nullable=True),
        sa.Column('suggested_title', sa.String(255), nullable=True),
        sa.Column('suggested_description', sa.Text(), nullable=True),
        sa.Column('title_suggestion', sa.String(255), nullable=True),
        sa.Column('description_suggestion', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('snap_jobs')
    op.drop_table('orders')
    op.drop_table('cross_posts')
    op.drop_table('marketplace_accounts')
    op.drop_table('my_items')
    op.drop_table('notifications')
    op.drop_table('user_prefs')
    op.drop_table('comps')
    op.drop_table('listing_scores')
    op.drop_table('listings')
    op.execute('DROP TYPE condition_enum')
