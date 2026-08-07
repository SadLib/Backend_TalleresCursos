from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    nombre: str
    primer_apellido: str
    segundo_apellido: str | None = None
    correo: EmailStr
    telefono: str | None = None
    password: str
    roles: list[str] | None = None


class LoginRequest(BaseModel):
    correo: EmailStr
    password: str


class TokenResponse(BaseModel):
    token: str
    usuario: dict
