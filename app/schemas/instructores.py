from pydantic import BaseModel
from typing import Literal


class InstructorCreate(BaseModel):
    usuario_id: int
    afiliacion: Literal["interno", "externo", "estudiante", "profesor"] | None = None
    profesion: str | None = None
    especialidad: str | None = None
    biografia: str | None = None


class InstructorUpdate(BaseModel):
    afiliacion: Literal["interno", "externo", "estudiante", "profesor"] | None = None
    profesion: str | None = None
    especialidad: str | None = None
    biografia: str | None = None
