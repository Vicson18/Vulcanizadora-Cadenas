# -*- coding: utf-8 -*-
"""
impresion.py
Genera la orden de servicio en PDF para entregársela al cliente
y la abre con el visor del sistema.

Requiere reportlab. Si no está instalado, la aplicación sigue
funcionando y solo se desactiva la impresión.
"""

import os
import platform
import subprocess
import unicodedata
from datetime import date, datetime

from config import TALLER, CARPETA_ORDENES

try:
    from reportlab.lib.pagesizes import LETTER
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    REPORTLAB_DISPONIBLE = True
except ImportError:
    REPORTLAB_DISPONIBLE = False


MENSAJE_SIN_REPORTLAB = (
    "Para imprimir la orden falta instalar reportlab. "
    "Abre la terminal y ejecuta:  pip install reportlab"
)

# Paleta de impresión: en papel el amarillo no se ve, así que el
# acento se convierte en negro y grises.
TINTA = "#111111"
GRIS = "#6B6B6B"
GRIS_CLARO = "#E4E4E4"

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


# ==================================================================
# Utilidades
# ==================================================================
def _fecha_texto(valor) -> str:
    if isinstance(valor, datetime):
        valor = valor.date()
    if not isinstance(valor, date):
        return str(valor or "")
    return f"{valor.day} de {MESES[valor.month - 1]} de {valor.year}"


def _limpiar(texto) -> str:
    """
    Las fuentes base de reportlab no traen todos los glifos.
    Se conservan los acentos y la ñ (sí existen en Helvetica) y se
    quitan los caracteres raros que saldrían como cuadros negros.
    """
    if texto is None:
        return ""
    texto = str(texto)
    salida = []
    for caracter in texto:
        if caracter in "•·—–":
            salida.append("-")
        elif unicodedata.category(caracter).startswith("C"):
            salida.append(" ")
        else:
            salida.append(caracter)
    return "".join(salida)


def _recortar(c, texto, ancho, fuente, tamano) -> str:
    """Corta el texto para que quepa en la columna."""
    texto = _limpiar(texto)
    if c.stringWidth(texto, fuente, tamano) <= ancho:
        return texto
    while texto and c.stringWidth(texto + "...", fuente, tamano) > ancho:
        texto = texto[:-1]
    return texto + "..."


def carpeta_salida() -> str:
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), CARPETA_ORDENES)
    os.makedirs(ruta, exist_ok=True)
    return ruta


