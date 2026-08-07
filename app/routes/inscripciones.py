from fastapi import APIRouter, Depends, HTTPException
from asyncpg import Connection
from app.config.database import get_db
from app.middlewares.auth import get_current_user

router = APIRouter(prefix="/api/inscripciones", tags=["inscripciones"])


@router.get("/me")
async def mis_inscripciones(db: Connection = Depends(get_db), current_user: dict = Depends(get_current_user)):
    rows = await db.fetch(
        """SELECT i.*,
                  row_to_json(t.*) AS taller
           FROM inscripciones i
           JOIN talleres t ON t.id = i.taller_id
           WHERE i.usuario_id = $1
           ORDER BY i.fecha_inscripcion DESC""",
        current_user["id"],
    )
    import json
    result = []
    for r in rows:
        d = dict(r)
        if isinstance(d.get("taller"), str):
            d["taller"] = json.loads(d["taller"])
        result.append(d)
    return result


@router.get("")
async def get_all(db: Connection = Depends(get_db), _=Depends(get_current_user)):
    rows = await db.fetch(
        """SELECT i.*, u.nombre, u.primer_apellido, t.nombre AS taller_nombre
           FROM inscripciones i
           JOIN usuarios u ON u.id = i.usuario_id
           JOIN talleres t ON t.id = i.taller_id
           ORDER BY i.fecha_inscripcion DESC"""
    )
    return [dict(r) for r in rows]


@router.get("/{id}")
async def get_by_id(id: int, db: Connection = Depends(get_db), _=Depends(get_current_user)):
    row = await db.fetchrow(
        """SELECT i.*, u.nombre, u.primer_apellido, t.nombre AS taller_nombre
           FROM inscripciones i
           JOIN usuarios u ON u.id = i.usuario_id
           JOIN talleres t ON t.id = i.taller_id
           WHERE i.id = $1""",
        id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Inscripción no encontrada")
    return dict(row)


@router.post("", status_code=201)
async def inscribir(body: dict, db: Connection = Depends(get_db), current_user: dict = Depends(get_current_user)):
    taller_id = body.get("taller_id")
    if not taller_id:
        raise HTTPException(status_code=422, detail="taller_id es requerido")

    usuario_id = current_user["id"]

    cupo = await db.fetchrow(
        """SELECT cupo_total,
                  (SELECT COUNT(*) FROM inscripciones WHERE taller_id=$1 AND estado='activa') AS inscritos
           FROM talleres WHERE id=$1""",
        taller_id,
    )
    if not cupo:
        raise HTTPException(status_code=404, detail="Taller no encontrado")
    if int(cupo["inscritos"]) >= cupo["cupo_total"]:
        raise HTTPException(status_code=409, detail="Sin cupo disponible")

    row = await db.fetchrow(
        "INSERT INTO inscripciones (usuario_id, taller_id) VALUES ($1,$2) ON CONFLICT DO NOTHING RETURNING *",
        usuario_id, taller_id,
    )
    if not row:
        raise HTTPException(status_code=409, detail="Ya inscrito en este taller")
    return dict(row)


@router.put("/{id}")
async def update_estado(id: int, body: dict, db: Connection = Depends(get_db), _=Depends(get_current_user)):
    estado = body.get("estado")
    estado_final = body.get("estado_final")
    row = await db.fetchrow(
        """UPDATE inscripciones
           SET estado = COALESCE($1, estado), estado_final = COALESCE($2, estado_final)
           WHERE id = $3 RETURNING *""",
        estado, estado_final, id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Inscripción no encontrada")
    return dict(row)


@router.patch("/{id}")
async def patch_estado(id: int, body: dict, db: Connection = Depends(get_db), _=Depends(get_current_user)):
    estado = body.get("estado")
    row = await db.fetchrow(
        "UPDATE inscripciones SET estado=$1 WHERE id=$2 RETURNING *",
        estado, id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Inscripción no encontrada")
    return dict(row)


@router.delete("/{id}")
async def cancelar(id: int, db: Connection = Depends(get_db), _=Depends(get_current_user)):
    await db.execute("UPDATE inscripciones SET estado='cancelada' WHERE id=$1", id)
    return {"mensaje": "Inscripción cancelada"}


@router.get("/taller/{taller_id}")
async def get_by_taller(taller_id: int, db: Connection = Depends(get_db), _=Depends(get_current_user)):
    rows = await db.fetch(
        """SELECT i.*, u.nombre, u.primer_apellido, u.correo
           FROM inscripciones i JOIN usuarios u ON u.id = i.usuario_id
           WHERE i.taller_id = $1 ORDER BY i.fecha_inscripcion""",
        taller_id,
    )
    return [dict(r) for r in rows]
