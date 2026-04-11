from itertools import product

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from starlette import status

from auth_routes import get_current_user, session
from models import User, Product
from schemas import ProductModel

product_router = APIRouter(
    prefix="/product"
)

@product_router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductModel, current_user: User = Depends(get_current_user)):
    # create a new product
    if current_user.is_staff:
        new_product = Product(
            name = product.name,
            price = product.price,
        )

        session.add(new_product)
        session.commit()
        data = {
            "success": True,
            "code": status.HTTP_201_CREATED,
            "message": "Product is created successfully",
            "data": {
                "id": new_product.id,
                "name": new_product.name,
                "price": new_product.price,
            }
        }
        return jsonable_encoder(data)

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Only SuperAdmin/staff users can create a product"
    )

@product_router.get("/list", status_code=status.HTTP_200_OK)
async def list_all_products(current_user: User = Depends(get_current_user)):
    # Bu route barcha mahsulotlar ro'yxatini chiqarib beradi.
    if current_user.is_staff:
        products = session.query(Product).all()
        custom_data = [
            {
                "id": product.id,
                "name": product.name,
                "price": product.price
            }
            for product in products
        ]

        return jsonable_encoder(custom_data)

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Only SuperAdmin/staff users can see all products"
    )

@product_router.get('/{id}', status_code=status.HTTP_200_OK)
async def get_product_by_id(id: int, current_user: User = Depends(get_current_user)):
    # Get an order by its ID
    if current_user.is_staff:
        product = session.query(Product).filter(Product.id == id).first()
        if product:
            custom_product = {
                    "id": product.id,
                    "name": product.name,
                    "price": product.price
                }
            return jsonable_encoder(custom_product)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with {id} not found."
            )

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Only SuperAdmin/staff user is allowed to this request."
    )

@product_router.delete("/{id}/delete", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product_by_id(id: int, current_user: User = Depends(get_current_user)):
    # Bu endpoint mahsulotni o'chirish uchun ishlatiladi.
    if current_user.is_staff:
        product = session.query(Product).filter(Product.id == id).first()
        if product:
            session.delete(product)
            session.commit()
            data = {
                "success": True,
                "code": status.HTTP_204_NO_CONTENT,
                "message": f"Product with {id} has been deleted successfully",
                "data": None
            }
            return jsonable_encoder(data)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with {id} is not found."
            )

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Only SuperAdmin/staff user is allowed to delete a product."
    )

@product_router.put("/{id}/update", status_code=status.HTTP_200_OK)
async def update_product_by_id(id: int, update_data: ProductModel, current_user: User = Depends(get_current_user)):
    # Bu endpoint mahsulotni yangilash uchun ishlatiladi.
    if current_user.is_staff:
        product = session.query(Product).filter(Product.id == id).first()
        if product:
            # update product
            for key, value in update_data.dict(exclude_unset=True).items():
                setattr(product, key, value)
            session.commit()
            data = {
                "success": True,
                "code": status.HTTP_200_OK,
                "message": f"Product with {id} has been updated successfully",
                "data": {
                    "id": product.id,
                    "name": product.name,
                    "price": product.price
                }
            }
            return jsonable_encoder(data)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with {id} is not found."
            )

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Only SuperAdmin/staff user is allowed to update a product."
    )


