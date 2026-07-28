# -*- coding: utf-8 -*-
"""
database.py
Capa de acceso a SQL Server con pyodbc.
Todas las vistas usan estas funciones; ninguna abre conexiones por su cuenta.
"""

import pyodbc
from contextlib import contextmanager

from config import DB_CONFIG


class ErrorBaseDatos(Exception):
    """Error controlado para mostrar al usuario en la interfaz."""
    pass


def cadena_conexion() -> str:
    partes = [
        f"DRIVER={DB_CONFIG['driver']}",
        f"SERVER={DB_CONFIG['server']}",
        f"DATABASE={DB_CONFIG['database']}",
    ]
    if DB_CONFIG.get("trusted_connection"):
        partes.append("Trusted_Connection=yes")
    else:
        partes.append(f"UID={DB_CONFIG['username']}")
        partes.append(f"PWD={DB_CONFIG['password']}")
    return ";".join(partes) + ";"


@contextmanager
def conexion(autocommit: bool = True):
    """
    Abre una conexión y la cierra siempre.

    Uso normal:      with conexion() as cn: ...
    Con transacción: with conexion(autocommit=False) as cn: ... cn.commit()
    """
    cn = None
    try:
        cn = pyodbc.connect(cadena_conexion(), timeout=DB_CONFIG.get("timeout", 10))
        cn.autocommit = autocommit
        yield cn
    except pyodbc.Error as ex:
        raise ErrorBaseDatos(_mensaje(ex)) from ex
    finally:
        if cn is not None:
            cn.close()


def _mensaje(ex: Exception) -> str:
    """Convierte el error de pyodbc en un texto útil para el usuario."""
    texto = str(ex)
    if "Login failed" in texto:
        return "El servidor rechazó las credenciales de conexión."
    if "server was not found" in texto or "no se pudo abrir" in texto.lower():
        return ("No se encontró el servidor de base de datos. "
                "Revisa DB_CONFIG['server'] en config.py.")
    if "Invalid object name" in texto:
        return "Falta una tabla o procedimiento. Ejecuta los scripts de la carpeta sql/."
    # pyodbc arma el mensaje como ('HY000', "[HY000] ... mensaje real ... (50000)")
    if "]" in texto:
        texto = texto.split("]")[-1]
    return texto.strip(" ()'\"")


def probar_conexion() -> tuple:
    """Devuelve (ok, mensaje). Se llama al arrancar la aplicación."""
    try:
        with conexion() as cn:
            cn.cursor().execute("SELECT 1").fetchone()
        return True, "Conexión establecida."
    except ErrorBaseDatos as ex:
        return False, str(ex)


# ------------------------------------------------------------------
# Helpers de consulta
# ------------------------------------------------------------------
def consultar(sql: str, parametros: tuple = ()) -> list:
    """SELECT que devuelve una lista de diccionarios."""
    with conexion() as cn:
        cur = cn.cursor()
        cur.execute(sql, parametros)
        columnas = [c[0] for c in cur.description]
        return [dict(zip(columnas, fila)) for fila in cur.fetchall()]


def consultar_uno(sql: str, parametros: tuple = ()):
    filas = consultar(sql, parametros)
    return filas[0] if filas else None


def escalar(sql: str, parametros: tuple = ()):
    with conexion() as cn:
        cur = cn.cursor()
        cur.execute(sql, parametros)
        fila = cur.fetchone()
        return fila[0] if fila else None


def ejecutar(sql: str, parametros: tuple = ()) -> int:
    """INSERT / UPDATE / DELETE. Devuelve el número de filas afectadas."""
    with conexion() as cn:
        cur = cn.cursor()
        cur.execute(sql, parametros)
        return cur.rowcount


def ejecutar_sp_multiple(sql: str, parametros: tuple = ()) -> list:
    """
    Ejecuta un procedimiento que devuelve varios result sets
    (los del dashboard) y regresa una lista de listas de diccionarios.
    """
    resultados = []
    with conexion() as cn:
        cur = cn.cursor()
        cur.execute(sql, parametros)
        while True:
            if cur.description:
                columnas = [c[0] for c in cur.description]
                resultados.append([dict(zip(columnas, f)) for f in cur.fetchall()])
            if not cur.nextset():
                break
    return resultados
