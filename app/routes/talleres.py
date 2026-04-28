import json
from fastapi import APIRouter, Depends, HTTPException, Query
from asyncpg import Connection
from app.config.database import get_db
from app.middlewares.auth import get_current_user
from app.schemas.talleres import TallerCreate, TallerUpdate

router = APIRouter(prefix="/api/talleres", tags=["talleres"])


@router.get("")
async def get_all(
    db: Connection = Depends(get_db),
    modalidad: str | None = Query(None),
    estado: str | None = Query(None),
):
    where, params = [], []
    if modalidad:
        params.append(modalidad)
        where.append(f"t.modalidad = ${len(params)}")
    if estado:
        params.append(estado)
        where.append(f"t.estado = ${len(params)}")

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    rows = await db.fetch(
        f"""SELECT t.*, array_agg(DISTINCT jsonb_build_object('id', u.id, 'nombre', u.nombre || ' ' || u.primer_apellido)) AS instructores
           FROM talleres t
           LEFT JOIN taller_instructor ti ON ti.taller_id = t.id
           LEFT JOIN instructores i ON i.id = ti.instructor_id
           LEFT JOIN usuarios u ON u.id = i.usuario_id
           {where_sql}
           GROUP BY t.id ORDER BY t.created_at DESC""",
        *params,
    )
    result = []
    for r in rows:
        d = dict(r)
        d["instructores"] = [json.loads(x) for x in d.get("instructores") or []]
        result.append(d)
    return result


@router.get("/{id}/inscripciones")
async def get_inscripciones(id: int, db: Connection = Depends(get_db), _=Depends(get_current_user)):
    rows = await db.fetch(
        """SELECT i.*, u.nombre, u.primer_apellido, u.correo
           FROM inscripciones i JOIN usuarios u ON u.id = i.usuario_id
           WHERE i.taller_id = $1 ORDER BY i.fecha_inscripcion""",
        id,
    )
    return [dict(r) for r in rows]


@router.get("/{id}")
async def get_by_id(id: int, db: Connection = Depends(get_db)):
    taller = await db.fetchrow("SELECT * FROM talleres WHERE id=$1", id)
    if not taller:
        raise HTTPException(status_code=404, detail="Taller no encontrado")

    temario = await db.fetch("SELECT orden, tema FROM temario WHERE taller_id=$1 ORDER BY orden", id)
    instructores = await db.fetch(
        """SELECT u.id, u.nombre, u.primer_apellido, i.profesion, i.especialidad
           FROM taller_instructor ti
           JOIN instructores i ON i.id = ti.instructor_id
           JOIN usuarios u ON u.id = i.usuario_id
           WHERE ti.taller_id=$1""",
        id,
    )
    return {**dict(taller), "temario": [dict(r) for r in temario], "instructores": [dict(r) for r in instructores]}


@router.post("", status_code=201)
async def create(body: TallerCreate, db: Connection = Depends(get_db), _=Depends(get_current_user)):
    row = await db.fetchrow(
        """INSERT INTO talleres (nombre, descripcion, detalles, imagen_url, modalidad, ubicacion,
           fecha_inicio, fecha_fin, hora_inicio, hora_fin, numero_sesiones, cupo_total)
           VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12) RETURNING *""",
        body.nombre, body.descripcion, body.detalles, body.imagen_url, body.modalidad, body.ubicacion,
        body.fecha_inicio, body.fecha_fin, body.hora_inicio, body.hora_fin, body.numero_sesiones, body.cupo_total,
    )
    return dict(row)


@router.put("/{id}")
async def update(id: int, body: TallerUpdate, db: Connection = Depends(get_db), _=Depends(get_current_user)):
    row = await db.fetchrow(
        """UPDATE talleres SET nombre=$1, descripcion=$2, detalles=$3, imagen_url=$4, modalidad=$5,
           ubicacion=$6, fecha_inicio=$7, fecha_fin=$8, hora_inicio=$9, hora_fin=$10,
           numero_sesiones=$11, cupo_total=$12, estado=$13, updated_at=CURRENT_TIMESTAMP
           WHERE id=$14 RETURNING *""",
        body.nombre, body.descripcion, body.detalles, body.imagen_url, body.modalidad, body.ubicacion,
        body.fecha_inicio, body.fecha_fin, body.hora_inicio, body.hora_fin,
        body.numero_sesiones, body.cupo_total, body.estado, id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Taller no encontrado")
    return dict(row)


@router.delete("/{id}")
async def remove(id: int, db: Connection = Depends(get_db), _=Depends(get_current_user)):
    await db.execute("DELETE FROM talleres WHERE id=$1", id)
    return {"message": "Taller eliminado"}


@router.post("/{taller_id}/instructores/{instructor_id}", status_code=201)
async def asignar_instructor(taller_id: int, instructor_id: int, db: Connection = Depends(get_db), _=Depends(get_current_user)):
    try:
        await db.execute(
            "INSERT INTO taller_instructor (taller_id, instructor_id) VALUES ($1,$2)",
            taller_id, instructor_id,
        )
    except Exception:
        raise HTTPException(status_code=409, detail="El instructor ya está asignado a este taller")
    return {"message": "Instructor asignado"}


@router.delete("/{taller_id}/instructores/{instructor_id}")
async def quitar_instructor(taller_id: int, instructor_id: int, db: Connection = Depends(get_db), _=Depends(get_current_user)):
    await db.execute(
        "DELETE FROM taller_instructor WHERE taller_id=$1 AND instructor_id=$2", taller_id, instructor_id
    )
    return {"message": "Instructor removido"}
