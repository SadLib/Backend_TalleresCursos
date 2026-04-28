from pydantic import BaseModel


class CertificadoCreate(BaseModel):
    inscripcion_id: int
