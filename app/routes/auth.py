from fastapi import APIRouter, Depends, HTTPException
from asyncpg import Connection
from app.config.database import get_db
from app.config.security import hash_password, verify_password, create_token
from app.middlewares.auth import get_current_user
from app.schemas.auth import RegisterRequest, LoginRequest

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", status_code=201)
async def register(body: RegisterRequest, db: Connection = Depends(get_db)):
    existe = await db.fetchrow("SELECT id FROM usuarios WHERE correo=$1", body.correo)
    if existe:
        raise HTTPException(status_code=409, detail="El correo ya está registrado")

    password_hash = hash_password(body.password)
    row = await db.fetchrow(
        """INSERT INTO usuarios (nombre, primer_apellido, segundo_apellido, correo, telefono, password_hash)
           VALUES ($1,$2,$3,$4,$5,$6) RETURNING id, nombre, correo, primer_apellido, segundo_apellido, telefono, activo, created_at""",
        body.nombre, body.primer_apellido, body.segundo_apellido,
        body.correo, body.telefono, password_hash,
    )
    usuario = dict(row)
    usuario_id = usuario["id"]
    roles_asignados = []

    if body.roles:
        for nombre_rol in body.roles:
            rol = await db.fetchrow("SELECT id FROM roles WHERE nombre=$1", nombre_rol)
            if rol:
                await db.execute(
                    "INSERT INTO usuario_rol (usuario_id, rol_id) VALUES ($1,$2) ON CONFLICT DO NOTHING",
                    usuario_id, rol["id"],
                )
                roles_asignados.append({"id": rol["id"], "nombre": nombre_rol})

        if "ponente" in body.roles:
            await db.execute(
                "INSERT INTO instructores (usuario_id) VALUES ($1) ON CONFLICT DO NOTHING",
                usuario_id,
            )

    usuario["roles"] = roles_asignados
    usuario["numero_cuenta"] = None
    usuario["carrera"] = None
    usuario["semestre"] = None
    return usuario


@router.post("/login")
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

    token = create_token({"id": row["id"], "nombre": row["nombre"], "roles": [r for r in (row["roles"] or []) if r]})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me")
async def me(db: Connection = Depends(get_db), current_user: dict = Depends(get_current_user)):
    row = await db.fetchrow(
        """SELECT u.id, u.nombre, u.primer_apellido, u.segundo_apellido, u.correo,
                  u.telefono, u.foto_url, u.activo, u.created_at,
                  a.numero_cuenta, a.semestre,
                  c.nombre AS carrera
           FROM usuarios u
           LEFT JOIN alumnos a ON a.usuario_id = u.id
           LEFT JOIN carreras c ON c.id = a.carrera_id
           WHERE u.id = $1""",
        current_user["id"],
    )
    if not row:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    roles_rows = await db.fetch(
        "SELECT r.id, r.nombre FROM roles r JOIN usuario_rol ur ON ur.rol_id = r.id WHERE ur.usuario_id = $1",
        current_user["id"],
    )

    d = dict(row)
    d["roles"] = [dict(r) for r in roles_rows]
    d["semestre"] = str(d["semestre"]) if d["semestre"] is not None else None
    return d
