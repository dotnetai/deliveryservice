from fastapi import FastAPI

from admin_routes import admin_router
from auth_routes import auth_router
from order_routes import order_router
from product_routes import product_router
from tenant_middleware import TenantMiddleware

app = FastAPI(
    title="Delivery Service API",
    description="Multi-tenant delivery service",
    version="2.0.0"
)

app.add_middleware(TenantMiddleware)

app.include_router(admin_router)
app.include_router(auth_router)
app.include_router(order_router)
app.include_router(product_router)

@app.get("/")
async def root():
    return {"message": "Delivery Service API v2.0 — Multi-tenant"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
