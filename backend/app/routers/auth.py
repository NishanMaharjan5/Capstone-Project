from fastapi import APIRouter, HTTPException, status
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from app.db.connection import users_collection
from app.schemas.auth_schema import RegisterRequest, LoginRequest, TokenResponse
import os

router = APIRouter()

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey123changemelater")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_token(user_id: str, email: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": user_id, "email": email, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest):
    existing = await users_collection.find_one({"email": body.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = hash_password(body.password)
    user_doc = {
        "name": body.name,
        "email": body.email,
        "password": hashed,
        "created_at": datetime.utcnow().isoformat()
    }
    result = await users_collection.insert_one(user_doc)
    token = create_token(str(result.inserted_id), body.email)
    return TokenResponse(access_token=token, name=body.name)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    user = await users_collection.find_one({"email": body.email})
    if not user or not verify_password(body.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_token(str(user["_id"]), user["email"])
    return TokenResponse(access_token=token, name=user["name"])