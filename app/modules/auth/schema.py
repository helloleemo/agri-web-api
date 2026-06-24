
import uuid

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str
    password: str = Field(..., min_length=8, max_length=200)


class RegisterRequest(BaseModel):
    email: str
    user_name: str = Field(..., max_length=20)
    password: str = Field(..., min_length=8, max_length=200)
    role_code: int = Field(..., gt=0)


class RegisterResponse(BaseModel):
    email: str
    verification_expires_in: int


class VerifyEmailRequest(BaseModel):
    token: str = Field(..., min_length=1)


class ResendVerificationEmailRequest(BaseModel):
    email: str


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=200)


class VerifyEmailResponse(BaseModel):
    email: str
    verified: bool = True


class AuthUser(BaseModel):
    id: uuid.UUID
    email: str
    user_name: str
    role_id: uuid.UUID
    role_code: int


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: AuthUser

class AuthEmailTemplateResponse(BaseModel):
    template_type: int
    subject_template: str | None = None
    body_template: str | None = None


class AuthEmailTemplateUpdate(BaseModel):
    subject_template: str | None = None
    body_template: str | None = None
