from pydantic import BaseModel


class CarreraCreate(BaseModel):
    nombre: str
