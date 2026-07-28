# -*- coding: utf-8 -*-
"""
repositorio.py
Operaciones de negocio contra la base de datos.
Las vistas nunca escriben SQL: llaman a estas funciones.
"""

import hashlib
import secrets
from datetime import date

import pyodbc

from database import conexion, consultar, consultar_uno, ejecutar, ejecutar_sp_multiple, ErrorBaseDatos


# ==================================================================
# USUARIOS / LOGIN
# ==================================================================
def _hash(password: str, salt: str) -> str:
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def validar_acceso(username: str, password: str):
    """
    Devuelve el diccionario del usuario si las credenciales son correctas,
    o None si no lo son.
    """
    usuario = consultar_uno(
        """
        SELECT UsuarioID, Username, PasswordHash, Salt, NombreCompleto, Rol
        FROM   dbo.Usuarios
        WHERE  Username = ? AND Activo = 1
        """,
        (username,),
    )
    if usuario is None:
        return None

    if _hash(password, usuario["Salt"]) != usuario["PasswordHash"]:
        return None

    ejecutar(
        "UPDATE dbo.Usuarios SET UltimoAcceso = SYSDATETIME() WHERE UsuarioID = ?",
        (usuario["UsuarioID"],),
    )
    usuario.pop("PasswordHash", None)
    usuario.pop("Salt", None)
    return usuario


def crear_usuario(username: str, password: str, nombre: str = None, rol: str = "OPERADOR") -> int:
    """Alta de usuario. Útil para dar de alta al personal del taller."""
    salt = secrets.token_hex(16)
    with conexion() as cn:
        cur = cn.cursor()
        cur.execute(
            """
            INSERT INTO dbo.Usuarios (Username, PasswordHash, Salt, NombreCompleto, Rol)
            VALUES (?, ?, ?, ?, ?);
            SELECT SCOPE_IDENTITY();
            """,
            (username, _hash(password, salt), salt, nombre, rol),
        )
        return int(cur.fetchone()[0])


def cambiar_password(usuario_id: int, password_nuevo: str) -> None:
    salt = secrets.token_hex(16)
    ejecutar(
        "UPDATE dbo.Usuarios SET PasswordHash = ?, Salt = ? WHERE UsuarioID = ?",
        (_hash(password_nuevo, salt), salt, usuario_id),
    )


# ==================================================================
# DASHBOARD
# ==================================================================
def dashboard_diario(fecha: date = None) -> dict:
    fecha = fecha or date.today()
    partes = ejecutar_sp_multiple("{CALL dbo.sp_Dashboard_Diario (?)}", (fecha,))
    totales = partes[0][0] if partes and partes[0] else {}
    desglose = partes[1] if len(partes) > 1 else []
    return {"totales": _normaliza_totales(totales), "desglose": desglose}


def dashboard_semanal(fecha: date = None) -> dict:
    fecha = fecha or date.today()
    partes = ejecutar_sp_multiple("{CALL dbo.sp_Dashboard_Semanal (?)}", (fecha,))
    totales = partes[0][0] if partes and partes[0] else {}
    desglose = partes[1] if len(partes) > 1 else []
    return {"totales": _normaliza_totales(totales), "desglose": desglose}


def _normaliza_totales(fila: dict) -> dict:
    return {
        "Ordenes": int(fila.get("Ordenes") or 0),
        "Piezas": int(fila.get("Piezas") or 0),
        "Ingresos": float(fila.get("Ingresos") or 0),
        "Terminadas": int(fila.get("Terminadas") or 0),
    }


def ordenes_recientes(limite: int = 12) -> list:
    return consultar(
        f"""
        SELECT TOP {int(limite)}
               OrdenID, Folio, FechaOrden, Cliente, Automovil, Piezas, Total, Estatus
        FROM   dbo.vw_Ordenes
        ORDER BY OrdenID DESC
        """
    )


def piezas_bajo_stock() -> list:
    return consultar(
        """
        SELECT Codigo, Tipo, Medida, Marca, Cantidad, StockMinimo
        FROM   dbo.vw_Inventario
        WHERE  Activo = 1 AND BajoStock = 1
        ORDER BY Cantidad ASC
        """
    )


# ==================================================================
# CATÁLOGOS
# ==================================================================
def listar_medidas() -> list:
    return consultar(
        """
        SELECT MedidaID, Medida
        FROM   dbo.MedidasLlanta
        WHERE  Activo = 1
        ORDER BY Medida
        """
    )


def agregar_medida(medida: str) -> int:
    """Da de alta una medida nueva si no existe y devuelve su MedidaID."""
    medida = medida.strip().upper()
    existente = consultar_uno(
        "SELECT MedidaID FROM dbo.MedidasLlanta WHERE Medida = ?", (medida,)
    )
    if existente:
        return existente["MedidaID"]

    ancho = perfil = rin = None
    try:
        cuerpo = medida.replace("LT", "").replace("P", "")
        ancho = int(cuerpo.split("/")[0])
        perfil = int(cuerpo.split("/")[1].split("R")[0])
        rin = int(cuerpo.split("R")[1])
    except (ValueError, IndexError):
        pass  # medida con formato libre: se guarda tal cual

    with conexion() as cn:
        cur = cn.cursor()
        cur.execute(
            """
            INSERT INTO dbo.MedidasLlanta (Medida, Ancho, Perfil, Rin)
            VALUES (?, ?, ?, ?);
            SELECT SCOPE_IDENTITY();
            """,
            (medida, ancho, perfil, rin),
        )
        return int(cur.fetchone()[0])


