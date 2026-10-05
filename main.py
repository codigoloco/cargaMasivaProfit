"""
Punto de entrada de MasivoProfit.
Inicializa la aplicación de escritorio Flet, el controlador principal y la vista.
"""

import sys
import os

# Asegurar que el directorio raíz del proyecto esté en el path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import flet as ft
from config import APP_TITLE, DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT
from controllers.app_controller import AppController
from views.main_view import MainView


def main(page: ft.Page):
    # Configuración de ventana
    page.title = APP_TITLE
    page.window.width = DEFAULT_WINDOW_WIDTH
    page.window.height = DEFAULT_WINDOW_HEIGHT
    page.window.min_width = 1000
    page.window.min_height = 650
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0

    # Inicialización del controlador
    controller = AppController()
    conectado, mensaje_conexion = controller.inicializar_sistema()

    # Construcción de la vista principal
    vista_principal = MainView(page, controller)
    page.add(vista_principal.build())

    # Notificar estado de la conexión inicial
    if conectado:
        vista_principal._mostrar_notificacion(mensaje_conexion, color=ft.Colors.GREEN_400)
    else:
        vista_principal._mostrar_notificacion(mensaje_conexion, color=ft.Colors.ORANGE_400)

    page.update()


if __name__ == "__main__":
    ft.run(main)
