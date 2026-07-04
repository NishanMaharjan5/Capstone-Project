from pydantic import BaseModel, EmailStr

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class GoogleRegisterRequest(BaseModel):
    credential: str
    name: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    name: str