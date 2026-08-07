from pydantic import BaseModel
from datetime import datetime


class UsuarioUpdate(BaseModel):
    nombre: str | None = None
    primer_apellido: str | None = None
    segundo_apellido: str | None = None
    telefono: str | None = None
    foto_url: str | None = None
    carrera: str | None = None
    semestre: str | None = None
    numero_cuenta: str | None = None
    activo: bool | None = None


class UsuarioResponse(BaseModel):
    id: int
    nombre: str
    primer_apellido: str
    segundo_apellido: str | None
    correo: str
    telefono: str | None
    activo: bool
    created_at: datetime
