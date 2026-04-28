from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.database import get_pool, close_pool
from app.routes import auth, usuarios, talleres, inscripciones
from app.routes import roles, alumnos, instructores, temario, certificados, carreras


@asynccontextmanager
async def lifespan(app: FastAPI):
    await get_pool()
    yield
    await close_pool()


app = FastAPI(
    title="Sistema de Talleres API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(talleres.router)
app.include_router(inscripciones.router)
app.include_router(roles.router)
app.include_router(roles.router_usuario_roles)
app.include_router(alumnos.router)
app.include_router(instructores.router)
app.include_router(temario.router)
app.include_router(certificados.router)
app.include_router(carreras.router)


@app.get("/api/health", tags=["health"])
async def health():
    return {"status": "ok"}
