# alembic/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, text
from alembic import context
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database import Base, engine
from models import User, Order, Product  # ensures models are registered

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_tenant_schemas(connection) -> list[str]:
    """Fetch all tenant schemas — excludes PostgreSQL system schemas."""
    result = connection.execute(text("""
        SELECT schema_name 
        FROM information_schema.schemata
        WHERE schema_name NOT IN (
            'public', 'information_schema', 'pg_catalog',
            'pg_toast', 'pg_temp_1', 'pg_toast_temp_1'
        )
        AND schema_name NOT LIKE 'pg_%'
    """))
    return [row[0] for row in result]


def run_migrations_for_schema(connection, schema: str):
    """Run migrations scoped to a single schema."""
    print(f"  → Migrating schema: '{schema}'")

    # Tell SQLAlchemy which schema to use for this migration run
    connection.execute(text(f"SET search_path TO {schema}, public"))
    # connection.execute(text("COMMIT"))  # needed before SET in some PG versions

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        version_table="alembic_version",        # each schema gets its OWN version table
        version_table_schema=schema,            # explicitly scoped
        include_schemas=True,
        compare_type=True,
        compare_server_default=True,

        # 🔥 THIS IS THE KEY FIX
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
        version_table_pk=True,

        # 👇 CRITICAL LINE
        schema_translate_map={None: schema},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    with engine.connect() as connection:
        # 1. Always migrate 'public' schema first (shared base)
        print("\n[Alembic] Migrating 'public' schema...")
        run_migrations_for_schema(connection, "public")

        # 2. Discover and migrate all tenant schemas
        tenant_schemas = get_tenant_schemas(connection)

        if tenant_schemas:
            print(f"\n[Alembic] Found {len(tenant_schemas)} tenant(s): {tenant_schemas}")
            for schema in tenant_schemas:
                run_migrations_for_schema(connection, schema)
        else:
            print("\n[Alembic] No tenant schemas found yet.")

        print("\n[Alembic] All migrations complete ✅")


def run_migrations_offline():
    """Offline mode — generates SQL scripts instead of running them."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()