from fastapi import APIRouter, Depends, HTTPException
from asyncpg import Connection
from app.config.database import get_db
from app.middlewares.auth import get_current_user
from app.schemas.usuarios import UsuarioUpdate

router = APIRouter(prefix="/api/usuarios", tags=["usuarios"])


@router.get("/me/inscripciones")
async def mis_inscripciones(db: Connection = Depends(get_db), current_user: dict = Depends(get_current_user)):
    import json
    rows = await db.fetch(
        """SELECT i.*, row_to_json(t.*) AS taller
           FROM inscripciones i JOIN talleres t ON t.id = i.taller_id
           WHERE i.usuario_id = $1 ORDER BY i.fecha_inscripcion DESC""",
        current_user["id"],
    )
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
        """SELECT u.id, u.nombre, u.primer_apellido, u.segundo_apellido, u.correo,
                  u.telefono, u.activo, u.created_at, a.numero_cuenta,
                  COALESCE(
                      json_agg(json_build_object('id', r.id, 'nombre', r.nombre))
                      FILTER (WHERE r.id IS NOT NULL), '[]'::json
                  ) AS roles
           FROM usuarios u
           LEFT JOIN alumnos a ON a.usuario_id = u.id
           LEFT JOIN usuario_rol ur ON ur.usuario_id = u.id
           LEFT JOIN roles r ON r.id = ur.rol_id
           GROUP BY u.id, a.numero_cuenta
           ORDER BY u.id"""
    )
    result = []
    for r in rows:
        d = dict(r)
        roles_raw = d.get("roles") or []
        if isinstance(roles_raw, str):
            import json as _json
            roles_raw = _json.loads(roles_raw)
        d["roles"] = roles_raw if isinstance(roles_raw, list) else []
        result.append(d)
    return result


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
    existing = await db.fetchrow(
        "SELECT id, nombre, primer_apellido, segundo_apellido, telefono, foto_url, activo FROM usuarios WHERE id=$1", id
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    nombre = body.nombre if body.nombre is not None else existing["nombre"]
    primer_apellido = body.primer_apellido if body.primer_apellido is not None else existing["primer_apellido"]
    segundo_apellido = body.segundo_apellido if body.segundo_apellido is not None else existing["segundo_apellido"]
    telefono = body.telefono if body.telefono is not None else existing["telefono"]
    foto_url = body.foto_url if body.foto_url is not None else existing["foto_url"]
    activo = body.activo if body.activo is not None else existing["activo"]

    row = await db.fetchrow(
        """UPDATE usuarios SET nombre=$1, primer_apellido=$2, segundo_apellido=$3,
           telefono=$4, foto_url=$5, activo=$6, updated_at=CURRENT_TIMESTAMP
           WHERE id=$7 RETURNING id, nombre, correo, primer_apellido, segundo_apellido, telefono, activo""",
        nombre, primer_apellido, segundo_apellido, telefono, foto_url, activo, id,
    )

    if body.carrera is not None or body.semestre is not None or body.numero_cuenta is not None:
        alumno = await db.fetchrow("SELECT id, numero_cuenta, carrera_id, semestre FROM alumnos WHERE usuario_id=$1", id)

        # Resolve carrera_id once if carrera was provided
        carrera_id = alumno["carrera_id"] if alumno else None
        if body.carrera is not None:
            carrera_row = await db.fetchrow("SELECT id FROM carreras WHERE nombre=$1", body.carrera)
            if not carrera_row:
                carrera_row = await db.fetchrow(
                    "INSERT INTO carreras (nombre) VALUES ($1) ON CONFLICT (nombre) DO UPDATE SET nombre=EXCLUDED.nombre RETURNING id",
                    body.carrera,
                )
            carrera_id = carrera_row["id"]

        semestre_int = alumno["semestre"] if alumno else None
        if body.semestre is not None:
            try:
                semestre_int = int("".join(filter(str.isdigit, body.semestre)))
                if semestre_int < 1 or semestre_int > 12:
                    semestre_int = None
            except (ValueError, TypeError):
                semestre_int = None

        if alumno:
            numero_cuenta = body.numero_cuenta if body.numero_cuenta is not None else alumno["numero_cuenta"]
            await db.execute(
                "UPDATE alumnos SET numero_cuenta=$1, carrera_id=$2, semestre=$3 WHERE usuario_id=$4",
                numero_cuenta, carrera_id, semestre_int, id,
            )
        elif body.numero_cuenta:
            await db.execute(
                "INSERT INTO alumnos (usuario_id, numero_cuenta, carrera_id, semestre) VALUES ($1,$2,$3,$4) ON CONFLICT DO NOTHING",
                id, body.numero_cuenta, carrera_id, semestre_int,
            )

    return dict(row)


@router.delete("/{id}")
async def deactivate(id: int, db: Connection = Depends(get_db), _=Depends(get_current_user)):
    await db.execute("UPDATE usuarios SET activo=false WHERE id=$1", id)
    return {"message": "Usuario desactivado"}
