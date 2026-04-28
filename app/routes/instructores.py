from fastapi import APIRouter, Depends, HTTPException
from asyncpg import Connection
from app.config.database import get_db
from app.middlewares.auth import get_current_user
from app.schemas.instructores import InstructorCreate, InstructorUpdate

router = APIRouter(prefix="/api/instructores", tags=["instructores"])


@router.get("")
async def get_all(db: Connection = Depends(get_db), _=Depends(get_current_user)):
    rows = await db.fetch(
        """SELECT i.*, u.nombre, u.primer_apellido, u.correo
           FROM instructores i
           JOIN usuarios u ON u.id = i.usuario_id
           ORDER BY i.id"""
    )
    return [dict(r) for r in rows]


@router.get("/{id}")
async def get_by_id(id: int, db: Connection = Depends(get_db), _=Depends(get_current_user)):
    row = await db.fetchrow(
        """SELECT i.*, u.nombre, u.primer_apellido, u.correo, u.telefono, u.foto_url
           FROM instructores i
           JOIN usuarios u ON u.id = i.usuario_id
           WHERE i.id = $1""",
        id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Instructor no encontrado")
    return dict(row)


@router.post("", status_code=201)
async def create(body: InstructorCreate, db: Connection = Depends(get_db), _=Depends(get_current_user)):
    try:
        row = await db.fetchrow(
            "INSERT INTO instructores (usuario_id, afiliacion, profesion, especialidad, biografia) VALUES ($1,$2,$3,$4,$5) RETURNING *",
            body.usuario_id, body.afiliacion, body.profesion, body.especialidad, body.biografia,
        )
    except Exception:
        raise HTTPException(status_code=409, detail="El usuario ya tiene perfil de instructor")
    return dict(row)


@router.put("/{id}")
async def update(id: int, body: InstructorUpdate, db: Connection = Depends(get_db), _=Depends(get_current_user)):
    row = await db.fetchrow(
        """UPDATE instructores SET afiliacion=$1, profesion=$2, especialidad=$3, biografia=$4
           WHERE id=$5 RETURNING *""",
        body.afiliacion, body.profesion, body.especialidad, body.biografia, id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Instructor no encontrado")
    return dict(row)


@router.delete("/{id}")
async def remove(id: int, db: Connection = Depends(get_db), _=Depends(get_current_user)):
    await db.execute("DELETE FROM instructores WHERE id=$1", id)
    return {"message": "Instructor eliminado"}
