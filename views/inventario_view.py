# -*- coding: utf-8 -*-
"""
views/inventario_view.py
Pantallas 4 y 5 del boceto: inventario dividido en Usadas / Nuevas,
con el formulario para agregar piezas con los datos de la llanta.
"""

import customtkinter as ctk

from config import C, F, CATEGORIAS_PIEZA
from database import ErrorBaseDatos
from widgets import (
    Aviso, Campo, CampoSelect, Metrica, Tarjeta, TituloSeccion,
    boton_principal, boton_secundario, crear_tabla, llenar_tabla,
)
import repositorio


class InventarioView(ctk.CTkFrame):

    def __init__(self, master, app):
        super().__init__(master, fg_color=C["asfalto"])
        self.app = app

        self.tipo_activo = "USADA"
        self.categoria_activa = None
        self.piezas = []

        self._construir()

    # ==============================================================
    def _construir(self):
        contenedor = ctk.CTkFrame(self, fg_color="transparent")
        contenedor.pack(fill="both", expand=True, padx=28, pady=18)

        # ---------- Encabezado ------------------------------------
        cabecera = ctk.CTkFrame(contenedor, fg_color="transparent")
        cabecera.pack(fill="x", pady=(0, 16))

        izq = ctk.CTkFrame(cabecera, fg_color="transparent")
        izq.pack(side="left")
        ctk.CTkLabel(izq, text="INVENTARIO", font=F["titulo"],
                     text_color=C["gis"]).pack(anchor="w")
        ctk.CTkLabel(izq, text="Lo que hay en el rack, contado por medida",
                     font=F["chico"], text_color=C["gis_tenue"]).pack(anchor="w")

        boton_secundario(cabecera, "Volver al tablero",
                         lambda: self.app.mostrar("dashboard"),
                         ancho=180, alto=40).pack(side="right")

        self.aviso = Aviso(contenedor)

        # ---------- Métricas ---------------------------------------
        metricas = ctk.CTkFrame(contenedor, fg_color="transparent")
        metricas.pack(fill="x", pady=(0, 16))
        for i in range(4):
            metricas.grid_columnconfigure(i, weight=1, uniform="m")

        self.m_usadas = Metrica(metricas, "Llantas usadas", "0", color=C["altavis"])
        self.m_nuevas = Metrica(metricas, "Llantas nuevas", "0")
        self.m_alertas = Metrica(metricas, "Bajo mínimo", "0", color=C["parche"])
        self.m_valor = Metrica(metricas, "Valor a precio de venta", "$0", color=C["verde"])

        for i, tarjeta in enumerate(
            (self.m_usadas, self.m_nuevas, self.m_alertas, self.m_valor)
        ):
            tarjeta.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 8, 0))

        # ---------- Panel de listado -------------------------------
        panel = Tarjeta(contenedor)
        panel.pack(fill="both", expand=True)

        barra = ctk.CTkFrame(panel, fg_color="transparent")
        barra.pack(fill="x", padx=18, pady=(18, 12))

        # Usadas / Nuevas (pantalla 4 del boceto)
        self.selector = ctk.CTkSegmentedButton(
            barra,
            values=["USADAS", "NUEVAS", "TODAS"],
            command=self._cambiar_tipo,
            font=(F["titulo"][0], 14),
            height=40,
            fg_color=C["hule_alto"],
            selected_color=C["altavis"],
            selected_hover_color=C["altavis_hover"],
            unselected_color=C["hule_alto"],
            unselected_hover_color=C["linea"],
            text_color=C["gis"],
            corner_radius=6,
        )
        self.selector.set("USADAS")
        self.selector.pack(side="left")

        # Autos / Motos (para separar llantas de moto en el inventario)
        self.selector_categoria = ctk.CTkSegmentedButton(
            barra,
            values=["TODAS", "AUTO", "MOTO"],
            command=self._cambiar_categoria,
            font=(F["titulo"][0], 14),
            height=40,
            fg_color=C["hule_alto"],
            selected_color=C["altavis"],
            selected_hover_color=C["altavis_hover"],
            unselected_color=C["hule_alto"],
            unselected_hover_color=C["linea"],
            text_color=C["gis"],
            corner_radius=6,
        )
        self.selector_categoria.set("TODAS")
        self.selector_categoria.pack(side="left", padx=(10, 0))

        self.campo_busqueda = ctk.CTkEntry(
            barra, width=260, height=40, placeholder_text="Buscar medida, marca o código",
            font=F["cuerpo"], fg_color=C["hule_alto"], border_color=C["linea"],
            border_width=1, text_color=C["gis"], corner_radius=6,
        )
        self.campo_busqueda.pack(side="left", padx=12)
        self.campo_busqueda.bind("<KeyRelease>", lambda _e: self.recargar())

        boton_principal(barra, "Agregar pieza", self.agregar_pieza,
                        ancho=170, alto=40).pack(side="right")
        boton_secundario(barra, "Editar", self.editar_pieza,
                         ancho=110, alto=40).pack(side="right", padx=(0, 10))
        boton_secundario(barra, "Dar de baja", self.dar_de_baja,
                         ancho=130, alto=40).pack(side="right", padx=(0, 10))

        cont, self.tabla = crear_tabla(
            panel,
            [("Codigo", "Código"), ("Tipo", "Tipo"), ("Categoria", "Vehículo"),
             ("Medida", "Medida"), ("Marca", "Marca"), ("Modelo", "Modelo"),
             ("Condicion", "Condición"), ("DOT", "DOT"), ("Cantidad", "Existencia"),
             ("StockMinimo", "Mín"), ("PrecioVenta", "Precio"), ("Ubicacion", "Ubicación")],
            anchos=[95, 70, 75, 105, 115, 115, 100, 65, 90, 55, 95, 95],
            altura=14,
        )
        cont.pack(fill="both", expand=True, padx=14, pady=(0, 8))
        self.tabla.bind("<Double-1>", lambda _e: self.editar_pieza())

        self.pie = ctk.CTkLabel(panel, text="", font=F["chico"], text_color=C["gis_tenue"])
        self.pie.pack(anchor="w", padx=18, pady=(0, 16))

    # ==============================================================
    def al_mostrar(self):
        self.recargar()

    def _cambiar_tipo(self, valor):
        self.tipo_activo = {"USADAS": "USADA", "NUEVAS": "NUEVA", "TODAS": None}[valor]
        self.recargar()

    def _cambiar_categoria(self, valor):
        self.categoria_activa = None if valor == "TODAS" else valor
        self.recargar()

    def recargar(self):
        filtro = self.campo_busqueda.get().strip()
        try:
            self.piezas = repositorio.listar_piezas(
                self.tipo_activo, filtro, categoria=self.categoria_activa
            )
            resumen = repositorio.resumen_inventario()
        except ErrorBaseDatos as ex:
            self.aviso.mostrar(str(ex), "error")
            return

        self.m_usadas.actualizar(resumen["Usadas"])
        self.m_nuevas.actualizar(resumen["Nuevas"])
        self.m_alertas.actualizar(resumen["Alertas"])
        self.m_valor.actualizar(f"${resumen['ValorVenta']:,.0f}")

        llenar_tabla(
            self.tabla, self.piezas,
            ["Codigo", "Tipo", "Categoria", "Medida", "Marca", "Modelo", "Condicion",
             "DOT", "Cantidad", "StockMinimo", "PrecioVenta", "Ubicacion"],
            formateadores={"PrecioVenta": lambda v: f"${float(v or 0):,.2f}"},
            tag_extra=lambda f: "alerta" if f.get("BajoStock") else None,
        )

        total = sum(p["Cantidad"] for p in self.piezas)
        self.pie.configure(
            text=f"{len(self.piezas)} registros · {total} llantas en existencia. "
                 f"Las líneas en naranja están en el mínimo o por debajo."
        )

    # --------------------------------------------------------------
    def _pieza_seleccionada(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            return None
        indice = self.tabla.index(seleccion[0])
        return self.piezas[indice] if 0 <= indice < len(self.piezas) else None

    # --------------------------------------------------------------
    def agregar_pieza(self):
        tipo = self.tipo_activo or "USADA"
        categoria = self.categoria_activa or "AUTO"
        DialogoPieza(self, self.app, tipo_inicial=tipo, categoria_inicial=categoria,
                    al_guardar=self._despues_de_guardar)

    def editar_pieza(self):
        pieza = self._pieza_seleccionada()
        if pieza is None:
            self.aviso.mostrar("Selecciona una pieza de la lista para editarla.", "info")
            return
        DialogoPieza(self, self.app, pieza=pieza, al_guardar=self._despues_de_guardar)

    def dar_de_baja(self):
        pieza = self._pieza_seleccionada()
        if pieza is None:
            self.aviso.mostrar("Selecciona la pieza que quieres dar de baja.", "info")
            return

        try:
            repositorio.desactivar_pieza(pieza["PiezaID"])
        except ErrorBaseDatos as ex:
            self.aviso.mostrar(str(ex), "error")
            return

        self.recargar()
        self.aviso.mostrar(f"{pieza['Codigo']} salió del inventario activo.", "ok")

    def _despues_de_guardar(self, mensaje):
        self.recargar()
        self.aviso.mostrar(mensaje, "ok")


# ==================================================================
# Pantalla 5: alta / edición de pieza
# ==================================================================
class DialogoPieza(ctk.CTkToplevel):
    """Formulario con los datos de la llanta: medida, marca, condición, etc."""

    def __init__(self, master, app, pieza=None, tipo_inicial="USADA",
                 categoria_inicial="AUTO", al_guardar=None):
        super().__init__(master)
        self.app = app
        self.pieza = pieza
        self.al_guardar = al_guardar
        self.medidas = []

        self.title("Editar pieza" if pieza else "Agregar pieza")
        self.configure(fg_color=C["asfalto"])
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self._construir(tipo_inicial, categoria_inicial)
        self._cargar_medidas()

        if pieza:
            self._precargar(pieza)

        self.after(120, self._centrar)

    # --------------------------------------------------------------
    def _construir(self, tipo_inicial, categoria_inicial="AUTO"):
        cuerpo = ctk.CTkFrame(self, fg_color="transparent")
        cuerpo.pack(padx=26, pady=24)

        TituloSeccion(
            cuerpo, "Datos de la llanta", fondo=C["asfalto"], ancho_huella=220
        ).pack(anchor="w", pady=(0, 18))

        rejilla = ctk.CTkFrame(cuerpo, fg_color="transparent")
        rejilla.pack()

        # Fila 1
        self.select_tipo = CampoSelect(rejilla, "Tipo", ["USADA", "NUEVA"], ancho=200)
        self.select_tipo.grid(row=0, column=0, sticky="w", padx=(0, 16), pady=(0, 14))
        self.select_tipo.set(tipo_inicial)

        self.select_categoria = CampoSelect(rejilla, "Vehículo", CATEGORIAS_PIEZA, ancho=200)
        self.select_categoria.grid(row=0, column=1, sticky="w", pady=(0, 14))
        self.select_categoria.set(categoria_inicial)

        # Fila 2
        self.select_medida = CampoSelect(rejilla, "Medida", [""], ancho=200)
        self.select_medida.grid(row=1, column=0, sticky="w", padx=(0, 16), pady=(0, 14))

        self.campo_marca = Campo(rejilla, "Marca", "Michelin, Firestone…", ancho=200)
        self.campo_marca.grid(row=1, column=1, sticky="w", pady=(0, 14))

        # Fila 3
        self.campo_modelo = Campo(rejilla, "Modelo", "Energy XM2", ancho=200)
        self.campo_modelo.grid(row=2, column=0, sticky="w", padx=(0, 16), pady=(0, 14))

        self.campo_condicion = Campo(rejilla, "Condición", "80% vida", ancho=200)
        self.campo_condicion.grid(row=2, column=1, sticky="w", pady=(0, 14))

        # Fila 4
        self.campo_dot = Campo(rejilla, "DOT", "Semana y año, ej. 2425", ancho=200)
        self.campo_dot.grid(row=3, column=0, sticky="w", padx=(0, 16), pady=(0, 14))

        self.campo_cantidad = Campo(rejilla, "Existencia", "0", ancho=200)
        self.campo_cantidad.grid(row=3, column=1, sticky="w", pady=(0, 14))
        self.campo_cantidad.set("1")

        # Fila 5
        self.campo_minimo = Campo(rejilla, "Mínimo antes de pedir", "0", ancho=200)
        self.campo_minimo.grid(row=4, column=0, sticky="w", padx=(0, 16), pady=(0, 14))
        self.campo_minimo.set("2")

        self.campo_costo = Campo(rejilla, "Precio de costo", "0.00", ancho=200)
        self.campo_costo.grid(row=4, column=1, sticky="w", pady=(0, 14))
        self.campo_costo.set("0")

        # Fila 6
        self.campo_venta = Campo(rejilla, "Precio de venta", "0.00", ancho=200)
        self.campo_venta.grid(row=5, column=0, sticky="w", padx=(0, 16), pady=(0, 14))
        self.campo_venta.set("0")

        self.campo_ubicacion = Campo(rejilla, "Ubicación en el rack", "A-01", ancho=200)
        self.campo_ubicacion.grid(row=5, column=1, sticky="w", pady=(0, 14))

        self.mensaje = ctk.CTkLabel(cuerpo, text="", font=F["chico"],
                                    text_color=C["rojo"], wraplength=420)
        self.mensaje.pack(anchor="w", pady=(10, 0))

        botones = ctk.CTkFrame(cuerpo, fg_color="transparent")
        botones.pack(fill="x", pady=(16, 0))
        boton_secundario(botones, "Cancelar", self.destroy, ancho=140).pack(side="left")
        boton_principal(botones, "Guardar pieza", self.guardar, ancho=200).pack(side="right")

    # --------------------------------------------------------------
    def _centrar(self):
        self.update_idletasks()
        ancho, alto = self.winfo_width(), self.winfo_height()
        x = self.master.winfo_rootx() + (self.master.winfo_width() - ancho) // 2
        y = self.master.winfo_rooty() + (self.master.winfo_height() - alto) // 3
        self.geometry(f"+{max(0, x)}+{max(0, y)}")

    def _cargar_medidas(self):
        try:
            self.medidas = repositorio.listar_medidas()
        except ErrorBaseDatos as ex:
            self.mensaje.configure(text=str(ex))
            return
        self.select_medida.cargar([m["Medida"] for m in self.medidas] or [""])

    def _precargar(self, pieza):
        self.select_tipo.set(pieza["Tipo"])
        self.select_categoria.set(pieza.get("Categoria") or "AUTO")
        self.select_medida.set(pieza["Medida"])
        self.campo_marca.set(pieza.get("Marca") or "")
        self.campo_modelo.set(pieza.get("Modelo") or "")
        self.campo_condicion.set(pieza.get("Condicion") or "")
        self.campo_dot.set(pieza.get("DOT") or "")
        self.campo_cantidad.set(pieza.get("Cantidad") or 0)
        self.campo_minimo.set(pieza.get("StockMinimo") or 0)
        self.campo_costo.set(f"{float(pieza.get('PrecioCosto') or 0):.2f}")
        self.campo_venta.set(f"{float(pieza.get('PrecioVenta') or 0):.2f}")
        self.campo_ubicacion.set(pieza.get("Ubicacion") or "")

    # --------------------------------------------------------------
    def _medida_id(self):
        texto = self.select_medida.get()
        for m in self.medidas:
            if m["Medida"] == texto:
                return m["MedidaID"]
        return None

    def _numero(self, campo, etiqueta, entero=False):
        texto = campo.get()
        campo.ocultar_error()
        if texto == "":
            return 0
        try:
            return int(float(texto)) if entero else float(texto)
        except ValueError:
            campo.marcar_error(f"{etiqueta} debe ser un número.")
            raise ValueError

    # --------------------------------------------------------------
    def guardar(self):
        self.mensaje.configure(text="")

        medida_id = self._medida_id()
        if not medida_id:
            self.mensaje.configure(text="Elige la medida de la llanta.")
            return

        try:
            cantidad = self._numero(self.campo_cantidad, "La existencia", entero=True)
            minimo = self._numero(self.campo_minimo, "El mínimo", entero=True)
            costo = self._numero(self.campo_costo, "El costo")
            venta = self._numero(self.campo_venta, "El precio de venta")
        except ValueError:
            return

        if cantidad < 0:
            self.campo_cantidad.marcar_error("No puede ser negativa.")
            return

        datos = {
            "tipo": self.select_tipo.get(),
            "categoria": self.select_categoria.get(),
            "medida_id": medida_id,
            "marca": self.campo_marca.get() or None,
            "modelo": self.campo_modelo.get() or None,
            "condicion": self.campo_condicion.get() or None,
            "dot": self.campo_dot.get() or None,
            "cantidad": cantidad,
            "stock_minimo": minimo,
            "precio_costo": costo,
            "precio_venta": venta,
            "ubicacion": self.campo_ubicacion.get() or None,
            "usuario_id": self.app.sesion.get("UsuarioID") if self.app.sesion else None,
        }

        try:
            if self.pieza:
                repositorio.actualizar_pieza(self.pieza["PiezaID"], datos)
                mensaje = f"{self.pieza['Codigo']} actualizada."
            else:
                repositorio.guardar_pieza(datos)
                mensaje = (f"{cantidad} llanta(s) {datos['tipo'].lower()}(s) "
                           f"{self.select_medida.get()} entraron al inventario.")
        except ErrorBaseDatos as ex:
            self.mensaje.configure(text=str(ex))
            return

        if self.al_guardar:
            self.al_guardar(mensaje)
        self.destroy()
