from pydantic import BaseModel


class TemaCreate(BaseModel):
    orden: int
    tema: str


class TemaUpdate(BaseModel):
    orden: int
    tema: str
