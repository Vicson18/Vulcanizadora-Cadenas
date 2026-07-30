# -*- coding: utf-8 -*-
"""
widgets.py
Componentes de interfaz reutilizables por todas las pantallas.
"""

import math
import tkinter as tk
from tkinter import ttk

import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from config import C, F, SERIE_COLORES


# ==================================================================
# Elemento firma: banda de dibujo de piso (huella de llanta)
# ==================================================================
class Huella(tk.Canvas):
    """
    Separador con la forma de una huella de llanta.
    Se usa para dividir secciones: es el detalle que identifica la app.
    """

    def __init__(self, master, ancho=240, alto=10, color=None, bloques=14, **kw):
        color = color or C["altavis"]
        super().__init__(
            master, width=ancho, height=alto, bg=kw.pop("fondo", C["hule"]),
            highlightthickness=0, bd=0, **kw
        )
        paso = ancho / bloques
        for i in range(bloques):
            x = i * paso
            self.create_polygon(
                x + 2, alto, x + 5, 0, x + paso * 0.6, 0, x + paso * 0.6 - 3, alto,
                fill=color if i % 2 == 0 else C["linea"], outline="",
            )


# ==================================================================
# Contenedores
# ==================================================================
class Tarjeta(ctk.CTkFrame):
    """Panel con fondo de hule y borde tenue."""

    def __init__(self, master, **kw):
        kw.setdefault("fg_color", C["hule"])
        kw.setdefault("border_color", C["linea"])
        kw.setdefault("border_width", 1)
        kw.setdefault("corner_radius", 10)
        super().__init__(master, **kw)


class TituloSeccion(ctk.CTkFrame):
    """Título de sección con la huella debajo."""

    def __init__(self, master, texto, fondo=None, ancho_huella=180, **kw):
        fondo = fondo or C["hule"]
        super().__init__(master, fg_color="transparent", **kw)
        ctk.CTkLabel(
            self, text=texto.upper(), font=F["seccion"], text_color=C["gis"], anchor="w"
        ).pack(anchor="w")
        Huella(self, ancho=ancho_huella, alto=8, fondo=fondo).pack(anchor="w", pady=(3, 0))


# ==================================================================
# Campos de captura
# ==================================================================
class Campo(ctk.CTkFrame):
    """Etiqueta + entrada, con mensaje de error debajo."""

    def __init__(self, master, etiqueta, placeholder="", ancho=260,
                 password=False, **kw):
        super().__init__(master, fg_color="transparent", **kw)

        ctk.CTkLabel(
            self, text=etiqueta.upper(), font=F["etiqueta"],
            text_color=C["gis_tenue"], anchor="w",
        ).pack(anchor="w", pady=(0, 4))

        self.entrada = ctk.CTkEntry(
            self,
            width=ancho,
            height=38,
            placeholder_text=placeholder,
            font=F["cuerpo"],
            fg_color=C["hule_alto"],
            border_color=C["linea"],
            border_width=1,
            text_color=C["gis"],
            corner_radius=6,
            show="•" if password else "",
        )
        self.entrada.pack(fill="x")

        self.error = ctk.CTkLabel(
            self, text="", font=F["chico"], text_color=C["rojo"], anchor="w"
        )

    # --- API -----------------------------------------------------
    def get(self) -> str:
        return self.entrada.get().strip()

    def set(self, valor):
        self.entrada.delete(0, "end")
        if valor is not None:
            self.entrada.insert(0, str(valor))

    def limpiar(self):
        self.set("")
        self.ocultar_error()

    def marcar_error(self, mensaje: str):
        self.entrada.configure(border_color=C["rojo"])
        self.error.configure(text=mensaje)
        self.error.pack(anchor="w", pady=(3, 0))

    def ocultar_error(self):
        self.entrada.configure(border_color=C["linea"])
        self.error.pack_forget()

    def focus(self):
        self.entrada.focus_set()


