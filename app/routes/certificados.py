import io
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from asyncpg import Connection
from app.config.database import get_db
from app.middlewares.auth import get_current_user
from app.schemas.certificados import CertificadoCreate

router = APIRouter(prefix="/api/certificados", tags=["certificados"])

MESES = [
    "", "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


def _generar_pdf(
    nombre_alumno: str,
    nombre_taller: str,
    codigo_verificacion: str,
    fecha_emision: datetime,
    numero_sesiones: int | None,
) -> bytes:
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.lib.colors import HexColor, white
    from reportlab.pdfgen import canvas as pdfcanvas

    buffer = io.BytesIO()
    width, height = landscape(letter)
    c = pdfcanvas.Canvas(buffer, pagesize=landscape(letter))

    # Fondo azul oscuro
    c.setFillColor(HexColor("#0f2554"))
    c.rect(0, 0, width, height, fill=1, stroke=0)

    # Tarjeta blanca
    margin = 36
    c.setFillColor(white)
    c.roundRect(margin, margin, width - 2 * margin, height - 2 * margin, 12, fill=1, stroke=0)

    # Marco dorado
    c.setStrokeColor(HexColor("#c9a227"))
    c.setLineWidth(2.5)
    c.roundRect(margin + 10, margin + 10, width - 2 * (margin + 10), height - 2 * (margin + 10), 8, fill=0, stroke=1)

    # Líneas decorativas superiores
    gold = HexColor("#c9a227")
    c.setStrokeColor(gold)
    c.setLineWidth(1)
    cx = width / 2
    c.line(cx - 220, height - 72, cx - 20, height - 72)
    c.line(cx + 20, height - 72, cx + 220, height - 72)

    # Encabezado
    c.setFillColor(HexColor("#0f2554"))
    c.setFont("Helvetica-Bold", 26)
    c.drawCentredString(cx, height - 100, "CONSTANCIA DE PARTICIPACIÓN")

    c.setStrokeColor(gold)
    c.setLineWidth(2)
    c.line(cx - 200, height - 112, cx + 200, height - 112)

    # "Se otorga la presente a:"
    c.setFillColor(HexColor("#666666"))
    c.setFont("Helvetica", 13)
    c.drawCentredString(cx, height - 155, "Se otorga la presente a:")

    # Nombre del alumno
    c.setFillColor(HexColor("#0f2554"))
    c.setFont("Helvetica-Bold", 26)
    c.drawCentredString(cx, height - 195, nombre_alumno)

    name_w = c.stringWidth(nombre_alumno, "Helvetica-Bold", 26)
    c.setStrokeColor(gold)
    c.setLineWidth(1.5)
    c.line(cx - name_w / 2, height - 205, cx + name_w / 2, height - 205)

    # "Por haber acreditado..."
    c.setFillColor(HexColor("#555555"))
    c.setFont("Helvetica", 13)
    c.drawCentredString(cx, height - 248, "Por haber acreditado satisfactoriamente el curso:")

    # Nombre del taller
    c.setFillColor(HexColor("#0f2554"))
    c.setFont("Helvetica-BoldOblique", 19)
    c.drawCentredString(cx, height - 282, f'"{nombre_taller}"')

    # Duración
    y = height - 322
    if numero_sesiones:
        c.setFillColor(HexColor("#555555"))
        c.setFont("Helvetica", 13)
        c.drawCentredString(cx, y, f"Con una duración de {numero_sesiones} horas.")
        y -= 32
    else:
        y -= 10

    # Fecha y folio
    fecha_fmt = f"{fecha_emision.day} de {MESES[fecha_emision.month]} de {fecha_emision.year}"
    c.setFillColor(HexColor("#555555"))
    c.setFont("Helvetica", 12)
    c.drawCentredString(cx, y, f"Fecha de emisión: {fecha_fmt}")
    c.drawCentredString(cx, y - 18, f"Folio: {codigo_verificacion}")

    # Línea de firma
    sig_y = margin + 80
    c.setStrokeColor(HexColor("#333333"))
    c.setLineWidth(1)
    c.line(cx - 90, sig_y, cx + 90, sig_y)
    c.setFillColor(HexColor("#555555"))
    c.setFont("Helvetica", 11)
    c.drawCentredString(cx, sig_y - 16, "Coordinador Académico")

    c.save()
    buffer.seek(0)
    return buffer.getvalue()


@router.post("", status_code=201)
async def generar(body: CertificadoCreate, db: Connection = Depends(get_db), _=Depends(get_current_user)):
    inscripcion = await db.fetchrow(
        "SELECT id FROM inscripciones WHERE id=$1 AND estado='activa'", body.inscripcion_id
    )
    if not inscripcion:
        raise HTTPException(status_code=404, detail="Inscripción no encontrada o no está activa")

    ya_existe = await db.fetchrow("SELECT * FROM certificados WHERE inscripcion_id=$1", body.inscripcion_id)
    if ya_existe:
        return dict(ya_existe)

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


@router.get("/por-inscripcion/{inscripcion_id}")
async def por_inscripcion(inscripcion_id: int, db: Connection = Depends(get_db), _=Depends(get_current_user)):
    row = await db.fetchrow(
        "SELECT * FROM certificados WHERE inscripcion_id=$1", inscripcion_id
    )
    if not row:
        raise HTTPException(status_code=404, detail="Sin certificado para esta inscripción")
    return dict(row)


@router.get("/{id}/pdf")
async def descargar_pdf(id: int, db: Connection = Depends(get_db), _=Depends(get_current_user)):
    row = await db.fetchrow(
        """SELECT c.*, u.nombre, u.primer_apellido, u.segundo_apellido,
                  t.nombre AS taller_nombre, t.numero_sesiones,
                  c.fecha_emision
           FROM certificados c
           JOIN inscripciones i ON i.id = c.inscripcion_id
           JOIN usuarios u ON u.id = i.usuario_id
           JOIN talleres t ON t.id = i.taller_id
           WHERE c.id = $1""",
        id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Certificado no encontrado")

    nombre_completo = f"{row['nombre']} {row['primer_apellido']}"
    if row.get("segundo_apellido"):
        nombre_completo += f" {row['segundo_apellido']}"

    pdf_bytes = _generar_pdf(
        nombre_alumno=nombre_completo,
        nombre_taller=row["taller_nombre"],
        codigo_verificacion=row["codigo_verificacion"],
        fecha_emision=row["fecha_emision"],
        numero_sesiones=row.get("numero_sesiones"),
    )

    filename = f"constancia-{row['codigo_verificacion']}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


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
