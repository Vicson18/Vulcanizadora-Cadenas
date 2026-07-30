# -*- coding: utf-8 -*-
"""
main.py
Punto de entrada de la aplicación de la vulcanizadora.

Ejecutar:  python main.py
"""

import sys
import tkinter as tk
from tkinter import font as tkfont, messagebox

import customtkinter as ctk

import config
from config import C, F, APP_NOMBRE, APP_SUBTITULO
from database import probar_conexion
from widgets import Aviso, Huella, aplicar_estilo_tabla
from views import LoginView, DashboardView, OrdenesView, InventarioView


class Aplicacion(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.sesion = None
        self.vistas = {}
        self.vista_actual = None

        self.title(f"{APP_NOMBRE} · {APP_SUBTITULO}")
        self.geometry("1360x820")
        self.minsize(1180, 720)
        self.configure(fg_color=C["asfalto"])

        ctk.set_appearance_mode("dark")

        self._verificar_fuentes()
        aplicar_estilo_tabla(self)

        self._barra_superior()
        self._area_vistas()

        self.protocol("WM_DELETE_WINDOW", self.salir)

        if not self._verificar_base_datos():
            return

        self.mostrar("login")

    # ==============================================================
    # Arranque
    # ==============================================================
    def _verificar_fuentes(self):
        """Si Bahnschrift no está instalada, usa Segoe UI y no rompe nada."""
        disponibles = set(tkfont.families(self))
        if config.FUENTE_TITULO not in disponibles:
            reemplazo = "Segoe UI Semibold" if "Segoe UI Semibold" in disponibles else "Arial"
            for clave, valor in F.items():
                if valor[0] == config.FUENTE_TITULO:
                    F[clave] = (reemplazo,) + tuple(valor[1:])
            config.FUENTE_TITULO = reemplazo

    def _verificar_base_datos(self) -> bool:
        ok, mensaje = probar_conexion()
        if ok:
            return True

        messagebox.showerror(
            "No se pudo conectar",
            f"{mensaje}\n\n"
            "Revisa DB_CONFIG en config.py y ejecuta los scripts de la carpeta sql/:\n"
            "  1. sql/01_schema.sql\n"
            "  2. sql/02_datos_iniciales.sql",
        )
        self.destroy()
        return False

    # ==============================================================
    # Estructura
    # ==============================================================
    def _barra_superior(self):
        self.barra = ctk.CTkFrame(self, fg_color=C["barra"], corner_radius=0, height=64)
        self.barra.pack_propagate(False)

        interior = ctk.CTkFrame(self.barra, fg_color="transparent")
        interior.pack(fill="both", expand=True, padx=28)

        # --- Marca ---------------------------------------------------
        marca = ctk.CTkFrame(interior, fg_color="transparent")
        marca.pack(side="left", pady=10)

        ctk.CTkLabel(marca, text=APP_NOMBRE.upper(), font=(F["titulo"][0], 20),
                     text_color=C["gis"]).pack(anchor="w")
        Huella(marca, ancho=120, alto=6, fondo=C["barra"]).pack(anchor="w", pady=(1, 0))

        # --- Navegación ----------------------------------------------
        navegacion = ctk.CTkFrame(interior, fg_color="transparent")
        navegacion.pack(side="left", padx=40)

        self.botones_nav = {}
        for clave, texto in (("dashboard", "Tablero"),
                             ("ordenes", "Crear orden"),
                             ("inventario", "Inventario")):
            boton = ctk.CTkButton(
                navegacion, text=texto.upper(), width=160, height=40,
                font=(F["titulo"][0], 18), corner_radius=6,
                fg_color="transparent", hover_color=C["hule_alto"],
                text_color=C["gis"],
                command=lambda c=clave: self.mostrar(c),
            )
            boton.pack(side="left", padx=(0, 6))
            self.botones_nav[clave] = boton

        # --- Sesión ---------------------------------------------------
        sesion = ctk.CTkFrame(interior, fg_color="transparent")
        sesion.pack(side="right")

        self.lbl_usuario = ctk.CTkLabel(sesion, text="", font=F["chico"],
                                        text_color=C["gis"])
        self.lbl_usuario.pack(side="left", padx=(0, 14))

        ctk.CTkButton(
            sesion, text="SALIR", width=90, height=36, font=(F["titulo"][0], 13),
            fg_color="transparent", hover_color=C["hule_alto"],
            text_color=C["gis"], border_color=C["linea"], border_width=1,
            corner_radius=6, command=self.cerrar_sesion,
        ).pack(side="left")

    def _area_vistas(self):
        self.contenido = ctk.CTkFrame(self, fg_color=C["asfalto"], corner_radius=0)
        self.contenido.pack(fill="both", expand=True)

        self.aviso_global = Aviso(self.contenido)

        self.vistas = {
            "login": LoginView(self.contenido, self),
            "dashboard": DashboardView(self.contenido, self),
            "ordenes": OrdenesView(self.contenido, self),
            "inventario": InventarioView(self.contenido, self),
        }

    # ==============================================================
    # Navegación
    # ==============================================================
    def mostrar(self, nombre: str):
        if nombre != "login" and self.sesion is None:
            nombre = "login"

        if self.vista_actual is not None:
            self.vista_actual.pack_forget()

        # La barra superior solo existe cuando hay sesión iniciada
        if nombre == "login":
            self.barra.pack_forget()
        else:
            self.barra.pack(fill="x", before=self.contenido)

        vista = self.vistas[nombre]
        vista.pack(fill="both", expand=True)
        self.vista_actual = vista

        for clave, boton in self.botones_nav.items():
            activo = clave == nombre
            boton.configure(
                fg_color=C["hule_alto"] if activo else "transparent",
                text_color=C["altavis"] if activo else C["gis"],
            )

        if hasattr(vista, "al_mostrar"):
            vista.al_mostrar()

    def iniciar_sesion(self, sesion: dict):
        self.sesion = sesion
        nombre = sesion.get("NombreCompleto") or sesion.get("Username")
        self.lbl_usuario.configure(text=f"{nombre} · {sesion.get('Rol', '')}")
        self.mostrar("dashboard")

    def cerrar_sesion(self):
        self.sesion = None
        self.lbl_usuario.configure(text="")
        self.mostrar("login")

    def avisar(self, mensaje: str, tipo: str = "info"):
        self.aviso_global.mostrar(mensaje, tipo)
        if self.vista_actual is not None:
            self.aviso_global.pack(fill="x", padx=28, pady=(14, 0),
                                   before=self.vista_actual)

    def salir(self):
        self.destroy()
        sys.exit(0)


if __name__ == "__main__":
    Aplicacion().mainloop()
