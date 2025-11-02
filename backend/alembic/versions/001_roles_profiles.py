from alembic import op
import sqlalchemy as sa


revision = "001_roles_profiles"
down_revision = "add_platform_marketplace"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(20), nullable=False, unique=True),
    )
    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role_id", sa.Integer, sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    )
    op.create_table(
        "buyer_profiles",
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("search_radius_km", sa.Integer, server_default="25"),
        sa.Column("price_min_cents", sa.Integer),
        sa.Column("price_max_cents", sa.Integer),
    )
    op.create_table(
        "seller_profiles",
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("default_location", sa.Text),
        sa.Column("default_condition", sa.Text),
    )
    op.execute("INSERT INTO roles (name) VALUES ('buyer') ON CONFLICT DO NOTHING;")
    op.execute("INSERT INTO roles (name) VALUES ('seller') ON CONFLICT DO NOTHING;")


def downgrade():
    op.drop_table("seller_profiles")
    op.drop_table("buyer_profiles")
    op.drop_table("user_roles")
    op.drop_table("roles")
