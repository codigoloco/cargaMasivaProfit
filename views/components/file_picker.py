"""
Componente de selección de archivos, descarga de plantilla y tarjetas de métricas.
"""

import flet as ft
from typing import Callable, Dict


class FilePickerComponent(ft.Container):
    def __init__(
        self,
        on_file_selected: Callable[[str], None],
        on_download_template: Callable[[], None],
        on_process_batch: Callable[[], None],
    ):
        super().__init__()
        self.on_file_selected = on_file_selected
        self.on_download_template = on_download_template
        self.on_process_batch = on_process_batch

        self.padding = ft.Padding.all(16)
        self.border_radius = ft.BorderRadius.all(10)
        self.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGHEST

        # Métricas interactivas
        self.txt_total = ft.Text("0", size=22, weight=ft.FontWeight.BOLD)
        self.txt_validos = ft.Text("0", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_400)
        self.txt_errores = ft.Text("0", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_400)
        self.txt_docenas = ft.Text("0", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_400)
        self.txt_unidades = ft.Text("0", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_400)

        # Botón de procesamiento
        self.btn_procesar = ft.ElevatedButton(
            content="Procesar Carga Masiva (0)",
            icon=ft.Icons.UPLOAD_FILE,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.BLUE_700,
                padding=ft.Padding.symmetric(horizontal=20, vertical=16),
            ),
            disabled=True,
            on_click=lambda e: self.on_process_batch(),
        )

        self.btn_seleccionar_archivo = ft.ElevatedButton(
            content="Cargar Archivo Excel / CSV",
            icon=ft.Icons.FILE_UPLOAD_OUTLINED,
            style=ft.ButtonStyle(
                padding=ft.Padding.symmetric(horizontal=16, vertical=14),
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                color=ft.Colors.PRIMARY,
            ),
            on_click=lambda e: self.on_file_selected(""),
        )

        self.btn_descargar_plantilla = ft.OutlinedButton(
            content="Descargar Plantilla Excel",
            icon=ft.Icons.FILE_DOWNLOAD_OUTLINED,
            style=ft.ButtonStyle(
                padding=ft.Padding.symmetric(horizontal=16, vertical=14),
            ),
            on_click=lambda e: self.on_download_template(),
        )

        self.txt_archivo_cargado = ft.Text(
            "Ningún archivo seleccionado",
            size=12,
            italic=True,
            color=ft.Colors.OUTLINE,
        )

        # Fila de Botones
        fila_acciones = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(
                    controls=[
                        self.btn_seleccionar_archivo,
                        self.btn_descargar_plantilla,
                        self.txt_archivo_cargado,
                    ],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                self.btn_procesar,
            ],
        )

        # Fila de Tarjetas de Resumen
        fila_kpis = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                self._crear_tarjeta_kpi("Total Registros", self.txt_total, ft.Icons.LIST_ALT, ft.Colors.BLUE_GREY_400),
                self._crear_tarjeta_kpi("Listos para Registrar", self.txt_validos, ft.Icons.CHECK_CIRCLE, ft.Colors.GREEN_400),
                self._crear_tarjeta_kpi("Con Errores / Repetidos", self.txt_errores, ft.Icons.ERROR_OUTLINE, ft.Colors.RED_400),
                self._crear_tarjeta_kpi("En Docenas (DOC)", self.txt_docenas, ft.Icons.AUTO_AWESOME_MOTION, ft.Colors.BLUE_400),
                self._crear_tarjeta_kpi("En Unidades (UND)", self.txt_unidades, ft.Icons.SELL_OUTLINED, ft.Colors.AMBER_400),
            ],
            spacing=10,
        )

        self.content = ft.Column(
            controls=[
                fila_acciones,
                ft.Divider(height=12, color=ft.Colors.OUTLINE_VARIANT),
                fila_kpis,
            ],
            spacing=12,
        )

    def _crear_tarjeta_kpi(self, titulo: str, widget_valor: ft.Text, icono, color_icono) -> ft.Container:
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(icono, color=color_icono, size=28),
                    ft.Column(
                        spacing=0,
                        controls=[
                            ft.Text(titulo, size=11, color=ft.Colors.OUTLINE),
                            widget_valor,
                        ],
                    ),
                ],
                spacing=10,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(horizontal=14, vertical=10),
            border_radius=ft.BorderRadius.all(8),
            bgcolor=ft.Colors.SURFACE,
            expand=True,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        )

    def actualizar_metricas(self, resumen: Dict, nombre_archivo: str = ""):
        """Actualiza las tarjetas de resumen y el estado del botón de procesar."""
        total = resumen.get("total", 0)
        validos = resumen.get("validos", 0)
        errores = resumen.get("errores", 0)
        docenas = resumen.get("docenas", 0)
        unidades = resumen.get("unidades", 0)

        self.txt_total.value = str(total)
        self.txt_validos.value = str(validos)
        self.txt_errores.value = str(errores)
        self.txt_docenas.value = str(docenas)
        self.txt_unidades.value = str(unidades)

        if nombre_archivo:
            self.txt_archivo_cargado.value = f"Archivo activo: {nombre_archivo}"
            self.txt_archivo_cargado.italic = False
            self.txt_archivo_cargado.weight = ft.FontWeight.W_500

        self.btn_procesar.content = f"Procesar Carga Masiva ({validos})"
        self.btn_procesar.disabled = validos == 0

        self.update()
