# -*- coding: utf-8 -*-
"""
config.py
Configuración central de la aplicación: conexión a base de datos,
paleta de colores y tipografías.
"""

import os

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
    "nombre": "VULCANIZADORA CADENA",
    "direccion": "Av. Principal 123, Col. Centro, Apodaca, N.L.",
    "telefono": "81 0000 0000",
    "horario": "Lunes a sábado de 8:00 a 19:00",
    "leyenda": ("La garantía cubre el servicio realizado, no daños previos de la "
                "llanta o del rin. Vehículos no recogidos después de 30 días "
                "generan almacenaje."),
}

# Carpeta donde se guardan las órdenes en PDF (se crea sola)
CARPETA_ORDENES = "ordenes_impresas"

# Logo del taller: fondo de la pantalla de acceso
RUTA_LOGO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "logo.jpeg")

# ------------------------------------------------------------------
# PALETA  ·  "Rojo Metálico & Negro"
# Negro de taller de fondo, gis de taller para el texto,
# rojo metálico como único acento fuerte.
# ------------------------------------------------------------------
C = {
    "asfalto":      "#0F0E0E",   # fondo de ventana
    "hule":         "#1C1919",   # tarjetas y paneles
    "hule_alto":    "#282323",   # campos, filas alternas
    "linea":        "#403838",   # bordes y separadores
    "gis":          "#F2EDEC",   # texto principal
    "gis_tenue":    "#A69B99",   # texto secundario
    "altavis":      "#FF1436",   # acento: rojo metálico brillante
    "altavis_hover":"#D40E2B",
    "barra":        "#FF3355",   # tira superior: rojo claro brillante
    "parche":       "#E8862D",   # naranja de aviso (alertas suaves)
    "verde":        "#3DD68C",   # OK / terminado
    "rojo":         "#FF4B5C",   # error / cancelado
    "azul":         "#4C9FE5",   # informativo
}

# Colores para los segmentos de las gráficas de dona
# (se mantienen medios/claros a propósito: el número se dibuja encima en tono oscuro)
SERIE_COLORES = ["#FF1436", "#E8862D", "#4C9FE5", "#3DD68C", "#B0A8A6", "#D4AF37"]

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
CATEGORIAS_PIEZA = ["AUTO", "MOTO"]
ESTATUS_ORDEN = ["ABIERTA", "EN PROCESO", "TERMINADA", "CANCELADA"]

# Servicios de un clic para el formulario de "Crear orden": al presionarlos
# solo rellenan el campo Concepto, el operador sigue eligiendo medida y precio.
SERVICIOS_RAPIDOS = [
    "Balanceo de rines",
    "Inflado",
    "Revisión de presión",
    "Cambio de válvulas",
]
