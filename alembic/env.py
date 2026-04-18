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


def schema_is_already_set_up(connection, schema: str) -> bool:
    """
    Returns True if the schema already has tables but no alembic_version yet.
    This means it was created before Alembic — we should stamp, not migrate.
    """
    users_exists = connection.execute(
        text("SELECT to_regclass(:t)"),
        {"t": f"{schema}.users"}
    ).scalar()

    alembic_version_exists = connection.execute(
        text("SELECT to_regclass(:t)"),
        {"t": f"{schema}.alembic_version"}
    ).scalar()

    # Tables exist but alembic hasn't tracked them yet → needs stamp
    return bool(users_exists) and not bool(alembic_version_exists)


def configure_for_schema(connection, schema: str):
    """Configure Alembic context to target a specific schema."""
    # Reset and set search_path so DDL lands in the right schema
    connection.execute(text("RESET search_path"))
    connection.execute(text(f"SET search_path TO {schema}, public"))

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        version_table="alembic_version",
        version_table_schema=schema,  # each schema tracks its own version
        include_schemas=True,
        compare_type=True,
        compare_server_default=True,
        dialect_opts={"paramstyle": "named"},
        # Translate unqualified table names → tenant schema
        schema_translate_map={None: schema},
    )


def run_migrations_for_schema(connection, schema: str):
    """
    Run migrations scoped to a single schema.
    If the schema was created before Alembic (tables exist, no alembic_version),
    just stamp it as head instead of running DDL that would fail.
    """
    print(f"  → Processing schema: '{schema}'")

    if schema_is_already_set_up(connection, schema):
        # Tables already exist — stamp as current head without running DDL
        print(f"    ⚡ Schema '{schema}' already has tables. Stamping as head...")
        configure_for_schema(connection, schema)
        with context.begin_transaction():
            context.get_context().stamp(context.get_context().connection,
                                        "1419fddf62ac")
        print(f"    ✅ Stamped '{schema}'")
        return

    # Normal path: run all pending migrations
    configure_for_schema(connection, schema)
    with context.begin_transaction():
        context.run_migrations()

    print(f"    ✅ Migrated '{schema}'")



# def run_migrations_for_schema(connection, schema: str):
#     """Run migrations scoped to a single schema."""
#     print(f"  → Migrating schema: '{schema}'")
#
#     # Tell SQLAlchemy which schema to use for this migration run
#     connection.execute(text(f"SET search_path TO {schema}, public"))
#     # connection.execute(text("COMMIT"))  # needed before SET in some PG versions
#
#     context.configure(
#         connection=connection,
#         target_metadata=target_metadata,
#         version_table="alembic_version",        # each schema gets its OWN version table
#         version_table_schema=schema,            # explicitly scoped
#         include_schemas=True,
#         compare_type=True,
#         compare_server_default=True,
#
#         # 🔥 THIS IS THE KEY FIX
#         dialect_opts={"paramstyle": "named"},
#         render_as_batch=True,
#         version_table_pk=True,
#
#         # 👇 CRITICAL LINE
#         schema_translate_map={None: schema},
#     )
#
#     with context.begin_transaction():
#         context.run_migrations()


def run_migrations_online():
    """
    Two modes:
    - target_schema is set  → migrate ONLY that one schema (called from create_tenant_schema)
    - target_schema not set → migrate public + all tenant schemas (CLI: alembic upgrade head)
    """
    # `target_schema` is injected by create_tenant_schema() via set_main_option()
    target_schema = config.get_main_option("target_schema", None)

    with engine.begin() as connection:
        if target_schema:
            # ── Single-tenant mode ───────────────────────────────────────────
            print(f"\n[Alembic] Migrating new tenant schema: '{target_schema}'")
            run_migrations_for_schema(connection, target_schema)
        else:
            # ── Full migration mode (CLI) ────────────────────────────────────
            print("\n[Alembic] Migrating 'public' schema...")
            run_migrations_for_schema(connection, "public")

            tenant_schemas = get_tenant_schemas(connection)
            if tenant_schemas:
                print(f"\n[Alembic] Found {len(tenant_schemas)} tenant(s): {tenant_schemas}")
                for schema in tenant_schemas:
                    run_migrations_for_schema(connection, schema)
            else:
                print("\n[Alembic] No tenant schemas found yet.")

        print("\n[Alembic] All migrations complete ✅")


    # with engine.connect() as connection:
    #     # 1. Always migrate 'public' schema first (shared base)
    #     print("\n[Alembic] Migrating 'public' schema...")
    #     run_migrations_for_schema(connection, "public")
    #
    #     # 2. Discover and migrate all tenant schemas
    #     tenant_schemas = get_tenant_schemas(connection)
    #
    #     if tenant_schemas:
    #         print(f"\n[Alembic] Found {len(tenant_schemas)} tenant(s): {tenant_schemas}")
    #         for schema in tenant_schemas:
    #             run_migrations_for_schema(connection, schema)
    #     else:
    #         print("\n[Alembic] No tenant schemas found yet.")
    #
    #     print("\n[Alembic] All migrations complete ✅")

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