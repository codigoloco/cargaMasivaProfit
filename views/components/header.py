"""
Componente Header para MasivoProfit.
Incluye selector de Base de Datos, estado de conexión y alternador de tema claro/oscuro.
"""

import flet as ft
from typing import Callable, List, Optional


class HeaderComponent(ft.Container):
    def __init__(
        self,
        bases_datos: List[str],
        base_datos_activa: Optional[str],
        on_db_change: Callable[[str], None],
        on_theme_toggle: Callable[[], None],
        is_dark_mode: bool = True,
    ):
        super().__init__()
        self.bases_datos = bases_datos
        self.base_datos_activa = base_datos_activa
        self.on_db_change = on_db_change
        self.on_theme_toggle = on_theme_toggle
        self.is_dark_mode = is_dark_mode

        self.padding = ft.Padding.symmetric(horizontal=20, vertical=12)
        self.border_radius = ft.BorderRadius.all(10)
        self.shadow = ft.BoxShadow(
            spread_radius=1,
            blur_radius=6,
            color=ft.Colors.BLACK12,
            offset=ft.Offset(0, 2),
        )

        self.dropdown_db = ft.Dropdown(
            label="Base de Datos Profit",
            width=220,
            value=self.base_datos_activa,
            options=[ft.DropdownOption(key=db, text=db) for db in self.bases_datos],
            on_select=self._handle_db_change,
            border_radius=8,
            dense=True,
            content_padding=10,
        )

        self.status_chip = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_400, size=16),
                    ft.Text("SQL Server Conectado", size=12, weight=ft.FontWeight.W_500),
                ],
                spacing=6,
            ),
            bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.GREEN),
            padding=ft.Padding.symmetric(horizontal=10, vertical=6),
            border_radius=ft.BorderRadius.all(16),
            border=ft.Border.all(1, ft.Colors.GREEN_400),
        )

        self.btn_theme = ft.IconButton(
            icon=ft.Icons.LIGHT_MODE if self.is_dark_mode else ft.Icons.DARK_MODE,
            tooltip="Alternar Modo Oscuro / Claro",
            on_click=self._handle_theme_click,
        )

        self.content = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                # Lado izquierdo: Título e ícono
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.INVENTORY_ROUNDED, size=32, color=ft.Colors.BLUE_400),
                        ft.Column(
                            spacing=0,
                            controls=[
                                ft.Text(
                                    "MasivoProfit",
                                    size=20,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.PRIMARY,
                                ),
                                ft.Text(
                                    "Gestión de Carga Masiva para Profit Plus",
                                    size=12,
                                    color=ft.Colors.OUTLINE,
                                ),
                            ],
                        ),
                    ],
                    spacing=12,
                ),
                # Lado derecho: Selector de BD, Estado y Tema
                ft.Row(
                    controls=[
                        self.status_chip,
                        self.dropdown_db,
                        self.btn_theme,
                    ],
                    spacing=14,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
        )

    def _handle_db_change(self, e):
        nueva_bd = self.dropdown_db.value
        if nueva_bd and self.on_db_change:
            self.base_datos_activa = nueva_bd
            self.on_db_change(nueva_bd)

    def _handle_theme_click(self, e):
        self.is_dark_mode = not self.is_dark_mode
        self.btn_theme.icon = (
            ft.Icons.LIGHT_MODE if self.is_dark_mode else ft.Icons.DARK_MODE
        )
        self.btn_theme.update()
        if self.on_theme_toggle:
            self.on_theme_toggle()

    def actualizar_bases_datos(self, bases: List[str], activa: Optional[str]):
        """Actualiza la lista y selección del dropdown."""
        self.bases_datos = bases
        self.base_datos_activa = activa
        self.dropdown_db.options = [ft.DropdownOption(key=db, text=db) for db in bases]
        self.dropdown_db.value = activa
        self.dropdown_db.update()
