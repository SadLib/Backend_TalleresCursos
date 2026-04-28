from pydantic import BaseModel


class InscripcionCreate(BaseModel):
    usuario_id: int
    taller_id: int
