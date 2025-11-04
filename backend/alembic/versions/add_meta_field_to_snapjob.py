"""Add meta field to SnapJob for structured copywriter data

Revision ID: add_meta_snapjob
Revises: phase_7_001
Create Date: 2025-11-03

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_meta_snapjob'
down_revision = 'phase_7_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add metadata JSON column to snap_jobs table."""
    # Add metadata column with default empty dict
    op.add_column(
        'snap_jobs',
        sa.Column('metadata', sa.JSON(), nullable=False, server_default='{}')
    )


def downgrade() -> None:
    """Remove metadata column from snap_jobs table."""
    op.drop_column('snap_jobs', 'metadata')
