from fastapi import APIRouter, status, Depends, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordBearer
import bcrypt
from jose import JWTError, jwt
from sqlalchemy import or_
from sqlalchemy.orm import Session

from dependencies import get_db
from schemas import SignUpModel, LoginModel
from database import session, engine
from models import User
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
from database import get_tenant_session


auth_router = APIRouter(
    prefix="/auth"
)

# Fallback global session (eski kod uchun)
session = session(bind=engine)

# Config
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def create_token(data: dict, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    to_encode["exp"] = datetime.utcnow() + expires_delta
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme), request: Request = None):
    """
    Tenant-aware current user.
    Agar request mavjud bo'lsa — tenant session ishlatadi,
    aks holda global session ishlatadi.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    # Tenant session yoki global session
    if request is not None:
        tenant = getattr(request.state, "tenant", "public")
        db = get_tenant_session(tenant)
    else:
        db = session

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return user


@auth_router.get("/")
async def welcome(current_user: User = Depends(get_current_user)):
    return {"message": f"Hello, {current_user.username}"}

@auth_router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(user: SignUpModel, db: Session = Depends(get_db())):
    db_email = db.query(User).filter(User.email == user.email).first()
    if db_email is not None:
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User with this email already registered")

    db_username = db.query(User).filter(User.username == user.username).first()
    if db_username is not None:
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User with this username already registered")

    new_user = User(
        username=user.username,
        email=user.email,
        password=bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'), # shifrlash -> bcrypt
        is_active=user.is_active,
        is_staff=user.is_staff
    )

    db.add(new_user)
    db.commit()
    data = {
        'id': new_user.id,
        'username': new_user.username,
        'email': new_user.email,
        'is_active': new_user.is_active,
        'is_staff': new_user.is_staff
    }

    response_model = {
        'success': True,
        'code': status.HTTP_201_CREATED,
        'message': 'User created successfully',
        'data': data
    }

    return response_model

@auth_router.post("/login", status_code=status.HTTP_200_OK)
async def login(user: LoginModel, db: Session = Depends(get_db)):
    # db_user = session.query(User).filter(User.username == user.username).first()

    # query with email or username
    db_user = db.query(User).filter(
        or_(
            User.username == user.username_or_email,
            User.email == user.username_or_email
        )
    ).first()

    if db_user and bcrypt.checkpw(user.password.encode('utf-8'), db_user.password.encode('utf-8')):
        access_token = create_token(
            {"sub": db_user.username},
            timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        refresh_token = create_token(
            {"sub": db_user.username, "type": "refresh"},
            timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        )

        token = {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'bearer'
        }

        response = {
            "success": True,
            "code": status.HTTP_200_OK,
            "message": "User successfully logged in.",
            "data": token
        }

        return jsonable_encoder(response)

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid username or password")


@auth_router.get("/login/refresh")
async def refresh_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        token_type = payload.get("type")

        if username is None or token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Token"
        )

    db_user = db.query(User).filter(User.username == username).first()
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    new_access_token = create_token(
        {"sub": db_user.username},
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {
        "success": True,
        "code": 200,
        "message": "New access token is created",
        "data": {
            "access_token": new_access_token
        }
    }