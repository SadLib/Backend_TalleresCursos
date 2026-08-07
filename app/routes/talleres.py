import json
from fastapi import APIRouter, Depends, HTTPException, Query
from asyncpg import Connection
from app.config.database import get_db
from app.middlewares.auth import get_current_user
from app.schemas.talleres import TallerCreate, TallerUpdate

router = APIRouter(prefix="/api/talleres", tags=["talleres"])


def _fmt_taller(r: dict) -> dict:
    d = dict(r)
    instructores_raw = d.get("instructores") or []
    d["instructores"] = [json.loads(x) for x in instructores_raw if x and json.loads(x).get("id")]
    if d.get("fecha_inicio"):
        d["fecha_inicio"] = str(d["fecha_inicio"])
    if d.get("fecha_fin"):
        d["fecha_fin"] = str(d["fecha_fin"])
    if d.get("hora_inicio"):
        d["hora_inicio"] = str(d["hora_inicio"])
    if d.get("hora_fin"):
        d["hora_fin"] = str(d["hora_fin"])
    return d


@router.get("")
async def get_all(
    db: Connection = Depends(get_db),
    modalidad: str | None = Query(None),
    estado: str | None = Query(None),
    instructor_id: int | None = Query(None),
):
    where, params = [], []
    if modalidad:
        params.append(modalidad)
        where.append(f"t.modalidad = ${len(params)}")
    if estado:
        params.append(estado)
        where.append(f"t.estado = ${len(params)}")
    if instructor_id:
        params.append(instructor_id)
        where.append(f"EXISTS (SELECT 1 FROM taller_instructor WHERE taller_id=t.id AND instructor_id=${len(params)})")
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    rows = await db.fetch(
        f"""SELECT t.*,
               (t.cupo_total - COALESCE((SELECT COUNT(*) FROM inscripciones WHERE taller_id=t.id AND estado='activa'), 0)) AS cupos_disponibles,
               array_agg(DISTINCT jsonb_build_object('id', u.id, 'nombre', u.nombre || ' ' || u.primer_apellido, 'especialidad', i.especialidad)) AS instructores
           FROM talleres t
           LEFT JOIN taller_instructor ti ON ti.taller_id = t.id
           LEFT JOIN instructores i ON i.id = ti.instructor_id
           LEFT JOIN usuarios u ON u.id = i.usuario_id
           {where_sql}
           GROUP BY t.id ORDER BY t.created_at DESC""",
        *params,
    )
    return [_fmt_taller(dict(r)) for r in rows]


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
    taller = await db.fetchrow(
        """SELECT t.*,
               (t.cupo_total - COALESCE((SELECT COUNT(*) FROM inscripciones WHERE taller_id=t.id AND estado='activa'), 0)) AS cupos_disponibles
           FROM talleres t WHERE t.id=$1""",
        id,
    )
    if not taller:
        raise HTTPException(status_code=404, detail="Taller no encontrado")

    temario = await db.fetch("SELECT id, orden, tema FROM temario WHERE taller_id=$1 ORDER BY orden", id)
    instructores = await db.fetch(
        """SELECT i.id, i.usuario_id, i.afiliacion, i.profesion AS institucion, i.especialidad, i.biografia,
                  u.nombre, u.primer_apellido, u.correo, u.foto_url
           FROM taller_instructor ti
           JOIN instructores i ON i.id = ti.instructor_id
           JOIN usuarios u ON u.id = i.usuario_id
           WHERE ti.taller_id=$1""",
        id,
    )

    d = dict(taller)
    for f in ["fecha_inicio", "fecha_fin"]:
        if d.get(f):
            d[f] = str(d[f])
    for f in ["hora_inicio", "hora_fin"]:
        if d.get(f):
            d[f] = str(d[f])

    ponentes = []
    for r in instructores:
        row = dict(r)
        ponentes.append({
            "id": row["id"],
            "usuario_id": row["usuario_id"],
            "afiliacion": row["afiliacion"],
            "institucion": row["institucion"],
            "especialidad": row["especialidad"],
            "biografia": row["biografia"],
            "usuario": {
                "nombre": row["nombre"],
                "primer_apellido": row["primer_apellido"],
                "correo": row["correo"],
                "foto_url": row["foto_url"],
            },
        })

    return {
        **d,
        "temario": [dict(r) for r in temario],
        "ponentes": ponentes,
        "sesiones": [],
    }