class CampoSelect(ctk.CTkFrame):
    """Etiqueta + menú desplegable."""

    def __init__(self, master, etiqueta, valores=None, ancho=260, comando=None, **kw):
        super().__init__(master, fg_color="transparent", **kw)

        ctk.CTkLabel(
            self, text=etiqueta.upper(), font=F["etiqueta"],
            text_color=C["gis_tenue"], anchor="w",
        ).pack(anchor="w", pady=(0, 4))

        self.variable = ctk.StringVar(value=(valores or [""])[0])
        self.menu = ctk.CTkOptionMenu(
            self,
            values=valores or [""],
            variable=self.variable,
            width=ancho,
            height=38,
            font=F["cuerpo"],
            dropdown_font=F["cuerpo"],
            fg_color=C["hule_alto"],
            button_color=C["linea"],
            button_hover_color=C["altavis"],
            text_color=C["gis"],
            dropdown_fg_color=C["hule_alto"],
            dropdown_text_color=C["gis"],
            dropdown_hover_color=C["linea"],
            corner_radius=6,
            command=comando,
        )
        self.menu.pack(fill="x")

    def get(self) -> str:
        return self.variable.get()

    def set(self, valor):
        self.variable.set(valor)

    def cargar(self, valores, seleccionar=None):
        valores = valores or [""]
        self.menu.configure(values=valores)
        self.variable.set(seleccionar if seleccionar in valores else valores[0])


