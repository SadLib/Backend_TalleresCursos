from pydantic import BaseModel


class RolCreate(BaseModel):
    nombre: str
