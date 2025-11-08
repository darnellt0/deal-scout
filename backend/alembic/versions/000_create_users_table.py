"""create users table

Revision ID: 000_create_users_table
Revises:
Create Date: 2025-11-08 14:56:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone


# revision identifiers, used by Alembic.
revision = '000_create_users_table'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create UserRole enum type
    op.execute("""
        CREATE TYPE userrole AS ENUM ('admin', 'seller', 'buyer', 'guest')
    """)

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(64), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('first_name', sa.String(128), nullable=True),
        sa.Column('last_name', sa.String(128), nullable=True),
        sa.Column('role', sa.Enum('admin', 'seller', 'buyer', 'guest', name='userrole'), nullable=False, server_default='buyer'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('profile', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)


def downgrade():
    # Drop indexes
    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('ix_users_username', table_name='users')

    # Drop table
    op.drop_table('users')

    # Drop enum type
    op.execute('DROP TYPE userrole')