class Contador(ctk.CTkFrame):
    """Cantidad con botones - y +, como el 'Cantidad + [1]' del boceto."""

    def __init__(self, master, etiqueta="Cantidad", valor=1, minimo=1, maximo=99, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        self.minimo, self.maximo = minimo, maximo

        ctk.CTkLabel(
            self, text=etiqueta.upper(), font=F["etiqueta"],
            text_color=C["gis_tenue"], anchor="w",
        ).pack(anchor="w", pady=(0, 4))

        fila = ctk.CTkFrame(self, fg_color="transparent")
        fila.pack(anchor="w")

        self._boton(fila, "−", self.restar).pack(side="left")

        self.valor = ctk.CTkEntry(
            fila, width=64, height=38, justify="center", font=F["dato"],
            fg_color=C["hule_alto"], border_color=C["linea"], border_width=1,
            text_color=C["gis"], corner_radius=6,
        )
        self.valor.insert(0, str(valor))
        self.valor.pack(side="left", padx=6)

        self._boton(fila, "+", self.sumar).pack(side="left")

    def _boton(self, master, texto, comando):
        return ctk.CTkButton(
            master, text=texto, width=38, height=38, command=comando,
            font=(F["titulo"][0], 18), fg_color=C["hule_alto"],
            hover_color=C["linea"], text_color=C["altavis"], corner_radius=6,
        )

    def get(self) -> int:
        try:
            return max(self.minimo, min(self.maximo, int(self.valor.get())))
        except ValueError:
            return self.minimo

    def set(self, n: int):
        self.valor.delete(0, "end")
        self.valor.insert(0, str(max(self.minimo, min(self.maximo, int(n)))))

    def sumar(self):
        self.set(self.get() + 1)

    def restar(self):
        self.set(self.get() - 1)


# ==================================================================
# Botones
# ==================================================================
def boton_principal(master, texto, comando, ancho=200, alto=44, **kw):
    return ctk.CTkButton(
        master, text=texto.upper(), command=comando, width=ancho, height=alto,
        font=(F["titulo"][0], 15), fg_color=C["altavis"],
        hover_color=C["altavis_hover"], text_color=C["gis"],
        corner_radius=6, **kw
    )


def boton_secundario(master, texto, comando, ancho=200, alto=44, **kw):
    return ctk.CTkButton(
        master, text=texto.upper(), command=comando, width=ancho, height=alto,
        font=(F["titulo"][0], 15), fg_color="transparent",
        hover_color=C["hule_alto"], text_color=C["gis"],
        border_color=C["linea"], border_width=1, corner_radius=6, **kw
    )


# ==================================================================
# Métricas
# ==================================================================
class Metrica(Tarjeta):
    """Número grande + etiqueta. Se lee desde el otro lado del taller."""

    def __init__(self, master, etiqueta, valor="0", color=None, **kw):
        super().__init__(master, **kw)
        color = color or C["gis"]

        self.lbl_valor = ctk.CTkLabel(
            self, text=str(valor), font=F["metrica"], text_color=color
        )
        self.lbl_valor.pack(padx=18, pady=(16, 0), anchor="w")

        ctk.CTkLabel(
            self, text=etiqueta.upper(), font=F["etiqueta"], text_color=C["gis_tenue"]
        ).pack(padx=18, pady=(0, 16), anchor="w")

    def actualizar(self, valor):
        self.lbl_valor.configure(text=str(valor))


# ==================================================================
# Gráfica de dona
# ==================================================================
class Dona(ctk.CTkFrame):
    """
    Dona de producción. El hueco central lleva el total, así que la
    gráfica se lee como el corte de una llanta: banda de rodamiento y rin.
    """

    def __init__(self, master, titulo="", tamano=2.5, **kw):
        super().__init__(master, fg_color="transparent", **kw)

        self.figura = Figure(figsize=(tamano, tamano), dpi=100, facecolor=C["hule"])
        self.ejes = self.figura.add_subplot(111)
        self.figura.subplots_adjust(left=0, right=1, top=1, bottom=0)

        self.lienzo = FigureCanvasTkAgg(self.figura, master=self)
        self.lienzo.get_tk_widget().configure(bg=C["hule"], highlightthickness=0)
        self.lienzo.get_tk_widget().pack()

        if titulo:
            ctk.CTkLabel(
                self, text=titulo.upper(), font=F["etiqueta"], text_color=C["gis_tenue"]
            ).pack(pady=(4, 0))

        self.dibujar([], "0")

    def dibujar(self, datos, centro="0", subcentro=""):
        """datos = [(etiqueta, valor), ...]"""
        self.ejes.clear()
        self.ejes.set_facecolor(C["hule"])

        valores = [max(0, float(v)) for _, v in datos]
        etiquetas = [e for e, _ in datos]

        if not valores or sum(valores) == 0:
            self.ejes.pie(
                [1], colors=[C["hule_alto"]],
                wedgeprops={"width": 0.34, "edgecolor": C["hule"], "linewidth": 3},
                startangle=90,
            )
            centro, subcentro = "0", "sin registro"
        else:
            colores = [SERIE_COLORES[i % len(SERIE_COLORES)] for i in range(len(valores))]
            cunas, _ = self.ejes.pie(
                valores, colors=colores, startangle=90,
                wedgeprops={"width": 0.34, "edgecolor": C["hule"], "linewidth": 3},
            )
            total = sum(valores)
            for cuna, valor, etiqueta in zip(cunas, valores, etiquetas):
                if valor / total < 0.06:      # el texto no cabe en rebanadas mínimas
                    continue
                angulo = (cuna.theta2 + cuna.theta1) / 2
                x = 0.83 * math.cos(math.radians(angulo))
                y = 0.83 * math.sin(math.radians(angulo))
                self.ejes.text(
                    x, y, str(int(valor)), ha="center", va="center",
                    color=C["asfalto"], fontsize=9, fontweight="bold",
                )

        self.ejes.text(0, 0.08, str(centro), ha="center", va="center",
                       color=C["gis"], fontsize=26, fontweight="bold")
        if subcentro:
            self.ejes.text(0, -0.22, subcentro.upper(), ha="center", va="center",
                           color=C["gis_tenue"], fontsize=8)

        self.ejes.set_aspect("equal")
        self.lienzo.draw()


class Leyenda(ctk.CTkFrame):
    """Lista de etiquetas con su color, al lado de la dona."""

    def __init__(self, master, **kw):
        super().__init__(master, fg_color="transparent", **kw)

    def dibujar(self, datos):
        for hijo in self.winfo_children():
            hijo.destroy()

        if not datos:
            ctk.CTkLabel(
                self, text="Sin órdenes en el periodo.", font=F["chico"],
                text_color=C["gis_tenue"],
            ).pack(anchor="w")
            return

        for i, (etiqueta, valor) in enumerate(datos):
            fila = ctk.CTkFrame(self, fg_color="transparent")
            fila.pack(anchor="w", fill="x", pady=2)

            punto = tk.Canvas(fila, width=10, height=10, bg=C["hule"],
                              highlightthickness=0, bd=0)
            punto.create_oval(0, 0, 10, 10,
                              fill=SERIE_COLORES[i % len(SERIE_COLORES)], outline="")
            punto.pack(side="left", padx=(0, 8))

            ctk.CTkLabel(fila, text=str(etiqueta), font=F["chico"],
                         text_color=C["gis"]).pack(side="left")
            ctk.CTkLabel(fila, text=str(int(valor)), font=F["chico"],
                         text_color=C["gis_tenue"]).pack(side="right")


# ==================================================================
# Tabla (ttk.Treeview con la paleta de la app)
# ==================================================================
def aplicar_estilo_tabla(root):
    estilo = ttk.Style(root)
    estilo.theme_use("clam")
    estilo.configure(
        "Taller.Treeview",
        background=C["hule"],
        fieldbackground=C["hule"],
        foreground=C["gis"],
        rowheight=30,
        borderwidth=0,
        font=(F["cuerpo"][0], 11),
    )
    estilo.configure(
        "Taller.Treeview.Heading",
        background=C["hule_alto"],
        foreground=C["gis_tenue"],
        relief="flat",
        font=(F["etiqueta"][0], 10, "bold"),
    )
    estilo.map(
        "Taller.Treeview.Heading",
        background=[("active", C["linea"])],
    )
    estilo.map(
        "Taller.Treeview",
        background=[("selected", C["altavis"])],
        foreground=[("selected", C["asfalto"])],
    )
    estilo.configure("Taller.Vertical.TScrollbar",
                     background=C["hule_alto"], troughcolor=C["hule"],
                     bordercolor=C["hule"], arrowcolor=C["gis_tenue"])


def crear_tabla(master, columnas, anchos=None, altura=12):
    """
    columnas = [("clave", "Encabezado"), ...]
    Devuelve (contenedor, treeview).
    """
    contenedor = ctk.CTkFrame(master, fg_color=C["hule"], corner_radius=8)

    claves = [c[0] for c in columnas]
    tabla = ttk.Treeview(
        contenedor, columns=claves, show="headings",
        style="Taller.Treeview", height=altura,
    )
    for i, (clave, encabezado) in enumerate(columnas):
        tabla.heading(clave, text=encabezado.upper())
        ancho = (anchos or [])[i] if anchos and i < len(anchos) else 120
        tabla.column(clave, width=ancho, anchor="w")

    barra = ttk.Scrollbar(contenedor, orient="vertical", command=tabla.yview,
                          style="Taller.Vertical.TScrollbar")
    tabla.configure(yscrollcommand=barra.set)

    tabla.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
    barra.pack(side="right", fill="y", padx=(0, 8), pady=8)

    tabla.tag_configure("par", background=C["hule"])
    tabla.tag_configure("impar", background=C["hule_alto"])
    tabla.tag_configure("alerta", foreground=C["parche"])

    return contenedor, tabla


def llenar_tabla(tabla, filas, claves, formateadores=None, tag_extra=None):
    """
    filas            = lista de diccionarios
    claves           = orden de columnas
    formateadores    = {"clave": funcion}
    tag_extra        = funcion(fila) -> str o None
    """
    tabla.delete(*tabla.get_children())
    formateadores = formateadores or {}

    for i, fila in enumerate(filas):
        valores = []
        for clave in claves:
            valor = fila.get(clave)
            if clave in formateadores:
                valor = formateadores[clave](valor)
            valores.append("" if valor is None else valor)

        tags = ["par" if i % 2 == 0 else "impar"]
        if tag_extra:
            extra = tag_extra(fila)
            if extra:
                tags.append(extra)

        tabla.insert("", "end", values=valores, tags=tuple(tags))


# ==================================================================
# Avisos
# ==================================================================
class Aviso(ctk.CTkFrame):
    """Banda de mensaje que aparece arriba del formulario y se desvanece."""

    def __init__(self, master, **kw):
        super().__init__(master, fg_color=C["hule_alto"], corner_radius=6, **kw)
        self.etiqueta = ctk.CTkLabel(self, text="", font=F["cuerpo"],
                                     text_color=C["gis"], anchor="w")
        self.etiqueta.pack(fill="x", padx=14, pady=10)
        self._tarea = None

    def mostrar(self, mensaje, tipo="info", segundos=5):
        colores = {"info": C["azul"], "ok": C["verde"], "error": C["rojo"]}
        self.etiqueta.configure(text=mensaje, text_color=colores.get(tipo, C["gis"]))
        self.pack(fill="x", pady=(0, 12))

        if self._tarea:
            self.after_cancel(self._tarea)
        if segundos:
            self._tarea = self.after(segundos * 1000, self.ocultar)

    def ocultar(self):
        self._tarea = None
        self.pack_forget()
