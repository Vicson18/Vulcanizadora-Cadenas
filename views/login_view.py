# -*- coding: utf-8 -*-
"""
views/login_view.py
Pantalla 1 del boceto: Username, Password, Access.
"""

import customtkinter as ctk

from config import C, F, APP_NOMBRE, APP_SUBTITULO, APP_VERSION
from database import ErrorBaseDatos
from widgets import Campo, Huella, Tarjeta, boton_principal
import repositorio


class LoginView(ctk.CTkFrame):

    def __init__(self, master, app):
        super().__init__(master, fg_color=C["asfalto"])
        self.app = app
        self._construir()

    # --------------------------------------------------------------
    def _construir(self):
        centro = ctk.CTkFrame(self, fg_color="transparent")
        centro.place(relx=0.5, rely=0.5, anchor="center")

        # --- Marca ---------------------------------------------------
        ctk.CTkLabel(
            centro, text=APP_NOMBRE.upper(), font=F["display"], text_color=C["gis"]
        ).pack()
        Huella(centro, ancho=300, alto=12, fondo=C["asfalto"]).pack(pady=(6, 4))
        ctk.CTkLabel(
            centro, text=APP_SUBTITULO, font=F["cuerpo"], text_color=C["gis_tenue"]
        ).pack(pady=(0, 26))

        # --- Tarjeta de acceso --------------------------------------
        tarjeta = Tarjeta(centro)
        tarjeta.pack()

        interior = ctk.CTkFrame(tarjeta, fg_color="transparent")
        interior.pack(padx=36, pady=34)

        self.campo_usuario = Campo(interior, "Usuario", "nombre de usuario", ancho=280)
        self.campo_usuario.pack(pady=(0, 16))

        self.campo_password = Campo(interior, "Contraseña", "contraseña",
                                    ancho=280, password=True)
        self.campo_password.pack(pady=(0, 8))

        self.mensaje = ctk.CTkLabel(
            interior, text="", font=F["chico"], text_color=C["rojo"], wraplength=280
        )
        self.mensaje.pack(pady=(0, 12))

        self.boton = boton_principal(interior, "Entrar", self.entrar, ancho=280)
        self.boton.pack()

        ctk.CTkLabel(
            centro, text=f"v{APP_VERSION}", font=F["chico"], text_color=C["linea"]
        ).pack(pady=(18, 0))

        # Enter en cualquiera de los dos campos entra
        for campo in (self.campo_usuario, self.campo_password):
            campo.entrada.bind("<Return>", lambda _e: self.entrar())

    # --------------------------------------------------------------
    def al_mostrar(self):
        self.campo_password.set("")
        self.mensaje.configure(text="")
        self.campo_usuario.focus()

    # --------------------------------------------------------------
    def entrar(self):
        usuario = self.campo_usuario.get()
        password = self.campo_password.entrada.get()

        self.campo_usuario.ocultar_error()
        self.campo_password.ocultar_error()
        self.mensaje.configure(text="")

        if not usuario:
            self.campo_usuario.marcar_error("Escribe tu usuario.")
            return
        if not password:
            self.campo_password.marcar_error("Escribe tu contraseña.")
            return

        self.boton.configure(text="VERIFICANDO…", state="disabled")
        self.update_idletasks()

        try:
            sesion = repositorio.validar_acceso(usuario, password)
        except ErrorBaseDatos as ex:
            self.mensaje.configure(text=str(ex))
            self.boton.configure(text="ENTRAR", state="normal")
            return

        self.boton.configure(text="ENTRAR", state="normal")

        if sesion is None:
            self.mensaje.configure(text="Usuario o contraseña incorrectos.")
            self.campo_password.set("")
            self.campo_password.focus()
            return

        self.app.iniciar_sesion(sesion)
