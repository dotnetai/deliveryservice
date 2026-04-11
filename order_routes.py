from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from starlette import status

from auth_routes import get_current_user, session
from models import User
from schemas import OrderModel, OrderStatusModel
from models import Order

order_router = APIRouter(
    prefix="/order"
)

@order_router.get("/")
async def welcome_page(current_user: User = Depends(get_current_user)):
    return {"This is order route page. User": current_user.username}

@order_router.post("/make", status_code=status.HTTP_201_CREATED)
async def make_order(order: OrderModel, current_user: User = Depends(get_current_user)):
    new_order = Order(
        quantity = order.quantity,
        product_id = order.product_id
    )
    new_order.user = current_user
    session.add(new_order)
    session.commit()

    response = {
        "success": True,
        "code": status.HTTP_201_CREATED,
        "message": "Order is created successfully",
        "data" : {
            "id": new_order.id,
            "product": {
                "id": new_order.product.id,
                "name": new_order.product.name,
                "price": new_order.product.price
            },
            "quantity": new_order.quantity,
            "order_statuses": new_order.order_statuses.value,
            "total_price": new_order.quantity * new_order.product.price
        }
    }

    return jsonable_encoder(response)

@order_router.get('/list', status_code=status.HTTP_200_OK)
async def list_all_orders(current_user: User = Depends(get_current_user)):
    # Bu barcha buyurtmalar ro'yhatini qaytaradi
    if current_user.is_staff:
        orders = session.query(Order).all()
        custom_data = [
            {
                "id": order.id,
                "user": {
                    "id": order.user.id,
                    "username": order.user.username,
                    "email": order.user.email
                },
                "product": {
                    "id": order.product.id,
                    "name": order.product.name,
                    "price": order.product.price
                },
                "quantity": order.quantity,
                "order_statuses": order.order_statuses.value,
                "total_price": order.quantity * order.product.price
            }
            for order in orders
        ]
        return jsonable_encoder(custom_data)

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Only SuperAdmin/staff users can see all orders"
    )

@order_router.get('/{id}', status_code=status.HTTP_200_OK)
async def get_order_by_id(id: int, current_user: User = Depends(get_current_user)):
    # Get an order by its ID
    if current_user.is_staff:
        order = session.query(Order).filter(Order.id == id).first()
        if order:
            custom_order = {
                    "id": order.id,
                    "user": {
                        "id": order.user.id,
                        "username": order.user.username,
                        "email": order.user.email
                    },
                    "product": {
                        "id": order.product.id,
                        "name": order.product.name,
                        "price": order.product.price
                    },
                    "quantity": order.quantity,
                    "order_statuses": order.order_statuses.value,
                    "total_price": order.quantity * order.product.price
                }
            return jsonable_encoder(custom_order)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order with {id} not found."
            )

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Only SuperAdmin/staff user is allowed to this request."
    )

@order_router.get('/user/orders', status_code=status.HTTP_200_OK)
async def get_user_orders(current_user: User = Depends(get_current_user)):
    """
    Get all orders for a user
    :param current_user:
    :return:
    """
    custom_data = [
        {
            "id": order.id,
            "user": {
                "id": order.user.id,
                "username": order.user.username,
                "email": order.user.email
            },
            "product": {
                "id": order.product.id,
                "name": order.product.name,
                "price": order.product.price
            },
            "quantity": order.quantity,
            "order_statuses": order.order_statuses.value,
            "total_price": order.quantity * order.product.price
        }
        for order in current_user.orders
    ]

    return jsonable_encoder(custom_data)

@order_router.get('/user/order/{id}', status_code=status.HTTP_200_OK)
async def get_user_order_by_id(id: int, current_user: User = Depends(get_current_user)):
    """
    Get user order by id
    :param current_user:
    :return:
    """
    order = session.query(Order).filter(Order.id == id, Order.user == current_user).first()
    # orders = current_user.orders
    if order:
        order_data = {
            "id": order.id,
            "user": {
                "id": order.user.id,
                "username": order.user.username,
                "email": order.user.email
            },
            "product": {
                "id": order.product.id,
                "name": order.product.name,
                "price": order.product.price
            },
            "quantity": order.quantity,
            "order_statuses": order.order_statuses.value,
            "total_price": order.quantity * order.product.price
        }

        return jsonable_encoder(order_data)
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with {id} not found."
        )

@order_router.put('/{id}/update', status_code=status.HTTP_200_OK)
async def update_order(id: int, order: OrderModel, current_user: User = Depends(get_current_user)):
    """
    Update user order by fields : quantity and product_id
    :param current_user:
    :return:
    """
    order_to_update = session.query(Order).filter(Order.id == id).first()
    if order_to_update.user != current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot update other user's orders"
        )

    order_to_update.quantity = order.quantity
    order_to_update.product_id = order.product_id
    session.commit()

    custom_response = {
        "success": True,
        "code": status.HTTP_200_OK,
        "message": "Your order has been updated successfully",
        "data": {
            "id": order.id,
            "quantity": order.quantity,
            "product_id": order.product_id,
            "order_status": order.order_statuses
        }
    }
    return jsonable_encoder(custom_response)


@order_router.patch('/{id}/update-status', status_code=status.HTTP_200_OK)
async def update_order_status(id: int, order: OrderStatusModel, current_user: User = Depends(get_current_user)):
    """Update user order's status"""
    if current_user.is_staff:
        order_to_update = session.query(Order).filter(Order.id == id).first()
        order_to_update.order_statuses = order.order_statuses
        session.commit()

        custom_response = {
            "success": True,
            "code": status.HTTP_200_OK,
            "message": "User order (status) has been updated successfully",
            "data": {
                "id": order_to_update.id,
                "order_status": order_to_update.order_statuses
            }
        }
        return jsonable_encoder(custom_response)


@order_router.delete('/{id}/delete', status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(id: int, current_user: User = Depends(get_current_user)):
    """Delete an order of user"""
    order = session.query(Order).filter(Order.id == id).first()
    if order.user != current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot update other user's orders"
        )

    if order.order_statuses != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot delete transit or shipped orders"
        )

    session.delete(order)
    session.commit()

    custom_response = {
        "success": True,
        "code": status.HTTP_200_OK,
        "message": "User order has been deleted successfully",
        "data": None
    }
    return jsonable_encoder(custom_response)


