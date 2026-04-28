from pydantic import BaseModel
from datetime import date, time, datetime
from typing import Literal


class TallerCreate(BaseModel):
    nombre: str
    descripcion: str | None = None
    detalles: str | None = None
    imagen_url: str | None = None
    modalidad: Literal["presencial", "en_linea", "hibrido"] | None = None
    ubicacion: str | None = None
    fecha_inicio: date | None = None
    fecha_fin: date | None = None
    hora_inicio: time | None = None
    hora_fin: time | None = None
    numero_sesiones: int | None = None
    cupo_total: int


class TallerUpdate(TallerCreate):
    estado: Literal["borrador", "pendiente", "aprobado", "concluido", "cancelado"] | None = None
