"""Alembic migration environment configuration."""

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, text
from alembic import context
import os

# This is the Alembic Config object, which provides the values of the
# [alembic] section of the alembic.ini file as Python data
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ===========================
# 1. Import all models to ensure they're loaded for autogenerate
# ===========================
from app.core.models import Base

target_metadata = Base.metadata

# ===========================
# 2. Read DATABASE_URL from environment (crucial for Docker/production)
# ===========================
# Priority: DATABASE_URL env var > alembic.ini sqlalchemy.url > fallback
def get_database_url():
    """Get DB URL from environment variables or alembic.ini"""
    # Try explicit DATABASE_URL first (set in .env or docker-compose)
    if os.getenv("DATABASE_URL"):
        return os.getenv("DATABASE_URL")

    # Fallback: construct from individual env vars (matches entrypoint.sh logic)
    db_host = os.getenv("DB_HOST", "postgres")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", os.getenv("DB_NAME", "deals"))
    db_user = os.getenv("POSTGRES_USER", os.getenv("DB_USER", "deals"))
    db_pass = os.getenv("POSTGRES_PASSWORD", os.getenv("DB_PASS", "deals"))

    return f"postgresql+psycopg://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

sqlalchemy_url = get_database_url()
config.set_main_option("sqlalchemy.url", sqlalchemy_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Get the config section and merge with sqlalchemy. prefix
    config_section = config.get_section(config.config_ini_section, {})

    # Ensure sqlalchemy.url is set from environment
    config_section["sqlalchemy.url"] = sqlalchemy_url

    connectable = engine_from_config(
        config_section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
