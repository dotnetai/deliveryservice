from fastapi import APIRouter, Depends, HTTPException

from auth_routes import get_current_user
from database import create_tenant_schema
from models import User
from starlette import status

admin_router = APIRouter(
    prefix="/admin"
)

@admin_router.post("/tenant/create")
async def create_tenant(
        tenant_name: str,
        current_user: User = Depends(get_current_user())
):
    """Yangi tenant (company/organization) yaratish — faqat superadmin"""
    if not current_user.is_staff:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superadmin can create tenants"
        )

    try:
        create_tenant_schema(tenant_name)
        return {
            "success": True,
            "message": f"Tenant '{tenant_name}' created successfully",
            "hint": f"Now send requests with header: X-Tenant-ID: {tenant_name}"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
