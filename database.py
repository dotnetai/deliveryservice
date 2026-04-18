from sqlalchemy import create_engine, text, MetaData
from sqlalchemy.orm import declarative_base, sessionmaker
from alembic.config import Config
from alembic import command

engine = create_engine("postgresql://postgres:RIVOJmz777@localhost/delivery_db", echo=True)

Base = declarative_base()  # modellarni hosil qilish uchun
# session = sessionmaker(bind=engine) # crud operatsiyalarni bajarish uchun
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_tenant_session(tenant: str):
    """Tenant schema bilan session qaytaradi."""
    # SQL injection'dan himoya
    if not tenant.replace("_", "").isalnum():
        raise ValueError(f"Invalid tenant name: {tenant}")

    db = SessionLocal()
    # db.execute(text(f"SET search_path TO {tenant}, public"))

    # Check schema exists
    result = db.execute(
        text("SELECT schema_name FROM information_schema.schemata WHERE schema_name = :tenant"),
        {"tenant": tenant}
    ).fetchone()

    if not result:
        raise Exception(f"Tenant schema '{tenant}' does not exist")

    # Force new transaction
    db.execute(text("RESET search_path"))
    db.execute(text(f"SET search_path TO {tenant}, public"))
    return db

# def create_tenant_schema(tenant: str):
#     if not tenant.replace("_", "").isalnum():
#         raise ValueError(f"Invalid tenant name: {tenant}")
#
#     with engine.begin() as conn:
#         # 1. Create schema
#         conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {tenant}"))
#
#         # 2. Create fresh metadata bound to schema
#         metadata = MetaData(schema=tenant)
#
#         for table in Base.metadata.tables.values():
#             table.tometadata(metadata)
#
#         # 3. Create tables INSIDE tenant
#         metadata.create_all(bind=conn)
#
#         print(f"✅ Tables created in schema '{tenant}'")

def create_tenant_schema(tenant: str):
    """
    Create a new PostgreSQL schema for the tenant and run Alembic migrations
    so that users / products / orders tables are created inside it.
    """
    if not tenant.replace("_", "").isalnum():
        raise ValueError(f"Invalid tenant name: {tenant}")

    # ── 1. Create the schema ─────────────────────────────────────────────────
    with engine.begin() as conn:
        existing = conn.execute(
            text("SELECT schema_name FROM information_schema.schemata WHERE schema_name = :t"),
            {"t": tenant}
        ).fetchone()
        if existing:
            raise ValueError(f"Tenant '{tenant}' already exists")

        conn.execute(text(f"CREATE SCHEMA {tenant}"))
        print(f"✅ Schema '{tenant}' created")

    # Run Alembic migrations scoped to this new tenant
    # Alembic's env.py will pick up the new schema automatically
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("target_schema", tenant)
    command.upgrade(alembic_cfg, "head")

    print(f"✅ Tables created in schema '{tenant}'")
