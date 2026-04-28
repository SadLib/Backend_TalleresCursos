from pydantic import BaseModel


class AlumnoCreate(BaseModel):
    usuario_id: int
    numero_cuenta: str
    carrera_id: int | None = None
    semestre: int | None = None


class AlumnoUpdate(BaseModel):
    numero_cuenta: str
    carrera_id: int | None = None
    semestre: int | None = None