# ==================================================================
# Generación del PDF
# ==================================================================
def generar_orden_pdf(orden: dict, ruta_destino: str = None) -> str:
    """
    orden = {"cabecera": {...}, "detalle": [{...}, ...]}
    Devuelve la ruta del archivo generado.
    """
    if not REPORTLAB_DISPONIBLE:
        raise RuntimeError(MENSAJE_SIN_REPORTLAB)

    cabecera = orden["cabecera"]
    detalle = orden["detalle"]

    if ruta_destino is None:
        nombre = f"{cabecera['Folio']}.pdf".replace("/", "-")
        ruta_destino = os.path.join(carpeta_salida(), nombre)

    ancho, alto = LETTER
    c = canvas.Canvas(ruta_destino, pagesize=LETTER)
    c.setTitle(f"Orden {cabecera['Folio']}")

    margen = 18 * mm
    util = ancho - 2 * margen
    y = alto - margen

    # ---------- Encabezado -----------------------------------------
    alto_banda = 26 * mm
    c.setFillColor(colors.HexColor(TINTA))
    c.rect(margen, y - alto_banda, util, alto_banda, stroke=0, fill=1)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 19)
    c.drawString(margen + 8 * mm, y - 11 * mm, _limpiar(TALLER["nombre"]).upper())

    c.setFont("Helvetica", 8)
    c.drawString(margen + 8 * mm, y - 16 * mm, _limpiar(TALLER["direccion"]))
    c.drawString(margen + 8 * mm, y - 20 * mm,
                 f"Tel. {_limpiar(TALLER['telefono'])}   ·   "
                 f"{_limpiar(TALLER['horario'])}".replace("·", "-"))

    # Folio a la derecha
    c.setFont("Helvetica", 7)
    c.drawRightString(ancho - margen - 8 * mm, y - 9 * mm, "ORDEN DE SERVICIO")
    c.setFont("Helvetica-Bold", 15)
    c.drawRightString(ancho - margen - 8 * mm, y - 16 * mm, _limpiar(cabecera["Folio"]))
    c.setFont("Helvetica", 8)
    c.drawRightString(ancho - margen - 8 * mm, y - 21 * mm,
                      _fecha_texto(cabecera["FechaOrden"]))

    y -= alto_banda

    # ---------- Huella de llanta (el detalle de la marca) ----------
    y -= 3 * mm
    _huella(c, margen, y, util, 3 * mm)
    y -= 10 * mm

    # ---------- Datos del cliente y del vehículo -------------------
    columna = util / 2
    y_bloque = y

    _campo(c, margen, y_bloque, "CLIENTE", cabecera.get("Cliente"), columna - 6 * mm)
    _campo(c, margen + columna, y_bloque, "AUTOMÓVIL",
           cabecera.get("Automovil") or "No especificado", columna - 6 * mm)
    y_bloque -= 12 * mm

    _campo(c, margen, y_bloque, "TELÉFONO",
           cabecera.get("Telefono") or "-", columna - 6 * mm)
    _campo(c, margen + columna, y_bloque, "PLACAS",
           cabecera.get("Placas") or "-", columna - 6 * mm)
    y_bloque -= 12 * mm

    _campo(c, margen, y_bloque, "RECIBIÓ",
           cabecera.get("Capturo") or "-", columna - 6 * mm)
    _campo(c, margen + columna, y_bloque, "ESTATUS",
           cabecera.get("Estatus") or "-", columna - 6 * mm)

    y = y_bloque - 14 * mm

    # ---------- Tabla de renglones ---------------------------------
    col_x = [
        margen,                       # medida
        margen + 32 * mm,             # concepto
        margen + util - 52 * mm,      # cantidad
        margen + util - 36 * mm,      # precio
        margen + util,                # importe (alineado a la derecha)
    ]

    c.setFillColor(colors.HexColor(TINTA))
    c.rect(margen, y - 7 * mm, util, 7 * mm, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(col_x[0] + 2 * mm, y - 5 * mm, "MEDIDA")
    c.drawString(col_x[1], y - 5 * mm, "CONCEPTO")
    c.drawRightString(col_x[2] + 10 * mm, y - 5 * mm, "CANT")
    c.drawRightString(col_x[3] + 14 * mm, y - 5 * mm, "P. UNIT")
    c.drawRightString(col_x[4] - 2 * mm, y - 5 * mm, "IMPORTE")

    y -= 7 * mm

    c.setFont("Helvetica", 9)
    for i, renglon in enumerate(detalle):
        alto_fila = 7 * mm

        if i % 2 == 1:
            c.setFillColor(colors.HexColor(GRIS_CLARO))
            c.rect(margen, y - alto_fila, util, alto_fila, stroke=0, fill=1)

        c.setFillColor(colors.HexColor(TINTA))
        texto_y = y - 5 * mm

        c.drawString(col_x[0] + 2 * mm, texto_y, _limpiar(renglon.get("Medida")))

        concepto = renglon.get("Descripcion") or "Servicio de llanta"
        if renglon.get("Marca"):
            concepto = f"{concepto} ({renglon['Marca']})"
        c.drawString(col_x[1], texto_y,
                     _recortar(c, concepto, col_x[2] - col_x[1] - 4 * mm, "Helvetica", 9))

        c.drawRightString(col_x[2] + 10 * mm, texto_y, str(renglon.get("Cantidad", 0)))
        c.drawRightString(col_x[3] + 14 * mm, texto_y,
                          f"${float(renglon.get('PrecioUnitario') or 0):,.2f}")
        c.drawRightString(col_x[4] - 2 * mm, texto_y,
                          f"${float(renglon.get('Importe') or 0):,.2f}")

        y -= alto_fila

    c.setStrokeColor(colors.HexColor(GRIS))
    c.setLineWidth(0.6)
    c.line(margen, y, margen + util, y)

    # ---------- Total ----------------------------------------------
    y -= 14 * mm
    ancho_total = 66 * mm
    x_total = margen + util - ancho_total

    c.setFillColor(colors.HexColor(TINTA))
    c.rect(x_total, y - 2 * mm, ancho_total, 13 * mm, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica", 8)
    c.drawString(x_total + 4 * mm, y + 6 * mm, "TOTAL")
    c.setFont("Helvetica-Bold", 15)
    c.drawRightString(x_total + ancho_total - 4 * mm, y + 3 * mm,
                      f"${float(cabecera.get('Total') or 0):,.2f}")

    piezas = sum(int(r.get("Cantidad") or 0) for r in detalle)
    c.setFillColor(colors.HexColor(GRIS))
    c.setFont("Helvetica", 8)
    c.drawString(margen, y + 6 * mm,
                 f"{piezas} llanta(s) - {len(detalle)} concepto(s)")

    y -= 12 * mm

    # ---------- Notas ------------------------------------------------
    if cabecera.get("Observaciones"):
        c.setFillColor(colors.HexColor(GRIS))
        c.setFont("Helvetica-Bold", 7)
        c.drawString(margen, y, "NOTAS")
        c.setFillColor(colors.HexColor(TINTA))
        c.setFont("Helvetica", 9)
        y -= 5 * mm
        for linea in _partir(c, cabecera["Observaciones"], util, "Helvetica", 9):
            c.drawString(margen, y, linea)
            y -= 4.5 * mm
        y -= 4 * mm

    # ---------- Firma y condiciones ----------------------------------
    y_firma = max(y, margen + 34 * mm)

    c.setStrokeColor(colors.HexColor(TINTA))
    c.setLineWidth(0.8)
    c.line(margen, y_firma, margen + 70 * mm, y_firma)
    c.setFillColor(colors.HexColor(GRIS))
    c.setFont("Helvetica", 7)
    c.drawString(margen, y_firma - 4 * mm, "FIRMA DEL CLIENTE")

    c.line(margen + util - 70 * mm, y_firma, margen + util, y_firma)
    c.drawString(margen + util - 70 * mm, y_firma - 4 * mm, "ENTREGÓ")

    # Condiciones al pie
    c.setFont("Helvetica", 6.5)
    y_pie = margen + 12 * mm
    for linea in _partir(c, TALLER["leyenda"], util, "Helvetica", 6.5):
        c.drawString(margen, y_pie, linea)
        y_pie -= 3.2 * mm

    c.setFont("Helvetica", 6)
    c.drawRightString(
        margen + util, margen + 4 * mm,
        f"Impreso el {_fecha_texto(date.today())}",
    )

    # ---------- Sello de cancelada -----------------------------------
    if (cabecera.get("Estatus") or "").upper() == "CANCELADA":
        c.saveState()
        c.setFillColor(colors.HexColor("#C8C8C8"))
        c.translate(ancho / 2, alto / 2)
        c.rotate(32)
        c.setFont("Helvetica-Bold", 78)
        c.drawCentredString(0, 0, "CANCELADA")
        c.restoreState()

    c.showPage()
    c.save()
    return ruta_destino


def _huella(c, x, y, ancho, alto, bloques=48):
    """Banda con forma de huella de llanta, igual que en la pantalla."""
    paso = ancho / bloques
    for i in range(bloques):
        c.setFillColor(colors.HexColor(TINTA if i % 2 == 0 else GRIS_CLARO))
        c.rect(x + i * paso, y - alto, paso * 0.6, alto, stroke=0, fill=1)


def _campo(c, x, y, etiqueta, valor, ancho):
    c.setFillColor(colors.HexColor(GRIS))
    c.setFont("Helvetica-Bold", 7)
    c.drawString(x, y, _limpiar(etiqueta))

    c.setFillColor(colors.HexColor(TINTA))
    c.setFont("Helvetica", 11)
    c.drawString(x, y - 5.5 * mm, _recortar(c, valor, ancho, "Helvetica", 11))

    c.setStrokeColor(colors.HexColor(GRIS_CLARO))
    c.setLineWidth(0.5)
    c.line(x, y - 7.5 * mm, x + ancho, y - 7.5 * mm)


def _partir(c, texto, ancho, fuente, tamano) -> list:
    """Parte el texto en líneas que quepan en el ancho dado."""
    palabras = _limpiar(texto).split()
    lineas, actual = [], ""
    for palabra in palabras:
        prueba = f"{actual} {palabra}".strip()
        if c.stringWidth(prueba, fuente, tamano) <= ancho:
            actual = prueba
        else:
            if actual:
                lineas.append(actual)
            actual = palabra
    if actual:
        lineas.append(actual)
    return lineas


# ==================================================================
# Abrir el archivo con el visor del sistema
# ==================================================================
def abrir_archivo(ruta: str) -> None:
    sistema = platform.system()
    if sistema == "Windows":
        os.startfile(ruta)                                  # noqa: S606
    elif sistema == "Darwin":
        subprocess.run(["open", ruta], check=False)
    else:
        subprocess.run(["xdg-open", ruta], check=False)


def imprimir_orden(orden: dict) -> str:
    """Genera el PDF y lo abre. Devuelve la ruta."""
    ruta = generar_orden_pdf(orden)
    abrir_archivo(ruta)
    return ruta
