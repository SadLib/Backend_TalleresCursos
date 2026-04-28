from fastapi import APIRouter, Depends, HTTPException
from asyncpg import Connection
from app.config.database import get_db
from app.middlewares.auth import get_current_user
from app.schemas.roles import RolCreate

router = APIRouter(prefix="/api/roles", tags=["roles"])


@router.get("")
async def get_all(db: Connection = Depends(get_db), _=Depends(get_current_user)):
    rows = await db.fetch("SELECT * FROM roles ORDER BY id")
    return [dict(r) for r in rows]


@router.post("", status_code=201)
async def create(body: RolCreate, db: Connection = Depends(get_db), _=Depends(get_current_user)):
    row = await db.fetchrow(
        "INSERT INTO roles (nombre) VALUES ($1) RETURNING *", body.nombre
    )
    return dict(row)


@router.delete("/{id}")
async def remove(id: int, db: Connection = Depends(get_db), _=Depends(get_current_user)):
    await db.execute("DELETE FROM roles WHERE id=$1", id)
    return {"message": "Rol eliminado"}


router_usuario_roles = APIRouter(prefix="/api/usuarios", tags=["roles"])


@router_usuario_roles.post("/{usuario_id}/roles/{rol_id}", status_code=201)
async def asignar_rol(usuario_id: int, rol_id: int, db: Connection = Depends(get_db), _=Depends(get_current_user)):
    existe = await db.fetchrow("SELECT 1 FROM usuario_rol WHERE usuario_id=$1 AND rol_id=$2", usuario_id, rol_id)
    if existe:
        raise HTTPException(status_code=409, detail="El usuario ya tiene ese rol")
    await db.execute("INSERT INTO usuario_rol (usuario_id, rol_id) VALUES ($1,$2)", usuario_id, rol_id)
    return {"message": "Rol asignado"}


@router_usuario_roles.delete("/{usuario_id}/roles/{rol_id}")
async def quitar_rol(usuario_id: int, rol_id: int, db: Connection = Depends(get_db), _=Depends(get_current_user)):
    await db.execute("DELETE FROM usuario_rol WHERE usuario_id=$1 AND rol_id=$2", usuario_id, rol_id)
    return {"message": "Rol removido"}
