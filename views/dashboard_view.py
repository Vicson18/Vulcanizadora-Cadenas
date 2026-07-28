# -*- coding: utf-8 -*-
"""
views/dashboard_view.py
Pantalla 2 del boceto: producción diaria y semanal + accesos a
Crear orden e Inventario.
"""

from datetime import date
from tkinter import messagebox

import customtkinter as ctk

from config import C, F
from database import ErrorBaseDatos
from impresion import MENSAJE_SIN_REPORTLAB, REPORTLAB_DISPONIBLE, imprimir_orden
from widgets import (
    Dona, Leyenda, Metrica, Tarjeta, TituloSeccion,
    boton_principal, boton_secundario, crear_tabla, llenar_tabla,
)
import repositorio

DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def _fecha_larga(dia: date) -> str:
    """Fecha en español sin depender del locale instalado en la máquina."""
    return f"{DIAS[dia.weekday()]} {dia.day} de {MESES[dia.month - 1]} de {dia.year}"


class DashboardView(ctk.CTkFrame):

    def __init__(self, master, app):
        super().__init__(master, fg_color=C["asfalto"])
        self.app = app
        self.ordenes = []
        self._construir()

    # ==============================================================
    def _construir(self):
        contenedor = ctk.CTkScrollableFrame(
            self, fg_color="transparent", scrollbar_button_color=C["linea"],
            scrollbar_button_hover_color=C["gis_tenue"],
        )
        contenedor.pack(fill="both", expand=True, padx=28, pady=(18, 18))

        # ---------- Encabezado ------------------------------------
        cabecera = ctk.CTkFrame(contenedor, fg_color="transparent")
        cabecera.pack(fill="x", pady=(0, 18))

        izquierda = ctk.CTkFrame(cabecera, fg_color="transparent")
        izquierda.pack(side="left")
        ctk.CTkLabel(izquierda, text="PRODUCCIÓN", font=F["titulo"],
                     text_color=C["gis"]).pack(anchor="w")
        self.lbl_fecha = ctk.CTkLabel(izquierda, text="", font=F["chico"],
                                      text_color=C["gis_tenue"])
        self.lbl_fecha.pack(anchor="w")

        acciones = ctk.CTkFrame(cabecera, fg_color="transparent")
        acciones.pack(side="right")
        boton_secundario(acciones, "Actualizar", self.recargar, ancho=130, alto=40).pack(side="left", padx=(0, 10))
        boton_secundario(acciones, "Inventario",
                         lambda: self.app.mostrar("inventario"),
                         ancho=150, alto=40).pack(side="left", padx=(0, 10))
        boton_principal(acciones, "Crear orden",
                        lambda: self.app.mostrar("ordenes"),
                        ancho=170, alto=40).pack(side="left")

        # ---------- Métricas del día -------------------------------
        metricas = ctk.CTkFrame(contenedor, fg_color="transparent")
        metricas.pack(fill="x", pady=(0, 18))
        for i in range(4):
            metricas.grid_columnconfigure(i, weight=1, uniform="m")

        self.m_ordenes = Metrica(metricas, "Órdenes de hoy", "0")
        self.m_piezas = Metrica(metricas, "Llantas atendidas", "0", color=C["altavis"])
        self.m_terminadas = Metrica(metricas, "Terminadas", "0", color=C["verde"])
        self.m_ingresos = Metrica(metricas, "Ingreso del día", "$0", color=C["gis"])

        for i, tarjeta in enumerate(
            (self.m_ordenes, self.m_piezas, self.m_terminadas, self.m_ingresos)
        ):
            tarjeta.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 8, 0))

        # ---------- Donas: diario y semanal ------------------------
        graficas = ctk.CTkFrame(contenedor, fg_color="transparent")
        graficas.pack(fill="x", pady=(0, 18))
        graficas.grid_columnconfigure(0, weight=1, uniform="g")
        graficas.grid_columnconfigure(1, weight=1, uniform="g")

        panel_d, self.dona_diario, self.leyenda_diario, self.pie_diario = self._panel_dona(
            graficas, "Diario", "Llantas por medida, hoy"
        )
        panel_d.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        panel_s, self.dona_semanal, self.leyenda_semanal, self.pie_semanal = self._panel_dona(
            graficas, "Semanal", "Llantas por día, últimos 7 días"
        )
        panel_s.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        # ---------- Listas -----------------------------------------
        listas = ctk.CTkFrame(contenedor, fg_color="transparent")
        listas.pack(fill="both", expand=True)
        listas.grid_columnconfigure(0, weight=3, uniform="l")
        listas.grid_columnconfigure(1, weight=2, uniform="l")

        # Últimas órdenes
        panel_ordenes = Tarjeta(listas)
        panel_ordenes.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        TituloSeccion(panel_ordenes, "Últimas órdenes").pack(anchor="w", padx=18, pady=(16, 10))

        cont, self.tabla_ordenes = crear_tabla(
            panel_ordenes,
            [("Folio", "Folio"), ("FechaOrden", "Fecha"), ("Cliente", "Cliente"),
             ("Automovil", "Automóvil"), ("Piezas", "Pzas"), ("Total", "Total"),
             ("Estatus", "Estatus")],
            anchos=[120, 90, 170, 170, 55, 90, 100],
            altura=9,
        )
        cont.pack(fill="both", expand=True, padx=12, pady=(0, 10))
        self.tabla_ordenes.bind("<Double-1>", lambda _e: self.imprimir_orden())

        acciones_orden = ctk.CTkFrame(panel_ordenes, fg_color="transparent")
        acciones_orden.pack(fill="x", padx=12, pady=(0, 6))

        boton_principal(acciones_orden, "Imprimir orden", self.imprimir_orden,
                        ancho=150, alto=36).pack(side="left", padx=(0, 8))
        boton_secundario(acciones_orden, "En proceso",
                         lambda: self.marcar("EN PROCESO"),
                         ancho=125, alto=36).pack(side="left", padx=(0, 8))
        boton_secundario(acciones_orden, "Terminada",
                         lambda: self.marcar("TERMINADA"),
                         ancho=125, alto=36).pack(side="left", padx=(0, 8))
        boton_secundario(acciones_orden, "Cancelar",
                         lambda: self.marcar("CANCELADA"),
                         ancho=115, alto=36).pack(side="left")

        ctk.CTkLabel(
            panel_ordenes,
            text="Selecciona una orden de la lista. Doble clic la imprime. "
                 "Al cancelar, las llantas regresan al inventario.",
            font=F["chico"], text_color=C["gis_tenue"], anchor="w", justify="left",
        ).pack(fill="x", padx=14, pady=(0, 14))

        # Alertas de inventario
        panel_alertas = Tarjeta(listas)
        panel_alertas.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        TituloSeccion(panel_alertas, "Se está acabando").pack(anchor="w", padx=18, pady=(16, 10))

        cont2, self.tabla_alertas = crear_tabla(
            panel_alertas,
            [("Medida", "Medida"), ("Tipo", "Tipo"), ("Marca", "Marca"),
             ("Cantidad", "Hay"), ("StockMinimo", "Mín")],
            anchos=[110, 80, 120, 55, 55],
            altura=9,
        )
        cont2.pack(fill="both", expand=True, padx=12, pady=(0, 14))

    # --------------------------------------------------------------
    def _panel_dona(self, master, titulo, subtitulo):
        tarjeta = Tarjeta(master)

        TituloSeccion(tarjeta, titulo).pack(anchor="w", padx=18, pady=(16, 2))
        ctk.CTkLabel(tarjeta, text=subtitulo, font=F["chico"],
                     text_color=C["gis_tenue"]).pack(anchor="w", padx=18, pady=(0, 8))

        cuerpo = ctk.CTkFrame(tarjeta, fg_color="transparent")
        cuerpo.pack(fill="x", padx=18, pady=(0, 10))

        dona = Dona(cuerpo, tamano=2.3)
        dona.pack(side="left")

        leyenda = Leyenda(cuerpo)
        leyenda.pack(side="left", fill="x", expand=True, padx=(16, 0))

        pie = ctk.CTkLabel(tarjeta, text="", font=F["chico"], text_color=C["gis_tenue"])
        pie.pack(anchor="w", padx=18, pady=(0, 16))

        return tarjeta, dona, leyenda, pie

    # ==============================================================
    def al_mostrar(self):
        self.recargar()

    def recargar(self):
        hoy = date.today()
        self.lbl_fecha.configure(text=_fecha_larga(hoy))

        try:
            diario = repositorio.dashboard_diario(hoy)
            semanal = repositorio.dashboard_semanal(hoy)
            ordenes = repositorio.ordenes_recientes(10)
            alertas = repositorio.piezas_bajo_stock()
        except ErrorBaseDatos as ex:
            self.app.avisar(str(ex), "error")
            return

        self.ordenes = ordenes

        # --- Métricas ------------------------------------------------
        t = diario["totales"]
        self.m_ordenes.actualizar(t["Ordenes"])
        self.m_piezas.actualizar(t["Piezas"])
        self.m_terminadas.actualizar(t["Terminadas"])
        self.m_ingresos.actualizar(f"${t['Ingresos']:,.0f}")

        # --- Dona diaria ---------------------------------------------
        datos_d = [(f["Etiqueta"], f["Valor"]) for f in diario["desglose"]]
        self.dona_diario.dibujar(datos_d, centro=str(t["Piezas"]), subcentro="llantas")
        self.leyenda_diario.dibujar(datos_d)
        self.pie_diario.configure(
            text=f"{t['Ordenes']} órdenes · ${t['Ingresos']:,.2f}"
        )

        # --- Dona semanal --------------------------------------------
        ts = semanal["totales"]
        datos_s = [(f["Etiqueta"], f["Valor"]) for f in semanal["desglose"]]
        self.dona_semanal.dibujar(datos_s, centro=str(ts["Piezas"]), subcentro="llantas")
        self.leyenda_semanal.dibujar(datos_s)
        promedio = ts["Piezas"] / 7 if ts["Piezas"] else 0
        self.pie_semanal.configure(
            text=f"{ts['Ordenes']} órdenes · ${ts['Ingresos']:,.2f} · "
                 f"promedio {promedio:.1f} llantas por día"
        )

        # --- Tablas ---------------------------------------------------
        llenar_tabla(
            self.tabla_ordenes, ordenes,
            ["Folio", "FechaOrden", "Cliente", "Automovil", "Piezas", "Total", "Estatus"],
            formateadores={
                "FechaOrden": lambda v: v.strftime("%d/%m/%y") if v else "",
                "Total": lambda v: f"${float(v or 0):,.2f}",
            },
        )

        llenar_tabla(
            self.tabla_alertas, alertas,
            ["Medida", "Tipo", "Marca", "Cantidad", "StockMinimo"],
            tag_extra=lambda f: "alerta",
        )

    # ==============================================================
    # Acciones sobre la orden seleccionada
    # ==============================================================
    def _orden_seleccionada(self):
        seleccion = self.tabla_ordenes.selection()
        if not seleccion:
            self.app.avisar("Selecciona primero una orden de la lista.", "info")
            return None
        indice = self.tabla_ordenes.index(seleccion[0])
        return self.ordenes[indice] if 0 <= indice < len(self.ordenes) else None

    def imprimir_orden(self):
        orden = self._orden_seleccionada()
        if orden is None:
            return

        if not REPORTLAB_DISPONIBLE:
            self.app.avisar(MENSAJE_SIN_REPORTLAB, "error")
            return

        try:
            datos = repositorio.obtener_orden(orden["OrdenID"])
            ruta = imprimir_orden(datos)
        except ErrorBaseDatos as ex:
            self.app.avisar(str(ex), "error")
            return
        except (OSError, RuntimeError) as ex:
            self.app.avisar(f"No se pudo generar el PDF: {ex}", "error")
            return

        self.app.avisar(f"Orden {orden['Folio']} lista para imprimir: {ruta}", "ok")

    def marcar(self, estatus: str):
        orden = self._orden_seleccionada()
        if orden is None:
            return

        if estatus == "CANCELADA":
            confirmar = messagebox.askyesno(
                "Cancelar orden",
                f"Vas a cancelar la orden {orden['Folio']} de {orden['Cliente']}.\n\n"
                "Las llantas que hayan salido del inventario regresan al rack "
                "y la orden ya no se podrá reabrir.\n\n¿Continúas?",
                icon="warning",
            )
            if not confirmar:
                return

        try:
            repositorio.cambiar_estatus_orden(
                orden["OrdenID"], estatus,
                self.app.sesion.get("UsuarioID") if self.app.sesion else None,
            )
        except ErrorBaseDatos as ex:
            self.app.avisar(str(ex), "error")
            return

        self.recargar()
        self.app.avisar(f"Orden {orden['Folio']}: {estatus.lower()}.", "ok")
