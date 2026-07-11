from fastapi import APIRouter, HTTPException, status
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from app.db.connection import users_collection
from app.schemas.auth_schema import RegisterRequest, LoginRequest, TokenResponse, GoogleRegisterRequest
import os
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from app.security import SECRET_KEY, ALGORITHM

router = APIRouter()

ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
MAIL_EMAIL       = os.getenv("MAIL_EMAIL")
MAIL_PASSWORD    = os.getenv("MAIL_PASSWORD")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In-memory OTP store — { email: { otp, expires_at } }
otp_store = {}


# ── Helpers ──────────────────────────────────────────────
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_token(user_id: str, email: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": user_id, "email": email, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def send_otp_email(to_email: str, otp: str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Your Receipt Analyzer OTP"
    msg["From"]    = MAIL_EMAIL
    msg["To"]      = to_email

    html = f"""
    <div style="font-family: sans-serif; max-width: 400px; margin: 0 auto; padding: 32px;">
        <h2 style="color: #2d6ef5;">Receipt Analyzer</h2>
        <p>Your one-time password to reset your password is:</p>
        <div style="font-size: 36px; font-weight: 700; letter-spacing: 8px; color: #111318; margin: 24px 0;">{otp}</div>
        <p style="color: #9ba3b8; font-size: 13px;">This OTP expires in 10 minutes. Do not share it with anyone.</p>
    </div>
    """
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(MAIL_EMAIL, MAIL_PASSWORD)
        server.sendmail(MAIL_EMAIL, to_email, msg.as_string())


# ── Schemas ───────────────────────────────────────────────
class GoogleLoginRequest(BaseModel):
    credential: str

class ForgotPasswordRequest(BaseModel):
    email: str

class VerifyOTPRequest(BaseModel):
    email: str
    otp: str
    new_password: str


# ── Routes ────────────────────────────────────────────────
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
        "auth_provider": "email",
        "created_at": datetime.utcnow().isoformat()
    }
    result = await users_collection.insert_one(user_doc)
    token = create_token(str(result.inserted_id), body.email)
    return TokenResponse(access_token=token, name=body.name)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    user = await users_collection.find_one({"email": body.email})
    if not user or not verify_password(body.password, user.get("password", "")):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_token(str(user["_id"]), user["email"])
    return TokenResponse(access_token=token, name=user["name"])


@router.post("/google", response_model=TokenResponse)
async def google_login(body: GoogleLoginRequest):
    try:
        id_info = id_token.verify_oauth2_token(
            body.credential,
            google_requests.Request(),
            GOOGLE_CLIENT_ID
        )
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    email = id_info["email"]
    name  = id_info.get("name", email.split("@")[0])

    user = await users_collection.find_one({"email": email})

    if not user:
        # First time Google login — create account
        user_doc = {
            "name": name,
            "email": email,
            "password": None,
            "auth_provider": "google",
            "created_at": datetime.utcnow().isoformat()
        }
        result = await users_collection.insert_one(user_doc)
        user_id = str(result.inserted_id)
    else:
        user_id = str(user["_id"])
        name    = user.get("name", name)

    token = create_token(user_id, email)
    return TokenResponse(access_token=token, name=name)


@router.post("/google-register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def google_register(body: GoogleRegisterRequest):
    try:
        id_info = id_token.verify_oauth2_token(
            body.credential,
            google_requests.Request(),
            GOOGLE_CLIENT_ID
        )
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    email = id_info["email"]

    existing = await users_collection.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists")

    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Please enter a display name")

    user_doc = {
        "name": name,
        "email": email,
        "password": None,
        "auth_provider": "google",
        "created_at": datetime.utcnow().isoformat()
    }
    result = await users_collection.insert_one(user_doc)
    token = create_token(str(result.inserted_id), email)
    return TokenResponse(access_token=token, name=name)


@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest):
    user = await users_collection.find_one({"email": body.email})
    if not user:
        # Don't reveal if email exists
        return {"message": "If that email is registered, an OTP has been sent."}

    otp = str(random.randint(100000, 999999))
    otp_store[body.email] = {
        "otp": otp,
        "expires_at": datetime.utcnow() + timedelta(minutes=10)
    }

    try:
        send_otp_email(body.email, otp)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

    return {"message": "If that email is registered, an OTP has been sent."}


@router.post("/verify-otp")
async def verify_otp(body: VerifyOTPRequest):
    record = otp_store.get(body.email)

    if not record:
        raise HTTPException(status_code=400, detail="No OTP requested for this email")

    if datetime.utcnow() > record["expires_at"]:
        del otp_store[body.email]
        raise HTTPException(status_code=400, detail="OTP has expired")

    if record["otp"] != body.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # OTP correct — update password
    hashed = hash_password(body.new_password)
    await users_collection.update_one(
        {"email": body.email},
        {"$set": {"password": hashed}}
    )
    del otp_store[body.email]

    return {"message": "Password reset successfully"}