@router.post("", status_code=201)
async def create(body: TallerCreate, db: Connection = Depends(get_db), current_user: dict = Depends(get_current_user)):
    row = await db.fetchrow(
        """INSERT INTO talleres (nombre, descripcion, detalles, imagen_url, modalidad, ubicacion,
           fecha_inicio, fecha_fin, hora_inicio, hora_fin, numero_sesiones, cupo_total)
           VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12) RETURNING *""",
        body.nombre, body.descripcion, body.detalles, body.imagen_url, body.modalidad, body.ubicacion,
        body.fecha_inicio, body.fecha_fin, body.hora_inicio, body.hora_fin, body.numero_sesiones, body.cupo_total,
    )
    taller_id = row["id"]

    # Auto-asignar al ponente creador si tiene registro en instructores
    instructor = await db.fetchrow(
        """SELECT i.id, i.afiliacion, i.especialidad, i.biografia, i.profesion AS institucion,
                  u.nombre, u.primer_apellido, u.correo, u.foto_url
           FROM instructores i JOIN usuarios u ON u.id=i.usuario_id
           WHERE i.usuario_id=$1""",
        current_user["id"],
    )
    ponentes = []
    if instructor:
        await db.execute(
            "INSERT INTO taller_instructor (taller_id, instructor_id) VALUES ($1,$2) ON CONFLICT DO NOTHING",
            taller_id, instructor["id"],
        )
        inst = dict(instructor)
        ponentes = [{
            "id": inst["id"],
            "usuario_id": current_user["id"],
            "afiliacion": inst["afiliacion"],
            "institucion": inst["institucion"],
            "especialidad": inst["especialidad"],
            "biografia": inst["biografia"],
            "usuario": {
                "nombre": inst["nombre"],
                "primer_apellido": inst["primer_apellido"],
                "correo": inst["correo"],
                "foto_url": inst["foto_url"],
            },
        }]

    d = dict(row)
    for f in ["fecha_inicio", "fecha_fin", "hora_inicio", "hora_fin"]:
        if d.get(f):
            d[f] = str(d[f])
    d["cupos_disponibles"] = d["cupo_total"]
    d["ponentes"] = ponentes
    d["temario"] = []
    d["sesiones"] = []
    return d


@router.put("/{id}")
async def update(id: int, body: TallerUpdate, db: Connection = Depends(get_db), _=Depends(get_current_user)):
    existing = await db.fetchrow("SELECT * FROM talleres WHERE id=$1", id)
    if not existing:
        raise HTTPException(status_code=404, detail="Taller no encontrado")

    nombre = body.nombre if body.nombre is not None else existing["nombre"]
    descripcion = body.descripcion if body.descripcion is not None else existing["descripcion"]
    detalles = body.detalles if body.detalles is not None else existing["detalles"]
    imagen_url = body.imagen_url if body.imagen_url is not None else existing["imagen_url"]
    modalidad = body.modalidad if body.modalidad is not None else existing["modalidad"]
    ubicacion = body.ubicacion if body.ubicacion is not None else existing["ubicacion"]
    fecha_inicio = body.fecha_inicio if body.fecha_inicio is not None else existing["fecha_inicio"]
    fecha_fin = body.fecha_fin if body.fecha_fin is not None else existing["fecha_fin"]
    hora_inicio = body.hora_inicio if body.hora_inicio is not None else existing["hora_inicio"]
    hora_fin = body.hora_fin if body.hora_fin is not None else existing["hora_fin"]
    numero_sesiones = body.numero_sesiones if body.numero_sesiones is not None else existing["numero_sesiones"]
    cupo_total = body.cupo_total if body.cupo_total is not None else existing["cupo_total"]
    estado = body.estado if body.estado is not None else existing["estado"]

    row = await db.fetchrow(
        """UPDATE talleres SET nombre=$1, descripcion=$2, detalles=$3, imagen_url=$4, modalidad=$5,
           ubicacion=$6, fecha_inicio=$7, fecha_fin=$8, hora_inicio=$9, hora_fin=$10,
           numero_sesiones=$11, cupo_total=$12, estado=$13, updated_at=CURRENT_TIMESTAMP
           WHERE id=$14 RETURNING *""",
        nombre, descripcion, detalles, imagen_url, modalidad, ubicacion,
        fecha_inicio, fecha_fin, hora_inicio, hora_fin,
        numero_sesiones, cupo_total, estado, id,
    )
    d = dict(row)
    for f in ["fecha_inicio", "fecha_fin", "hora_inicio", "hora_fin"]:
        if d.get(f):
            d[f] = str(d[f])
    d["cupos_disponibles"] = d["cupo_total"]
    return d


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
