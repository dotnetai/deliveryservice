from fastapi import Request
from database import get_tenant_session

def get_db(request: Request):
    """
    Tenant-aware database session.
    Har bir request uchun to'g'ri schema ishlatiladi.

    Usage:
        @router.get("/")
        async def endpoint(db: Session = Depends(get_db)):
            ...
    """
    tenant = getattr(request.state, "tenant", "public")
    db = get_tenant_session(tenant)
    try:
        yield db
    finally:
        db.close()