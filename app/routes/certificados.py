import uuid
from fastapi import APIRouter, Depends, HTTPException
from asyncpg import Connection
from app.config.database import get_db
from app.middlewares.auth import get_current_user
from app.schemas.certificados import CertificadoCreate

router = APIRouter(prefix="/api/certificados", tags=["certificados"])


@router.post("", status_code=201)
async def generar(body: CertificadoCreate, db: Connection = Depends(get_db), _=Depends(get_current_user)):
    inscripcion = await db.fetchrow(
        "SELECT id FROM inscripciones WHERE id=$1 AND estado='activa'", body.inscripcion_id
    )
    if not inscripcion:
        raise HTTPException(status_code=404, detail="Inscripción no encontrada o no está activa")

    ya_existe = await db.fetchrow("SELECT id FROM certificados WHERE inscripcion_id=$1", body.inscripcion_id)
    if ya_existe:
        raise HTTPException(status_code=409, detail="Ya existe un certificado para esta inscripción")

    codigo = str(uuid.uuid4()).replace("-", "").upper()[:12]
    row = await db.fetchrow(
        "INSERT INTO certificados (inscripcion_id, codigo_verificacion) VALUES ($1,$2) RETURNING *",
        body.inscripcion_id, codigo,
    )
    return dict(row)


@router.get("/verificar/{codigo}")
async def verificar(codigo: str, db: Connection = Depends(get_db)):
    row = await db.fetchrow(
        """SELECT c.*, u.nombre, u.primer_apellido, t.nombre AS taller_nombre
           FROM certificados c
           JOIN inscripciones i ON i.id = c.inscripcion_id
           JOIN usuarios u ON u.id = i.usuario_id
           JOIN talleres t ON t.id = i.taller_id
           WHERE c.codigo_verificacion = $1""",
        codigo.upper(),
    )
    if not row:
        raise HTTPException(status_code=404, detail="Certificado no válido")
    return dict(row)


@router.get("/{id}")
async def get_by_id(id: int, db: Connection = Depends(get_db), _=Depends(get_current_user)):
    row = await db.fetchrow(
        """SELECT c.*, u.nombre, u.primer_apellido, t.nombre AS taller_nombre
           FROM certificados c
           JOIN inscripciones i ON i.id = c.inscripcion_id
           JOIN usuarios u ON u.id = i.usuario_id
           JOIN talleres t ON t.id = i.taller_id
           WHERE c.id = $1""",
        id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Certificado no encontrado")
    return dict(row)
