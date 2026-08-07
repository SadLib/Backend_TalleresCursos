from fastapi import APIRouter, Depends, HTTPException
from asyncpg import Connection
from app.config.database import get_db
from app.middlewares.auth import get_current_user
from app.schemas.alumnos import AlumnoCreate, AlumnoUpdate

router = APIRouter(prefix="/api/alumnos", tags=["alumnos"])


@router.get("")
async def get_all(db: Connection = Depends(get_db), _=Depends(get_current_user)):
    rows = await db.fetch(
        """SELECT a.*, u.nombre, u.primer_apellido, u.correo, c.id AS carrera_id, c.nombre AS carrera
           FROM alumnos a
           JOIN usuarios u ON u.id = a.usuario_id
           LEFT JOIN carreras c ON c.id = a.carrera_id
           ORDER BY a.id"""
    )
    return [dict(r) for r in rows]

@router.get("/{id}")
async def get_by_id(id: int, db: Connection = Depends(get_db), _=Depends(get_current_user)):
    row = await db.fetchrow(
        """SELECT a.*, u.nombre, u.primer_apellido, u.correo, u.telefono, c.id AS carrera_id, c.nombre AS carrera
           FROM alumnos a
           JOIN usuarios u ON u.id = a.usuario_id
           LEFT JOIN carreras c ON c.id = a.carrera_id
           WHERE a.id = $1""",
        id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Alumno no encontrado")
    return dict(row)


@router.post("", status_code=201)
async def create(body: AlumnoCreate, db: Connection = Depends(get_db), _=Depends(get_current_user)):
    try:
        await db.execute(
            "INSERT INTO alumnos (usuario_id, numero_cuenta, carrera_id, semestre) VALUES ($1,$2,$3,$4)",
            body.usuario_id, body.numero_cuenta, body.carrera_id, body.semestre,
        )
    except Exception:
        raise HTTPException(status_code=409, detail="El usuario ya tiene perfil de alumno o número de cuenta duplicado")
    
    row = await db.fetchrow(
        """SELECT a.*, u.nombre, u.primer_apellido, u.correo, c.id AS carrera_id, c.nombre AS carrera
           FROM alumnos a
           JOIN usuarios u ON u.id = a.usuario_id
           LEFT JOIN carreras c ON c.id = a.carrera_id
           WHERE a.usuario_id = $1""",
        body.usuario_id,
    )
    return dict(row)


@router.put("/{id}")
async def update(id: int, body: AlumnoUpdate, db: Connection = Depends(get_db), _=Depends(get_current_user)):
    await db.execute(
        "UPDATE alumnos SET numero_cuenta=$1, carrera_id=$2, semestre=$3 WHERE id=$4",
        body.numero_cuenta, body.carrera_id, body.semestre, id,
    )
    
    row = await db.fetchrow(
        """SELECT a.*, u.nombre, u.primer_apellido, u.correo, u.telefono, c.id AS carrera_id, c.nombre AS carrera
           FROM alumnos a
           JOIN usuarios u ON u.id = a.usuario_id
           LEFT JOIN carreras c ON c.id = a.carrera_id
           WHERE a.id = $1""",
        id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Alumno no encontrado")
    return dict(row)


@router.delete("/{id}")
async def remove(id: int, db: Connection = Depends(get_db), _=Depends(get_current_user)):
    await db.execute("DELETE FROM alumnos WHERE id=$1", id)
    return {"message": "Alumno eliminado"}
