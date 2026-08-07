from fastapi import APIRouter, Depends, HTTPException
from asyncpg import Connection
from app.config.database import get_db
from app.middlewares.auth import get_current_user
from app.schemas.instructores import InstructorCreate, InstructorUpdate

router = APIRouter(prefix="/api/instructores", tags=["instructores"])


def _fmt_instructor(row: dict) -> dict:
    return {
        "id": row["id"],
        "usuario_id": row["usuario_id"],
        "afiliacion": row["afiliacion"],
        "institucion": row.get("profesion"),
        "especialidad": row.get("especialidad"),
        "biografia": row.get("biografia"),
        "usuario": {
            "id": row["usuario_id"],
            "nombre": row.get("nombre"),
            "primer_apellido": row.get("primer_apellido"),
            "segundo_apellido": row.get("segundo_apellido"),
            "correo": row.get("correo"),
            "telefono": row.get("telefono"),
            "foto_url": row.get("foto_url"),
            "activo": row.get("activo"),
        },
    }


@router.get("/me")
async def get_me(db: Connection = Depends(get_db), current_user: dict = Depends(get_current_user)):
    row = await db.fetchrow(
        """SELECT i.*, u.nombre, u.primer_apellido, u.correo, u.telefono, u.foto_url, u.activo
           FROM instructores i JOIN usuarios u ON u.id = i.usuario_id
           WHERE i.usuario_id = $1""",
        current_user["id"],
    )
    if not row:
        raise HTTPException(status_code=404, detail="No tienes perfil de instructor")
    return _fmt_instructor(dict(row))


@router.get("")
async def get_all(db: Connection = Depends(get_db)):
    rows = await db.fetch(
        """SELECT i.*, u.nombre, u.primer_apellido, u.correo, u.telefono, u.foto_url, u.activo
           FROM instructores i JOIN usuarios u ON u.id = i.usuario_id
           ORDER BY i.id"""
    )
    return [_fmt_instructor(dict(r)) for r in rows]


@router.get("/{id}")
async def get_by_id(id: int, db: Connection = Depends(get_db)):
    row = await db.fetchrow(
        """SELECT i.*, u.nombre, u.primer_apellido, u.correo, u.telefono, u.foto_url, u.activo
           FROM instructores i JOIN usuarios u ON u.id = i.usuario_id
           WHERE i.id = $1""",
        id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Instructor no encontrado")
    return _fmt_instructor(dict(row))


@router.post("", status_code=201)
async def create(body: InstructorCreate, db: Connection = Depends(get_db), _=Depends(get_current_user)):
    try:
        row = await db.fetchrow(
            "INSERT INTO instructores (usuario_id, afiliacion, profesion, especialidad, biografia) VALUES ($1,$2,$3,$4,$5) RETURNING *",
            body.usuario_id, body.afiliacion, body.profesion, body.especialidad, body.biografia,
        )
    except Exception:
        raise HTTPException(status_code=409, detail="El usuario ya tiene perfil de instructor")
    rol = await db.fetchrow("SELECT id FROM roles WHERE nombre='ponente'")
    if rol:
        await db.execute(
            "INSERT INTO usuario_rol (usuario_id, rol_id) VALUES ($1,$2) ON CONFLICT DO NOTHING",
            body.usuario_id, rol["id"],
        )
    return dict(row)


@router.put("/me")
async def update_me(body: InstructorUpdate, db: Connection = Depends(get_db), current_user: dict = Depends(get_current_user)):
    existing = await db.fetchrow("SELECT * FROM instructores WHERE usuario_id=$1", current_user["id"])
    if not existing:
        raise HTTPException(status_code=404, detail="No tienes perfil de instructor")
    afiliacion = body.afiliacion if body.afiliacion is not None else existing["afiliacion"]
    profesion = body.profesion if body.profesion is not None else existing["profesion"]
    especialidad = body.especialidad if body.especialidad is not None else existing["especialidad"]
    biografia = body.biografia if body.biografia is not None else existing["biografia"]
    await db.execute(
        "UPDATE instructores SET afiliacion=$1, profesion=$2, especialidad=$3, biografia=$4 WHERE usuario_id=$5",
        afiliacion, profesion, especialidad, biografia, current_user["id"],
    )
    row = await db.fetchrow(
        """SELECT i.*, u.nombre, u.primer_apellido, u.segundo_apellido, u.correo, u.telefono, u.foto_url, u.activo
           FROM instructores i JOIN usuarios u ON u.id = i.usuario_id WHERE i.usuario_id=$1""",
        current_user["id"],
    )
    return _fmt_instructor(dict(row))


@router.put("/{id}")
async def update(id: int, body: InstructorUpdate, db: Connection = Depends(get_db), _=Depends(get_current_user)):
    existing = await db.fetchrow("SELECT * FROM instructores WHERE id=$1", id)
    if not existing:
        raise HTTPException(status_code=404, detail="Instructor no encontrado")
    afiliacion = body.afiliacion if body.afiliacion is not None else existing["afiliacion"]
    profesion = body.profesion if body.profesion is not None else existing["profesion"]
    especialidad = body.especialidad if body.especialidad is not None else existing["especialidad"]
    biografia = body.biografia if body.biografia is not None else existing["biografia"]
    await db.execute(
        "UPDATE instructores SET afiliacion=$1, profesion=$2, especialidad=$3, biografia=$4 WHERE id=$5",
        afiliacion, profesion, especialidad, biografia, id,
    )
    row = await db.fetchrow(
        """SELECT i.*, u.nombre, u.primer_apellido, u.segundo_apellido, u.correo, u.telefono, u.foto_url, u.activo
           FROM instructores i JOIN usuarios u ON u.id = i.usuario_id WHERE i.id=$1""",
        id,
    )
    return _fmt_instructor(dict(row))


@router.delete("/{id}")
async def remove(id: int, db: Connection = Depends(get_db), _=Depends(get_current_user)):
    await db.execute("DELETE FROM instructores WHERE id=$1", id)
    return {"message": "Instructor eliminado"}
