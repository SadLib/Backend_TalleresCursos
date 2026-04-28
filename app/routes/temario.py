from fastapi import APIRouter, Depends, HTTPException
from asyncpg import Connection
from app.config.database import get_db
from app.middlewares.auth import get_current_user
from app.schemas.temario import TemaCreate, TemaUpdate

router = APIRouter(tags=["temario"])


@router.post("/api/talleres/{taller_id}/temario", status_code=201)
async def create(taller_id: int, body: TemaCreate, db: Connection = Depends(get_db), _=Depends(get_current_user)):
    try:
        row = await db.fetchrow(
            "INSERT INTO temario (taller_id, orden, tema) VALUES ($1,$2,$3) RETURNING *",
            taller_id, body.orden, body.tema,
        )
    except Exception:
        raise HTTPException(status_code=409, detail="Ya existe un tema con ese orden en este taller")
    return dict(row)


@router.get("/api/talleres/{taller_id}/temario")
async def get_by_taller(taller_id: int, db: Connection = Depends(get_db), _=Depends(get_current_user)):
    rows = await db.fetch(
        "SELECT * FROM temario WHERE taller_id=$1 ORDER BY orden", taller_id
    )
    return [dict(r) for r in rows]


@router.put("/api/temario/{id}")
async def update(id: int, body: TemaUpdate, db: Connection = Depends(get_db), _=Depends(get_current_user)):
    row = await db.fetchrow(
        "UPDATE temario SET orden=$1, tema=$2 WHERE id=$3 RETURNING *",
        body.orden, body.tema, id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Tema no encontrado")
    return dict(row)


@router.delete("/api/temario/{id}")
async def remove(id: int, db: Connection = Depends(get_db), _=Depends(get_current_user)):
    await db.execute("DELETE FROM temario WHERE id=$1", id)
    return {"message": "Tema eliminado"}
