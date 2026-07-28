# -*- coding: utf-8 -*-
"""
views/ordenes_view.py
Pantalla 3 del boceto: Cliente, Automóvil, Teléfono, fecha (día/mes/año),
Cantidad, Medida de llanta y guardar.
"""

import calendar
from datetime import date

import customtkinter as ctk

from config import C, F
from database import ErrorBaseDatos
from impresion import MENSAJE_SIN_REPORTLAB, REPORTLAB_DISPONIBLE, imprimir_orden
from widgets import (
    Aviso, Campo, CampoSelect, Contador, Tarjeta, TituloSeccion,
    boton_principal, boton_secundario, crear_tabla, llenar_tabla,
)
import repositorio

MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
         "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

SIN_INVENTARIO = "Sin descontar inventario"


class OrdenesView(ctk.CTkFrame):

    def __init__(self, master, app):
        super().__init__(master, fg_color=C["asfalto"])
        self.app = app

        self.medidas = []            # [{MedidaID, Medida}, ...]
        self.piezas_medida = []      # piezas disponibles de la medida elegida
        self.renglones = []          # renglones capturados de la orden
        self.cliente_sugerido = None
        self.ultima_orden = None     # para el botón de impresión

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
        ctk.CTkLabel(izq, text="CREAR ORDEN", font=F["titulo"],
                     text_color=C["gis"]).pack(anchor="w")
        ctk.CTkLabel(izq, text="Una orden por vehículo que entra al taller",
                     font=F["chico"], text_color=C["gis_tenue"]).pack(anchor="w")

        boton_secundario(cabecera, "Volver al tablero",
                         lambda: self.app.mostrar("dashboard"),
                         ancho=180, alto=40).pack(side="right")

        self.aviso = Aviso(contenedor)

        # ---------- Cuerpo: formulario | resumen -------------------
        cuerpo = ctk.CTkFrame(contenedor, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True)
        cuerpo.grid_columnconfigure(0, weight=3, uniform="c")
        cuerpo.grid_columnconfigure(1, weight=2, uniform="c")
        cuerpo.grid_rowconfigure(0, weight=1)

        self._formulario(cuerpo)
        self._resumen(cuerpo)

    # --------------------------------------------------------------
    def _formulario(self, master):
        tarjeta = Tarjeta(master)
        tarjeta.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        cuerpo = ctk.CTkScrollableFrame(
            tarjeta, fg_color="transparent", scrollbar_button_color=C["linea"],
            scrollbar_button_hover_color=C["gis_tenue"],
        )
        cuerpo.pack(fill="both", expand=True, padx=18, pady=18)

        # --- Datos del cliente -------------------------------------
        TituloSeccion(cuerpo, "Quién y qué carro").pack(anchor="w", pady=(0, 14))

        self.campo_cliente = Campo(cuerpo, "Cliente", "Nombre completo")
        self.campo_cliente.pack(fill="x", pady=(0, 4))
        self.campo_cliente.entrada.bind("<KeyRelease>", self._buscar_cliente)

        self.sugerencias = ctk.CTkFrame(cuerpo, fg_color="transparent")

        self.campo_telefono = Campo(cuerpo, "Núm. telefónico", "81 0000 0000")
        self.campo_telefono.pack(fill="x", pady=(12, 0))

        self.campo_automovil = Campo(cuerpo, "Automóvil", "Marca, modelo y año")
        self.campo_automovil.pack(fill="x", pady=(12, 0))

        self.campo_placas = Campo(cuerpo, "Placas", "Opcional")
        self.campo_placas.pack(fill="x", pady=(12, 0))

        # --- Fecha --------------------------------------------------
        TituloSeccion(cuerpo, "Fecha de la orden").pack(anchor="w", pady=(22, 14))

        fila_fecha = ctk.CTkFrame(cuerpo, fg_color="transparent")
        fila_fecha.pack(anchor="w")

        hoy = date.today()
        self.select_dia = CampoSelect(fila_fecha, "Día",
                                      [str(d) for d in range(1, 32)], ancho=80)
        self.select_dia.pack(side="left", padx=(0, 10))
        self.select_dia.set(str(hoy.day))

        self.select_mes = CampoSelect(fila_fecha, "Mes", MESES, ancho=90,
                                      comando=lambda _v: self._ajustar_dias())
        self.select_mes.pack(side="left", padx=(0, 10))
        self.select_mes.set(MESES[hoy.month - 1])

        anios = [str(a) for a in range(hoy.year - 1, hoy.year + 2)]
        self.select_anio = CampoSelect(fila_fecha, "Año", anios, ancho=100,
                                       comando=lambda _v: self._ajustar_dias())
        self.select_anio.pack(side="left")
        self.select_anio.set(str(hoy.year))

        # --- Llantas ------------------------------------------------
        TituloSeccion(cuerpo, "Llantas de la orden").pack(anchor="w", pady=(22, 14))

        self.select_medida = CampoSelect(cuerpo, "Medida de llanta", [""],
                                         ancho=260, comando=self._al_cambiar_medida)
        self.select_medida.pack(fill="x")

        ctk.CTkButton(
            cuerpo, text="+ Registrar una medida que no está en la lista",
            command=self._nueva_medida, font=F["chico"], height=24,
            fg_color="transparent", hover_color=C["hule_alto"],
            text_color=C["altavis"], anchor="w",
        ).pack(anchor="w", pady=(4, 12))

        self.select_pieza = CampoSelect(cuerpo, "Pieza del inventario",
                                        [SIN_INVENTARIO], ancho=260,
                                        comando=self._al_cambiar_pieza)
        self.select_pieza.pack(fill="x", pady=(0, 12))

        fila_cantidad = ctk.CTkFrame(cuerpo, fg_color="transparent")
        fila_cantidad.pack(anchor="w", fill="x")

        self.contador = Contador(fila_cantidad, "Cantidad", valor=1)
        self.contador.pack(side="left", padx=(0, 18))

        self.campo_precio = Campo(fila_cantidad, "Precio unitario", "0.00", ancho=140)
        self.campo_precio.pack(side="left")

        self.campo_concepto = Campo(cuerpo, "Concepto",
                                    "Ej. Reparación de ponchadura, balanceo, montaje")
        self.campo_concepto.pack(fill="x", pady=(12, 14))

        boton_principal(cuerpo, "Agregar a la orden", self.agregar_renglon,
                        ancho=260).pack(anchor="w")

        # --- Observaciones ------------------------------------------
        TituloSeccion(cuerpo, "Notas").pack(anchor="w", pady=(22, 14))
        self.texto_notas = ctk.CTkTextbox(
            cuerpo, height=70, font=F["cuerpo"], fg_color=C["hule_alto"],
            border_color=C["linea"], border_width=1, text_color=C["gis"],
            corner_radius=6,
        )
        self.texto_notas.pack(fill="x")

    # --------------------------------------------------------------
    def _resumen(self, master):
        tarjeta = Tarjeta(master)
        tarjeta.grid(row=0, column=1, sticky="nsew")

        # Barra inferior anclada al fondo de la tarjeta: así "Guardar orden"
        # siempre queda visible, sin importar cuántos renglones tenga la tabla.
        barra_inferior = ctk.CTkFrame(tarjeta, fg_color="transparent")
        barra_inferior.pack(side="bottom", fill="x")

        acciones = ctk.CTkFrame(barra_inferior, fg_color="transparent")
        acciones.pack(fill="x", padx=18, pady=(10, 0))
        boton_secundario(acciones, "Quitar renglón", self.quitar_renglon,
                         ancho=150, alto=36).pack(side="left")

        # --- Total ---------------------------------------------------
        pie = ctk.CTkFrame(barra_inferior, fg_color=C["hule_alto"], corner_radius=8)
        pie.pack(fill="x", padx=14, pady=14)

        fila = ctk.CTkFrame(pie, fg_color="transparent")
        fila.pack(fill="x", padx=16, pady=14)

        ctk.CTkLabel(fila, text="TOTAL", font=F["etiqueta"],
                     text_color=C["gis_tenue"]).pack(side="left")
        self.lbl_total = ctk.CTkLabel(fila, text="$0.00", font=F["metrica"],
                                      text_color=C["altavis"])
        self.lbl_total.pack(side="right")

        botones = ctk.CTkFrame(barra_inferior, fg_color="transparent")
        botones.pack(fill="x", padx=14, pady=(0, 10))
        boton_secundario(botones, "Limpiar", self.limpiar_todo,
                         ancho=110, alto=46).pack(side="left")
        boton_principal(botones, "Guardar orden", self.guardar,
                        ancho=200, alto=46).pack(side="right")

        # Aparece apenas se guarda una orden
        self.boton_imprimir = boton_secundario(
            barra_inferior, "Imprimir la orden guardada", self.imprimir_ultima, alto=40
        )

        TituloSeccion(tarjeta, "Renglones").pack(anchor="w", padx=18, pady=(18, 12))

        cont, self.tabla = crear_tabla(
            tarjeta,
            [("medida", "Medida"), ("concepto", "Concepto"),
             ("cantidad", "Cant"), ("precio", "P. unit"), ("importe", "Importe")],
            anchos=[100, 150, 55, 80, 90],
            altura=12,
        )
        cont.pack(fill="both", expand=True, padx=14)

    # ==============================================================
    # Ciclo de vida
    # ==============================================================
    def al_mostrar(self):
        self.cargar_medidas()
        self.campo_cliente.focus()

    def cargar_medidas(self):
        try:
            self.medidas = repositorio.listar_medidas()
        except ErrorBaseDatos as ex:
            self.aviso.mostrar(str(ex), "error")
            return

        valores = [m["Medida"] for m in self.medidas] or [""]
        actual = self.select_medida.get()
        self.select_medida.cargar(valores, seleccionar=actual)
        self._al_cambiar_medida(self.select_medida.get())

    # ==============================================================
    # Cliente
    # ==============================================================
    def _buscar_cliente(self, evento=None):
        if evento is not None and evento.keysym in ("Up", "Down", "Return", "Tab"):
            return

        texto = self.campo_cliente.get()
        for hijo in self.sugerencias.winfo_children():
            hijo.destroy()

        if len(texto) < 2:
            self.sugerencias.pack_forget()
            return

        try:
            encontrados = repositorio.buscar_clientes(texto, 5)
        except ErrorBaseDatos:
            return

        if not encontrados:
            self.sugerencias.pack_forget()
            return

        self.sugerencias.pack(fill="x", pady=(4, 0), after=self.campo_cliente)
        for cliente in encontrados:
            etiqueta = cliente["Nombre"]
            if cliente.get("Telefono"):
                etiqueta += f"  ·  {cliente['Telefono']}"
            ctk.CTkButton(
                self.sugerencias, text=etiqueta, font=F["chico"], height=28,
                anchor="w", fg_color=C["hule_alto"], hover_color=C["linea"],
                text_color=C["gis"], corner_radius=4,
                command=lambda c=cliente: self._usar_cliente(c),
            ).pack(fill="x", pady=1)

    def _usar_cliente(self, cliente):
        self.cliente_sugerido = cliente
        self.campo_cliente.set(cliente["Nombre"])
        if cliente.get("Telefono"):
            self.campo_telefono.set(cliente["Telefono"])
        self.sugerencias.pack_forget()

        try:
            autos = repositorio.automoviles_de_cliente(cliente["ClienteID"])
        except ErrorBaseDatos:
            return
        if autos:
            self.campo_automovil.set(autos[0]["Descripcion"])
            if autos[0].get("Placas"):
                self.campo_placas.set(autos[0]["Placas"])

    # ==============================================================
    # Fecha
    # ==============================================================
    def _ajustar_dias(self):
        """Evita capturar un 31 de febrero."""
        try:
            anio = int(self.select_anio.get())
            mes = MESES.index(self.select_mes.get()) + 1
        except ValueError:
            return

        ultimo = calendar.monthrange(anio, mes)[1]
        actual = self.select_dia.get()
        self.select_dia.cargar(
            [str(d) for d in range(1, ultimo + 1)],
            seleccionar=actual if actual.isdigit() and int(actual) <= ultimo else "1",
        )

    def _fecha_seleccionada(self) -> date:
        return date(
            int(self.select_anio.get()),
            MESES.index(self.select_mes.get()) + 1,
            int(self.select_dia.get()),
        )

    # ==============================================================
    # Medidas y piezas
    # ==============================================================
    def _medida_id(self, texto):
        for m in self.medidas:
            if m["Medida"] == texto:
                return m["MedidaID"]
        return None

    def _al_cambiar_medida(self, valor=None):
        medida_id = self._medida_id(self.select_medida.get())
        self.piezas_medida = []

        if medida_id:
            try:
                self.piezas_medida = repositorio.piezas_por_medida(medida_id)
            except ErrorBaseDatos as ex:
                self.aviso.mostrar(str(ex), "error")

        opciones = [SIN_INVENTARIO] + [
            f"{p['Tipo']} · {p['Marca'] or 's/marca'} · hay {p['Cantidad']}"
            for p in self.piezas_medida
        ]
        self.select_pieza.cargar(opciones)

    def _al_cambiar_pieza(self, valor=None):
        pieza = self._pieza_seleccionada()
        if pieza:
            self.campo_precio.set(f"{float(pieza['PrecioVenta']):.2f}")
            self.contador.maximo = int(pieza["Cantidad"])
            if self.contador.get() > pieza["Cantidad"]:
                self.contador.set(pieza["Cantidad"])
        else:
            self.contador.maximo = 99

    def _pieza_seleccionada(self):
        opciones = self.select_pieza.menu.cget("values")
        seleccion = self.select_pieza.get()
        if seleccion == SIN_INVENTARIO or seleccion not in opciones:
            return None
        indice = list(opciones).index(seleccion) - 1
        if 0 <= indice < len(self.piezas_medida):
            return self.piezas_medida[indice]
        return None

    def _nueva_medida(self):
        dialogo = ctk.CTkInputDialog(
            title="Nueva medida",
            text="Escribe la medida tal como viene en el costado de la llanta.\n"
                 "Ejemplo: 205/55R16",
            fg_color=C["hule"],
            button_fg_color=C["altavis"],
            button_hover_color=C["altavis_hover"],
            button_text_color=C["asfalto"],
            entry_fg_color=C["hule_alto"],
            entry_border_color=C["linea"],
            entry_text_color=C["gis"],
        )
        texto = dialogo.get_input()

        if not texto or not texto.strip():
            return

        try:
            repositorio.agregar_medida(texto)
        except ErrorBaseDatos as ex:
            self.aviso.mostrar(str(ex), "error")
            return

        self.cargar_medidas()
        self.select_medida.set(texto.strip().upper())
        self._al_cambiar_medida()
        self.aviso.mostrar(f"Medida {texto.strip().upper()} registrada.", "ok")

    # ==============================================================
    # Renglones
    # ==============================================================
    def agregar_renglon(self):
        medida = self.select_medida.get()
        medida_id = self._medida_id(medida)

        if not medida_id:
            self.aviso.mostrar("Elige la medida de llanta.", "error")
            return

        cantidad = self.contador.get()
        pieza = self._pieza_seleccionada()

        if pieza and cantidad > pieza["Cantidad"]:
            self.aviso.mostrar(
                f"Solo hay {pieza['Cantidad']} piezas de esa medida en inventario.",
                "error",
            )
            return

        try:
            precio = float(self.campo_precio.get() or 0)
        except ValueError:
            self.campo_precio.marcar_error("Usa solo números, por ejemplo 850.00")
            return
        self.campo_precio.ocultar_error()

        concepto = self.campo_concepto.get() or (
            f"{pieza['Tipo'].capitalize()} {pieza['Marca'] or ''}".strip()
            if pieza else "Servicio de llanta"
        )

        self.renglones.append({
            "medida_id": medida_id,
            "medida": medida,
            "cantidad": cantidad,
            "pieza_id": pieza["PiezaID"] if pieza else None,
            "precio": precio,
            "descripcion": concepto,
        })

        self._refrescar_renglones()
        self.contador.set(1)
        self.campo_concepto.limpiar()
        self.aviso.mostrar(f"{cantidad} × {medida} agregado.", "ok", segundos=3)

    def quitar_renglon(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            self.aviso.mostrar("Selecciona el renglón que quieres quitar.", "info")
            return

        indice = self.tabla.index(seleccion[0])
        if 0 <= indice < len(self.renglones):
            self.renglones.pop(indice)
            self._refrescar_renglones()

    def _refrescar_renglones(self):
        filas = [{
            "medida": r["medida"],
            "concepto": r["descripcion"],
            "cantidad": r["cantidad"],
            "precio": f"${r['precio']:,.2f}",
            "importe": f"${r['cantidad'] * r['precio']:,.2f}",
        } for r in self.renglones]

        llenar_tabla(self.tabla, filas,
                     ["medida", "concepto", "cantidad", "precio", "importe"])

        total = sum(r["cantidad"] * r["precio"] for r in self.renglones)
        self.lbl_total.configure(text=f"${total:,.2f}")

    # ==============================================================
    # Guardar
    # ==============================================================
    def guardar(self):
        self.campo_cliente.ocultar_error()

        if not self.campo_cliente.get():
            self.campo_cliente.marcar_error("Falta el nombre del cliente.")
            self.campo_cliente.focus()
            return

        if not self.renglones:
            self.aviso.mostrar("Agrega al menos una llanta antes de guardar.", "error")
            return

        cabecera = {
            "cliente": self.campo_cliente.get(),
            "telefono": self.campo_telefono.get() or None,
            "automovil": self.campo_automovil.get() or None,
            "placas": self.campo_placas.get() or None,
            "fecha": self._fecha_seleccionada(),
            "usuario_id": self.app.sesion.get("UsuarioID") if self.app.sesion else None,
            "observaciones": self.texto_notas.get("1.0", "end").strip() or None,
        }

        try:
            resultado = repositorio.guardar_orden(cabecera, self.renglones)
        except ErrorBaseDatos as ex:
            self.aviso.mostrar(str(ex), "error")
            return

        self.ultima_orden = resultado
        self.boton_imprimir.configure(
            text=f"IMPRIMIR LA ORDEN {resultado['Folio']}"
        )
        self.boton_imprimir.pack(fill="x", padx=14, pady=(0, 18))

        self.aviso.mostrar(
            f"Orden {resultado['Folio']} guardada por ${resultado['Total']:,.2f}.",
            "ok", segundos=8,
        )
        self.limpiar_todo(conservar_aviso=True)

    def imprimir_ultima(self):
        if not self.ultima_orden:
            return

        if not REPORTLAB_DISPONIBLE:
            self.aviso.mostrar(MENSAJE_SIN_REPORTLAB, "error", segundos=10)
            return

        try:
            datos = repositorio.obtener_orden(self.ultima_orden["OrdenID"])
            ruta = imprimir_orden(datos)
        except ErrorBaseDatos as ex:
            self.aviso.mostrar(str(ex), "error")
            return
        except (OSError, RuntimeError) as ex:
            self.aviso.mostrar(f"No se pudo generar el PDF: {ex}", "error")
            return

        self.aviso.mostrar(f"PDF generado en {ruta}", "ok", segundos=10)

    def limpiar_todo(self, conservar_aviso=False):
        for campo in (self.campo_cliente, self.campo_telefono, self.campo_automovil,
                      self.campo_placas, self.campo_precio, self.campo_concepto):
            campo.limpiar()

        self.texto_notas.delete("1.0", "end")
        self.renglones.clear()
        self.cliente_sugerido = None
        self.contador.set(1)
        self.sugerencias.pack_forget()
        self._refrescar_renglones()
        self.cargar_medidas()

        if not conservar_aviso:
            self.aviso.ocultar()

        self.campo_cliente.focus()