def buscar_clientes(texto: str, limite: int = 8) -> list:
    return consultar(
        f"""
        SELECT TOP {int(limite)} ClienteID, Nombre, Telefono
        FROM   dbo.Clientes
        WHERE  Activo = 1 AND (Nombre LIKE ? OR Telefono LIKE ?)
        ORDER BY Nombre
        """,
        (f"%{texto}%", f"%{texto}%"),
    )


def automoviles_de_cliente(cliente_id: int) -> list:
    return consultar(
        """
        SELECT AutomovilID, Descripcion, Placas
        FROM   dbo.Automoviles
        WHERE  ClienteID = ? AND Activo = 1
        ORDER BY Descripcion
        """,
        (cliente_id,),
    )


# ==================================================================
# ÓRDENES
# ==================================================================
def guardar_orden(cabecera: dict, renglones: list) -> dict:
    """
    Guarda cliente, automóvil, orden y renglones en una sola transacción.

    cabecera  = {"cliente", "telefono", "automovil", "placas",
                 "fecha" (date), "usuario_id", "observaciones"}
    renglones = [{"medida_id", "cantidad", "pieza_id", "precio", "descripcion"}, ...]

    Devuelve {"OrdenID", "Folio", "Total"}.
    """
    if not cabecera.get("cliente"):
        raise ErrorBaseDatos("Captura el nombre del cliente.")
    if not renglones:
        raise ErrorBaseDatos("Agrega al menos una llanta a la orden.")

    try:
        with conexion(autocommit=False) as cn:
            cur = cn.cursor()

            # --- Cliente -------------------------------------------------
            cur.execute(
                """
                DECLARE @ClienteID INT;
                EXEC dbo.sp_Cliente_Guardar ?, ?, @ClienteID OUTPUT;
                SELECT @ClienteID;
                """,
                (cabecera["cliente"].strip(), cabecera.get("telefono")),
            )
            cliente_id = int(cur.fetchone()[0])
            cur.nextset()

            # --- Automóvil (opcional) ------------------------------------
            automovil_id = None
            if cabecera.get("automovil"):
                cur.execute(
                    """
                    DECLARE @AutomovilID INT;
                    EXEC dbo.sp_Automovil_Guardar ?, ?, ?, @AutomovilID OUTPUT;
                    SELECT @AutomovilID;
                    """,
                    (cliente_id, cabecera["automovil"].strip(), cabecera.get("placas")),
                )
                automovil_id = int(cur.fetchone()[0])
                cur.nextset()

            # --- Encabezado de la orden ----------------------------------
            cur.execute(
                """
                DECLARE @OrdenID INT, @Folio VARCHAR(20);
                EXEC dbo.sp_Orden_Crear ?, ?, ?, ?, ?, ?, @OrdenID OUTPUT, @Folio OUTPUT;
                SELECT @OrdenID, @Folio;
                """,
                (
                    cliente_id,
                    automovil_id,
                    cabecera.get("telefono"),
                    cabecera.get("fecha") or date.today(),
                    cabecera.get("usuario_id"),
                    cabecera.get("observaciones"),
                ),
            )
            fila = cur.fetchone()
            orden_id, folio = int(fila[0]), fila[1]
            cur.nextset()

            # --- Renglones -----------------------------------------------
            for r in renglones:
                cur.execute(
                    "{CALL dbo.sp_Orden_AgregarDetalle (?, ?, ?, ?, ?, ?)}",
                    (
                        orden_id,
                        r["medida_id"],
                        int(r["cantidad"]),
                        r.get("pieza_id"),
                        float(r.get("precio") or 0),
                        r.get("descripcion"),
                    ),
                )
                while cur.nextset():
                    pass

            cn.commit()

            total = consultar_uno(
                "SELECT Total FROM dbo.Ordenes WHERE OrdenID = ?", (orden_id,)
            )
            return {
                "OrdenID": orden_id,
                "Folio": folio,
                "Total": float(total["Total"]) if total else 0.0,
            }

    except pyodbc.Error as ex:
        texto = str(ex)
        if "]" in texto:
            texto = texto.split("]")[-1]
        raise ErrorBaseDatos(texto.strip(" ()'\"")) from ex


def listar_ordenes(desde: date = None, hasta: date = None, estatus: str = None) -> list:
    sql = "SELECT * FROM dbo.vw_Ordenes WHERE 1 = 1"
    params = []
    if desde:
        sql += " AND FechaOrden >= ?"
        params.append(desde)
    if hasta:
        sql += " AND FechaOrden <= ?"
        params.append(hasta)
    if estatus:
        sql += " AND Estatus = ?"
        params.append(estatus)
    sql += " ORDER BY OrdenID DESC"
    return consultar(sql, tuple(params))


