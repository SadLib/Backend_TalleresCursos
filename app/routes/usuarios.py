from fastapi import APIRouter, Depends, HTTPException
from asyncpg import Connection
from app.config.database import get_db
from app.middlewares.auth import get_current_user
from app.schemas.usuarios import UsuarioUpdate

router = APIRouter(prefix="/api/usuarios", tags=["usuarios"])


@router.get("/me/inscripciones")
async def mis_inscripciones(db: Connection = Depends(get_db), current_user: dict = Depends(get_current_user)):
    rows = await db.fetch(
        """SELECT i.*, t.nombre AS taller_nombre, t.modalidad, t.fecha_inicio, t.fecha_fin
           FROM inscripciones i
           JOIN talleres t ON t.id = i.taller_id
           WHERE i.usuario_id = $1
           ORDER BY i.fecha_inscripcion DESC""",
        current_user["id"],
    )
    return [dict(r) for r in rows]


@router.get("")
async def get_all(db: Connection = Depends(get_db), _=Depends(get_current_user)):
    rows = await db.fetch(
        "SELECT id, nombre, primer_apellido, segundo_apellido, correo, telefono, activo, created_at FROM usuarios ORDER BY id"
    )
    return [dict(r) for r in rows]


@router.get("/{id}")
async def get_by_id(id: int, db: Connection = Depends(get_db), _=Depends(get_current_user)):
    row = await db.fetchrow(
        "SELECT id, nombre, primer_apellido, segundo_apellido, correo, telefono, foto_url, activo, created_at FROM usuarios WHERE id=$1",
        id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return dict(row)


@router.put("/{id}")
async def update(id: int, body: UsuarioUpdate, db: Connection = Depends(get_db), _=Depends(get_current_user)):
    row = await db.fetchrow(
        """UPDATE usuarios SET nombre=$1, primer_apellido=$2, segundo_apellido=$3,
           telefono=$4, foto_url=$5, updated_at=CURRENT_TIMESTAMP
           WHERE id=$6 RETURNING id, nombre, correo""",
        body.nombre, body.primer_apellido, body.segundo_apellido,
        body.telefono, body.foto_url, id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return dict(row)


@router.delete("/{id}")
async def deactivate(id: int, db: Connection = Depends(get_db), _=Depends(get_current_user)):
    await db.execute("UPDATE usuarios SET activo=false WHERE id=$1", id)
    return {"message": "Usuario desactivado"}
