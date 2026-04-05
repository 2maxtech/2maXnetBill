from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class RegisterRequest(BaseModel):
    company_name: str
    full_name: str
    email: EmailStr
    phone: str
    username: str
    password: str


class ProfileUpdate(BaseModel):
    username: str | None = None
    email: EmailStr | None = None
    full_name: str | None = None
    company_name: str | None = None
    phone: str | None = None
    current_password: str | None = None
    new_password: str | None = None
