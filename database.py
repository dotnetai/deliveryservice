from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

engine = create_engine("postgresql://postgres:RIVOJmz777@localhost/delivery_db", echo=True)

Base = declarative_base()  # modellarni hosil qilish uchun
session = sessionmaker(bind=engine) # crud operatsiyalarni bajarish uchun

def get_tenant_session(tenant: str):
    """Tenant schema bilan session qaytaradi."""
    # SQL injection'dan himoya
    if not tenant.replace("_", "").isalnum():
        raise ValueError(f"Invalid tenant name: {tenant}")

    db = session(bind=engine)
    db.execute(text(f"SET search_path TO {tenant}, public"))
    return db

def create_tenant_schema(tenant: str):
    """Yangi tenant uchun schema va table'lar yaratish"""
    if not tenant.replace("_", "").isalnum():
        raise ValueError(f"Invalid tenant name: {tenant}")

    with engine.connect() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {tenant}"))
        conn.execute(text(f"SET search_path TO {tenant}, public"))
        Base.metadata.create_all(conn)
        conn.commit()
        print(f"✅ Tenant '{tenant}' schema created")
