# -*- coding: utf-8 -*-
"""
config.py
Configuración central de la aplicación: conexión a base de datos,
paleta de colores y tipografías.
"""

# ------------------------------------------------------------------
# BASE DE DATOS
# ------------------------------------------------------------------
# Cambia SERVER por tu instancia. Ejemplos:
#   LocalDB   -> r"(localdb)\MSSQLLocalDB"
#   Local     -> r".\SQLEXPRESS"
#   Remoto    -> "192.168.1.50,1433"
DB_CONFIG = {
    "driver": "{ODBC Driver 17 for SQL Server}",
    "server": r"(localdb)\MSSQLLocalDB",
    "database": "VulcaDB",
    "trusted_connection": True,   # True = autenticación de Windows
    "username": "",               # se usa solo si trusted_connection = False
    "password": "",
    "timeout": 10,
}

APP_NOMBRE = "Vulcanizadora"
APP_SUBTITULO = "Control de piso"
APP_VERSION = "1.1.0"

# ------------------------------------------------------------------
# DATOS DEL TALLER
# Es lo que se imprime en la orden que se le entrega al cliente.
# Cámbialos por los reales antes de usar la aplicación.
# ------------------------------------------------------------------
TALLER = {
    "nombre": "VULCANIZADORA CADENAS",
    "direccion": "Av. Principal 123, Col. Centro, Apodaca, N.L.",
    "telefono": "81 0000 0000",
    "horario": "Lunes a sábado de 8:00 a 19:00",
    "leyenda": ("La garantía cubre el servicio realizado, no daños previos de la "
                "llanta o del rin. Vehículos no recogidos después de 30 días "
                "generan almacenaje."),
}

# Carpeta donde se guardan las órdenes en PDF (se crea sola)
CARPETA_ORDENES = "ordenes_impresas"

# ------------------------------------------------------------------
# PALETA  ·  "Asfalto & Cal"
# Asfalto mojado de fondo, gis de taller para el texto,
# amarillo de alta visibilidad (el del chaleco) como único acento fuerte.
# ------------------------------------------------------------------
C = {
    "asfalto":      "#0E1113",   # fondo de ventana
    "hule":         "#171B1F",   # tarjetas y paneles
    "hule_alto":    "#20262B",   # campos, filas alternas
    "linea":        "#2C343B",   # bordes y separadores
    "gis":          "#E8EDF2",   # texto principal
    "gis_tenue":    "#8A959E",   # texto secundario
    "altavis":      "#FFC145",   # acento: amarillo alta visibilidad
    "altavis_hover":"#E5A92B",
    "parche":       "#E85D3D",   # naranja de parche caliente (alertas suaves)
    "verde":        "#3DD68C",   # OK / terminado
    "rojo":         "#FF5A5F",   # error / cancelado
    "azul":         "#4CB2E5",   # informativo
}

# Colores para los segmentos de las gráficas de dona
SERIE_COLORES = ["#FFC145", "#E85D3D", "#4CB2E5", "#3DD68C", "#B08CFF", "#8A959E"]

# ------------------------------------------------------------------
# TIPOGRAFÍAS
# Bahnschrift viene con Windows 10/11: condensada, industrial, legible
# a distancia (la pantalla se ve desde el piso del taller).
# Si no existe, main.py cae a Segoe UI automáticamente.
# ------------------------------------------------------------------
FUENTE_TITULO = "Bahnschrift SemiBold Condensed"
FUENTE_TEXTO = "Segoe UI"
FUENTE_DATOS = "Consolas"

F = {
    "display": (FUENTE_TITULO, 34),
    "titulo":  (FUENTE_TITULO, 22),
    "seccion": (FUENTE_TITULO, 15),
    "cuerpo":  (FUENTE_TEXTO, 13),
    "chico":   (FUENTE_TEXTO, 11),
    "etiqueta":(FUENTE_TEXTO, 11, "bold"),
    "dato":    (FUENTE_DATOS, 13),
    "metrica": (FUENTE_TITULO, 30),
}

# ------------------------------------------------------------------
# REGLAS DE NEGOCIO
# ------------------------------------------------------------------
TIPOS_PIEZA = ["USADA", "NUEVA"]
ESTATUS_ORDEN = ["ABIERTA", "EN PROCESO", "TERMINADA", "CANCELADA"]
