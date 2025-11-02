"""Add platform column to marketplace_accounts.

Revision ID: add_platform_marketplace
Revises: phase_7_001
Create Date: 2025-10-31 22:40:00.000000
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "add_platform_marketplace"
down_revision = "phase_7_001"
branch_labels = None
depends_on = None


def _has_column(table: str, column: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return any(col["name"] == column for col in inspector.get_columns(table))


def upgrade() -> None:
    if not _has_column("marketplace_accounts", "platform"):
        with op.batch_alter_table("marketplace_accounts") as batch_op:
            batch_op.add_column(sa.Column("platform", sa.String(length=50), nullable=True))

    if _has_column("marketplace_accounts", "marketplace"):
        op.execute(
            "UPDATE marketplace_accounts "
            "SET platform = COALESCE(platform, marketplace)"
        )
        op.execute("DROP INDEX IF EXISTS ix_marketplace_accounts_marketplace")
        with op.batch_alter_table("marketplace_accounts") as batch_op:
            batch_op.drop_column("marketplace")

    op.execute("DROP INDEX IF EXISTS ix_marketplace_accounts_platform")

    with op.batch_alter_table("marketplace_accounts") as batch_op:
        batch_op.alter_column(
            "platform",
            existing_type=sa.String(length=50),
            nullable=False,
        )
        batch_op.create_index(
            "ix_marketplace_accounts_platform", ["platform"], unique=False
        )
        batch_op.alter_column(
            "user_id",
            existing_type=sa.Integer(),
            nullable=True,
        )
        batch_op.alter_column(
            "account_username",
            existing_type=sa.String(length=255),
            nullable=True,
        )


def downgrade() -> None:
    if not _has_column("marketplace_accounts", "marketplace"):
        with op.batch_alter_table("marketplace_accounts") as batch_op:
            batch_op.add_column(
                sa.Column("marketplace", sa.String(length=50), nullable=True)
            )

    op.execute(
        "UPDATE marketplace_accounts "
        "SET marketplace = COALESCE(marketplace, platform)"
    )
    op.execute("DROP INDEX IF EXISTS ix_marketplace_accounts_platform")

    with op.batch_alter_table("marketplace_accounts") as batch_op:
        batch_op.alter_column(
            "marketplace",
            existing_type=sa.String(length=50),
            nullable=False,
        )
        batch_op.create_index(
            "ix_marketplace_accounts_marketplace", ["marketplace"], unique=False
        )
        if _has_column("marketplace_accounts", "platform"):
            batch_op.drop_column("platform")
        batch_op.alter_column(
            "user_id",
            existing_type=sa.Integer(),
            nullable=False,
        )
        batch_op.alter_column(
            "account_username",
            existing_type=sa.String(length=255),
            nullable=False,
        )
