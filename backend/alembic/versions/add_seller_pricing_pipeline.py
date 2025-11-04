"""Add seller pricing pipeline models and fields

Revision ID: seller_pricing_pipeline
Revises: phase_7_add_deal_alerts_and_notifications
Create Date: 2025-11-04

This migration adds:
1. New fields to SnapJob: progress, error_message, meta
2. New ListingDraft table for seller drafts
3. New MediaAsset table for image processing

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'seller_pricing_pipeline'
down_revision = 'phase_7_add_deal_alerts_and_notifications'
branch_labels = None
depends_on = None


def upgrade():
    # Add new fields to snap_jobs table
    op.add_column('snap_jobs', sa.Column('progress', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('snap_jobs', sa.Column('error_message', sa.Text(), nullable=True))
    op.add_column('snap_jobs', sa.Column('meta', sa.JSON(), nullable=False, server_default='{}'))

    # Create listing_drafts table
    op.create_table(
        'listing_drafts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('snap_job_id', sa.Integer(), nullable=True),
        sa.Column('category', sa.String(length=120), nullable=False),
        sa.Column('attributes', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('condition', sa.Enum('poor', 'fair', 'good', 'great', 'excellent', name='condition'), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('bullet_highlights', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('tags', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('price_suggested', sa.Float(), nullable=True),
        sa.Column('price_low', sa.Float(), nullable=True),
        sa.Column('price_high', sa.Float(), nullable=True),
        sa.Column('pricing_rationale', sa.Text(), nullable=True),
        sa.Column('images', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='draft'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['snap_job_id'], ['snap_jobs.id'], ),
    )
    op.create_index(op.f('ix_listing_drafts_user_id'), 'listing_drafts', ['user_id'], unique=False)

    # Create media_assets table
    op.create_table(
        'media_assets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('snap_job_id', sa.Integer(), nullable=True),
        sa.Column('listing_draft_id', sa.Integer(), nullable=True),
        sa.Column('original_url', sa.String(length=500), nullable=False),
        sa.Column('processed_url', sa.String(length=500), nullable=True),
        sa.Column('thumbnail_url', sa.String(length=500), nullable=True),
        sa.Column('processing_status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('processing_options', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['snap_job_id'], ['snap_jobs.id'], ),
        sa.ForeignKeyConstraint(['listing_draft_id'], ['listing_drafts.id'], ),
    )
    op.create_index(op.f('ix_media_assets_snap_job_id'), 'media_assets', ['snap_job_id'], unique=False)
    op.create_index(op.f('ix_media_assets_listing_draft_id'), 'media_assets', ['listing_draft_id'], unique=False)


def downgrade():
    # Drop media_assets table
    op.drop_index(op.f('ix_media_assets_listing_draft_id'), table_name='media_assets')
    op.drop_index(op.f('ix_media_assets_snap_job_id'), table_name='media_assets')
    op.drop_table('media_assets')

    # Drop listing_drafts table
    op.drop_index(op.f('ix_listing_drafts_user_id'), table_name='listing_drafts')
    op.drop_table('listing_drafts')

    # Remove new columns from snap_jobs
    op.drop_column('snap_jobs', 'meta')
    op.drop_column('snap_jobs', 'error_message')
    op.drop_column('snap_jobs', 'progress')
