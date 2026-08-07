from fastapi import APIRouter, Depends, HTTPException
from asyncpg import Connection
from app.config.database import get_db
from app.middlewares.auth import get_current_user
from app.schemas.carreras import CarreraCreate

router = APIRouter(prefix="/api/carreras", tags=["carreras"])


@router.get("")
async def get_all(db: Connection = Depends(get_db)):
    rows = await db.fetch("SELECT id, nombre FROM carreras ORDER BY nombre")
    return [dict(r) for r in rows]


@router.post("", status_code=201)
async def create(body: CarreraCreate, db: Connection = Depends(get_db), _=Depends(get_current_user)):
    try:
        row = await db.fetchrow(
            "INSERT INTO carreras (nombre) VALUES ($1) RETURNING *", body.nombre
        )
    except Exception:
        raise HTTPException(status_code=409, detail="La carrera ya existe")
    return dict(row)
