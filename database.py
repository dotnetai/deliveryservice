from sqlalchemy import create_engine, text, MetaData
from sqlalchemy.orm import declarative_base, sessionmaker

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
#     """Yangi tenant uchun schema va table'lar yaratish"""
#     if not tenant.replace("_", "").isalnum():
#         raise ValueError(f"Invalid tenant name: {tenant}")
#
#     with engine.connect() as conn:
#         conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {tenant}"))
#         conn.execute(text(f"SET search_path TO {tenant}, public"))
#         Base.metadata.create_all(conn)
#         conn.commit()
#         print(f"✅ Tenant '{tenant}' schema created")

def create_tenant_schema(tenant: str):
    if not tenant.replace("_", "").isalnum():
        raise ValueError(f"Invalid tenant name: {tenant}")

    with engine.begin() as conn:
        # 1. Create schema
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {tenant}"))

        # 2. Create fresh metadata bound to schema
        metadata = MetaData(schema=tenant)

        for table in Base.metadata.tables.values():
            table.tometadata(metadata)

        # 3. Create tables INSIDE tenant
        metadata.create_all(bind=conn)

        print(f"✅ Tables created in schema '{tenant}'")
