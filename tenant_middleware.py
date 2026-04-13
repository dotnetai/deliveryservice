from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
import re

class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Header orqali: X-Tenant-ID: tenant_a
        tenant = request.headers.get("X-Tenant-ID")

        # 2. Subdomain orqali: tenant_a.delivery.com
        if not tenant:
            host = request.headers.get("host", "")
            match = re.match(r"^([^.]+)\.", host)
            if match and match.group(1) not in ("www", "127", "localhost"):
                tenant = match.group(1)

        # 3. Default
        if not tenant:
            tenant = "public"

        # Faqat alphanumeric + underscore
        if not tenant.replace("_", "").isalnum():
            tenant = "public"

        request.state.tenant = tenant
        response = await call_next(request)
        return response