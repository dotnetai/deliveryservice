from fastapi import APIRouter

order_router = APIRouter(
    prefix="/order"
)

@order_router.get("/")
async def signup():
    return {"message": "Bu order route signup qisimi"}