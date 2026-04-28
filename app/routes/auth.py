from fastapi import APIRouter, Depends, HTTPException, status
from asyncpg import Connection
from app.config.database import get_db
from app.config.security import hash_password, verify_password, create_token
from app.middlewares.auth import get_current_user
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", status_code=201)
async def register(body: RegisterRequest, db: Connection = Depends(get_db)):
    existe = await db.fetchrow("SELECT id FROM usuarios WHERE correo=$1", body.correo)
    if existe:
        raise HTTPException(status_code=409, detail="El correo ya está registrado")

    password_hash = hash_password(body.password)
    row = await db.fetchrow(
        """INSERT INTO usuarios (nombre, primer_apellido, segundo_apellido, correo, telefono, password_hash)
           VALUES ($1,$2,$3,$4,$5,$6) RETURNING id, nombre, correo""",
        body.nombre, body.primer_apellido, body.segundo_apellido,
        body.correo, body.telefono, password_hash,
    )
    return {"usuario": dict(row)}


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: Connection = Depends(get_db)):
    row = await db.fetchrow(
        """SELECT u.id, u.nombre, u.primer_apellido, u.password_hash, u.activo,
                  array_agg(r.nombre) AS roles
           FROM usuarios u
           LEFT JOIN usuario_rol ur ON ur.usuario_id = u.id
           LEFT JOIN roles r ON r.id = ur.rol_id
           WHERE u.correo = $1
           GROUP BY u.id""",
        body.correo,
    )
    if not row:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    if not row["activo"]:
        raise HTTPException(status_code=403, detail="Cuenta desactivada")
    if not verify_password(body.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    token = create_token({"id": row["id"], "nombre": row["nombre"], "roles": list(row["roles"] or [])})
    return {"token": token, "usuario": {"id": row["id"], "nombre": row["nombre"], "roles": list(row["roles"] or [])}}


@router.get("/me")
async def me(db: Connection = Depends(get_db), current_user: dict = Depends(get_current_user)):
    row = await db.fetchrow(
        """SELECT u.id, u.nombre, u.primer_apellido, u.segundo_apellido, u.correo,
                  u.telefono, u.foto_url, u.activo, u.created_at,
                  array_agg(r.nombre) AS roles
           FROM usuarios u
           LEFT JOIN usuario_rol ur ON ur.usuario_id = u.id
           LEFT JOIN roles r ON r.id = ur.rol_id
           WHERE u.id = $1
           GROUP BY u.id""",
        current_user["id"],
    )
    if not row:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    d = dict(row)
    d["roles"] = [r for r in (d["roles"] or []) if r is not None]
    return d
