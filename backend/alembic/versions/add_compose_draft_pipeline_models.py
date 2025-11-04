"""Add compose draft pipeline models (MediaAsset, ListingDraft, CrossPostJob)

Revision ID: compose_draft_001
Revises: phase_7_001
Create Date: 2025-11-03

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'compose_draft_001'
down_revision = 'phase_7_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create media_assets table
    op.create_table(
        'media_assets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('snap_job_id', sa.Integer(), nullable=True),
        sa.Column('listing_draft_id', sa.Integer(), nullable=True),
        sa.Column('original_url', sa.String(length=500), nullable=False),
        sa.Column('processed_url', sa.String(length=500), nullable=True),
        sa.Column('thumbnail_url', sa.String(length=500), nullable=True),
        sa.Column('media_type', sa.String(length=50), nullable=False, server_default='image'),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('processing_status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('processing_steps', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('ocr_text', sa.Text(), nullable=True),
        sa.Column('vision_labels', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('vision_captions', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['snap_job_id'], ['snap_jobs.id'], ),
        sa.ForeignKeyConstraint(['listing_draft_id'], ['listing_drafts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_media_assets_user_id'), 'media_assets', ['user_id'], unique=False)
    op.create_index(op.f('ix_media_assets_snap_job_id'), 'media_assets', ['snap_job_id'], unique=False)
    op.create_index(op.f('ix_media_assets_listing_draft_id'), 'media_assets', ['listing_draft_id'], unique=False)

    # Create listing_drafts table
    op.create_table(
        'listing_drafts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('snap_job_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='draft'),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=120), nullable=False),
        sa.Column('attributes', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('condition', sa.Enum('poor', 'fair', 'good', 'great', 'excellent', name='condition'), nullable=True),
        sa.Column('price_suggested', sa.Float(), nullable=True),
        sa.Column('price_low', sa.Float(), nullable=True),
        sa.Column('price_high', sa.Float(), nullable=True),
        sa.Column('price_rationale', sa.Text(), nullable=True),
        sa.Column('bullet_highlights', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('tags', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('seo_keywords', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('vision_confidence', sa.Float(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('parent_draft_id', sa.Integer(), nullable=True),
        sa.Column('published_item_id', sa.Integer(), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['snap_job_id'], ['snap_jobs.id'], ),
        sa.ForeignKeyConstraint(['parent_draft_id'], ['listing_drafts.id'], ),
        sa.ForeignKeyConstraint(['published_item_id'], ['my_items.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_listing_drafts_user_id'), 'listing_drafts', ['user_id'], unique=False)
    op.create_index(op.f('ix_listing_drafts_snap_job_id'), 'listing_drafts', ['snap_job_id'], unique=False)
    op.create_index(op.f('ix_listing_drafts_status'), 'listing_drafts', ['status'], unique=False)

    # Create cross_post_jobs table
    op.create_table(
        'cross_post_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('snap_job_id', sa.Integer(), nullable=True),
        sa.Column('listing_draft_id', sa.Integer(), nullable=True),
        sa.Column('my_item_id', sa.Integer(), nullable=True),
        sa.Column('platforms', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('progress', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('platform_metadata', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('cross_post_ids', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('logs', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['snap_job_id'], ['snap_jobs.id'], ),
        sa.ForeignKeyConstraint(['listing_draft_id'], ['listing_drafts.id'], ),
        sa.ForeignKeyConstraint(['my_item_id'], ['my_items.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cross_post_jobs_user_id'), 'cross_post_jobs', ['user_id'], unique=False)
    op.create_index(op.f('ix_cross_post_jobs_snap_job_id'), 'cross_post_jobs', ['snap_job_id'], unique=False)
    op.create_index(op.f('ix_cross_post_jobs_listing_draft_id'), 'cross_post_jobs', ['listing_draft_id'], unique=False)
    op.create_index(op.f('ix_cross_post_jobs_my_item_id'), 'cross_post_jobs', ['my_item_id'], unique=False)
    op.create_index(op.f('ix_cross_post_jobs_status'), 'cross_post_jobs', ['status'], unique=False)


def downgrade() -> None:
    # Drop cross_post_jobs table
    op.drop_index(op.f('ix_cross_post_jobs_status'), table_name='cross_post_jobs')
    op.drop_index(op.f('ix_cross_post_jobs_my_item_id'), table_name='cross_post_jobs')
    op.drop_index(op.f('ix_cross_post_jobs_listing_draft_id'), table_name='cross_post_jobs')
    op.drop_index(op.f('ix_cross_post_jobs_snap_job_id'), table_name='cross_post_jobs')
    op.drop_index(op.f('ix_cross_post_jobs_user_id'), table_name='cross_post_jobs')
    op.drop_table('cross_post_jobs')

    # Drop listing_drafts table
    op.drop_index(op.f('ix_listing_drafts_status'), table_name='listing_drafts')
    op.drop_index(op.f('ix_listing_drafts_snap_job_id'), table_name='listing_drafts')
    op.drop_index(op.f('ix_listing_drafts_user_id'), table_name='listing_drafts')
    op.drop_table('listing_drafts')

    # Drop media_assets table
    op.drop_index(op.f('ix_media_assets_listing_draft_id'), table_name='media_assets')
    op.drop_index(op.f('ix_media_assets_snap_job_id'), table_name='media_assets')
    op.drop_index(op.f('ix_media_assets_user_id'), table_name='media_assets')
    op.drop_table('media_assets')