def cambiar_estatus_orden(orden_id: int, estatus: str, usuario_id: int = None) -> None:
    """
    Cambia el estatus de la orden. Si se cancela, el procedimiento
    regresa las llantas al inventario y lo deja asentado en el kardex.
    """
    try:
        ejecutar("{CALL dbo.sp_Orden_CambiarEstatus (?, ?, ?)}",
                 (orden_id, estatus, usuario_id))
    except pyodbc.Error as ex:
        texto = str(ex)
        if "]" in texto:
            texto = texto.split("]")[-1]
        raise ErrorBaseDatos(texto.strip(" ()'\"")) from ex


def obtener_orden(orden_id: int) -> dict:
    """Devuelve {"cabecera": {...}, "detalle": [...]} para imprimir."""
    partes = ejecutar_sp_multiple("{CALL dbo.sp_Orden_Obtener (?)}", (orden_id,))

    if not partes or not partes[0]:
        raise ErrorBaseDatos("La orden ya no existe.")

    return {
        "cabecera": partes[0][0],
        "detalle": partes[1] if len(partes) > 1 else [],
    }


# ==================================================================
# INVENTARIO
# ==================================================================
def listar_piezas(tipo: str = None, filtro: str = "", solo_activas: bool = True) -> list:
    sql = "SELECT * FROM dbo.vw_Inventario WHERE 1 = 1"
    params = []
    if solo_activas:
        sql += " AND Activo = 1"
    if tipo:
        sql += " AND Tipo = ?"
        params.append(tipo)
    if filtro:
        sql += """ AND (Medida LIKE ? OR ISNULL(Marca, '') LIKE ?
                        OR ISNULL(Modelo, '') LIKE ? OR ISNULL(Codigo, '') LIKE ?)"""
        params.extend([f"%{filtro}%"] * 4)
    sql += " ORDER BY Medida, Marca"
    return consultar(sql, tuple(params))


def piezas_por_medida(medida_id: int, tipo: str = None) -> list:
    """Piezas con existencia para una medida: alimenta el select de la orden."""
    sql = """
        SELECT PiezaID, Codigo, Tipo, Marca, Modelo, Condicion, Cantidad, PrecioVenta
        FROM   dbo.vw_Inventario
        WHERE  Activo = 1 AND Cantidad > 0 AND MedidaID = ?
    """
    params = [medida_id]
    if tipo:
        sql += " AND Tipo = ?"
        params.append(tipo)
    sql += " ORDER BY Tipo, Marca"
    return consultar(sql, tuple(params))


def guardar_pieza(datos: dict) -> int:
    with conexion() as cn:
        cur = cn.cursor()
        cur.execute(
            """
            DECLARE @PiezaID INT;
            EXEC dbo.sp_Pieza_Guardar ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, @PiezaID OUTPUT;
            SELECT @PiezaID;
            """,
            (
                datos["tipo"],
                datos["medida_id"],
                datos.get("marca"),
                datos.get("modelo"),
                datos.get("condicion"),
                datos.get("dot"),
                int(datos.get("cantidad") or 0),
                int(datos.get("stock_minimo") or 0),
                float(datos.get("precio_costo") or 0),
                float(datos.get("precio_venta") or 0),
                datos.get("ubicacion"),
                datos.get("usuario_id"),
            ),
        )
        return int(cur.fetchone()[0])


def actualizar_pieza(pieza_id: int, datos: dict) -> None:
    ejecutar(
        "{CALL dbo.sp_Pieza_Actualizar (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)}",
        (
            pieza_id,
            datos["tipo"],
            datos["medida_id"],
            datos.get("marca"),
            datos.get("modelo"),
            datos.get("condicion"),
            datos.get("dot"),
            int(datos.get("cantidad") or 0),
            int(datos.get("stock_minimo") or 0),
            float(datos.get("precio_costo") or 0),
            float(datos.get("precio_venta") or 0),
            datos.get("ubicacion"),
            datos.get("usuario_id"),
        ),
    )


def desactivar_pieza(pieza_id: int) -> None:
    ejecutar("UPDATE dbo.Piezas SET Activo = 0 WHERE PiezaID = ?", (pieza_id,))


def resumen_inventario() -> dict:
    fila = consultar_uno(
        """
        SELECT SUM(CASE WHEN Tipo = 'NUEVA' THEN Cantidad ELSE 0 END) AS Nuevas,
               SUM(CASE WHEN Tipo = 'USADA' THEN Cantidad ELSE 0 END) AS Usadas,
               SUM(CASE WHEN BajoStock = 1 THEN 1 ELSE 0 END)         AS Alertas,
               ISNULL(SUM(Cantidad * PrecioVenta), 0)                 AS ValorVenta
        FROM   dbo.vw_Inventario
        WHERE  Activo = 1
        """
    ) or {}
    return {
        "Nuevas": int(fila.get("Nuevas") or 0),
        "Usadas": int(fila.get("Usadas") or 0),
        "Alertas": int(fila.get("Alertas") or 0),
        "ValorVenta": float(fila.get("ValorVenta") or 0),
    }
