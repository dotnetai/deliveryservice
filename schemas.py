from pydantic import BaseModel
from typing import Optional

class SignUpModel(BaseModel):
    id: Optional[int] = None
    username: str
    email: str
    password: str
    is_staff: Optional[bool]
    is_active: Optional[bool]

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "username": "mohirdev",
                "email": "mohirdev@gmail.com",
                "password": "password12345",
                "is_staff": False,
                "is_active": True,
            }
        }

class LoginModel(BaseModel):
    username_or_email: str
    password: str


class OrderModel(BaseModel):
    id: Optional[int] = None
    quantity: int
    order_statuses: Optional[str] = "PENDING"
    user_id: Optional[int] = None
    product_id: int

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "quantity": 2
            }
        }

class OrderStatusModel(BaseModel):
    order_statuses: Optional[str] = "PENDING"

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "order_statuses": "PENDING",
            }
        }

class ProductModel(BaseModel):
    id: Optional[int] = None
    name: str
    price: int

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "name": "Uzbek palov",
                "price": 30000,
            }
        }





















