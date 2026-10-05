"""
Componente de tabla interactiva de previsualización de artículos.
Permite filtrado dinámico, revisión de errores y visualización explícita de docenas/unidades.
"""

import flet as ft
from typing import List, Dict, Callable


class PreviewTableComponent(ft.Container):
    def __init__(
        self,
        on_search_change: Callable[[str], None],
        on_verify_status: Callable[[], None] = None,
    ):
        super().__init__()
        self.on_search_change = on_search_change
        self.on_verify_status = on_verify_status

        self.padding = ft.Padding.all(12)
        self.border_radius = ft.BorderRadius.all(10)
        self.bgcolor = ft.Colors.SURFACE
        self.expand = True

        # Campo de búsqueda en tiempo real
        self.search_field = ft.TextField(
            hint_text="Buscar por código, descripción, modelo o referencia...",
            prefix_icon=ft.Icons.SEARCH,
            dense=True,
            border_radius=8,
            on_change=lambda e: self.on_search_change(e.control.value),
            expand=True,
        )

        self.lbl_conteo = ft.Text("0 registros mostrados", size=12, color=ft.Colors.OUTLINE)

        self.btn_verificar = ft.OutlinedButton(
            content="Verificar si ya está Creado en Profit",
            icon=ft.Icons.SYNC_ROUNDED,
            style=ft.ButtonStyle(padding=ft.Padding.symmetric(horizontal=12, vertical=10)),
            on_click=lambda e: self.on_verify_status() if self.on_verify_status else None,
        )

        # Fila superior de búsqueda y acciones
        barra_herramientas = ft.Row(
            controls=[
                self.search_field,
                self.btn_verificar,
                self.lbl_conteo,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        )

        # Definición de columnas de la tabla
        self.data_table = ft.DataTable(
            heading_row_color=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            heading_row_height=42,
            data_row_min_height=38,
            data_row_max_height=48,
            column_spacing=18,
            columns=[
                ft.DataColumn(ft.Text("Estado", weight=ft.FontWeight.BOLD, size=11)),
                ft.DataColumn(ft.Text("Código", weight=ft.FontWeight.BOLD, size=11)),
                ft.DataColumn(ft.Text("Descripción", weight=ft.FontWeight.BOLD, size=11)),
                ft.DataColumn(ft.Text("Referencia", weight=ft.FontWeight.BOLD, size=11)),
                ft.DataColumn(ft.Text("Modelo", weight=ft.FontWeight.BOLD, size=11)),
                ft.DataColumn(ft.Text("Línea", weight=ft.FontWeight.BOLD, size=11)),
                ft.DataColumn(ft.Text("Sublínea", weight=ft.FontWeight.BOLD, size=11)),
                ft.DataColumn(ft.Text("Categoría", weight=ft.FontWeight.BOLD, size=11)),
                ft.DataColumn(ft.Text("Almacén", weight=ft.FontWeight.BOLD, size=11)),
                # Obligatorio especificar si es Docena o Unidad
                ft.DataColumn(ft.Text("Medida (Docena / Unidad)", weight=ft.FontWeight.BOLD, size=11)),
                ft.DataColumn(ft.Text("Stock Inicial", weight=ft.FontWeight.BOLD, size=11), numeric=True),
                ft.DataColumn(ft.Text("Precio 1", weight=ft.FontWeight.BOLD, size=11), numeric=True),
                ft.DataColumn(ft.Text("Precio 2", weight=ft.FontWeight.BOLD, size=11), numeric=True),
                ft.DataColumn(ft.Text("Precio 3", weight=ft.FontWeight.BOLD, size=11), numeric=True),
                ft.DataColumn(ft.Text("Precio 4", weight=ft.FontWeight.BOLD, size=11), numeric=True),
                ft.DataColumn(ft.Text("Precio 5", weight=ft.FontWeight.BOLD, size=11), numeric=True),
                ft.DataColumn(ft.Text("Observaciones", weight=ft.FontWeight.BOLD, size=11)),
            ],
            rows=[],
        )

        self.empty_state = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(ft.Icons.UPLOAD_FILE_OUTLINED, size=48, color=ft.Colors.OUTLINE),
                    ft.Text(
                        "No hay artículos para previsualizar",
                        size=14,
                        weight=ft.FontWeight.W_500,
                        color=ft.Colors.OUTLINE,
                    ),
                    ft.Text(
                        "Descarga la plantilla o selecciona un archivo Excel (.xlsx) / CSV para comenzar.",
                        size=12,
                        color=ft.Colors.OUTLINE,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            alignment=ft.Alignment.CENTER,
            padding=ft.Padding.all(40),
            expand=True,
        )

        # Contenedor con scroll para la tabla
        self.table_scroll_container = ft.Column(
            controls=[
                ft.Row(
                    controls=[self.data_table],
                    scroll=ft.ScrollMode.ADAPTIVE,
                )
            ],
            scroll=ft.ScrollMode.ADAPTIVE,
            expand=True,
            visible=False,
        )

        self.content = ft.Column(
            controls=[
                barra_herramientas,
                ft.Divider(height=8, color=ft.Colors.OUTLINE_VARIANT),
                self.empty_state,
                self.table_scroll_container,
            ],
            expand=True,
            spacing=8,
        )

    def actualizar_filas(self, articulos: List[Dict]):
        """Renderiza las filas de la tabla según los artículos proporcionados."""
        total = len(articulos)
        self.lbl_conteo.value = f"{total} registro{'s' if total != 1 else ''} mostrado{'s' if total != 1 else ''}"

        if not articulos:
            self.empty_state.visible = True
            self.table_scroll_container.visible = False
            self.data_table.rows.clear()
            self.update()
            return

        self.empty_state.visible = False
        self.table_scroll_container.visible = True

        filas = []
        for art in articulos:
            estado = art.get("estado", "")
            es_valido = art.get("es_valido", False)
            mensaje = art.get("mensaje_estado", "")
            unidad = str(art.get("unidad_tipo", "DOCENA")).upper()

            # Badge de Estado Dinámico
            if estado == "CREADO_EXITOSO":
                badge_color = ft.Colors.GREEN_400
                badge_bg = ft.Colors.with_opacity(0.2, ft.Colors.GREEN)
                badge_icon = ft.Icons.DONE_ALL_ROUNDED
                badge_text = "Creado en Profit"
            elif estado == "YA_EXISTE_BD":
                badge_color = ft.Colors.ORANGE_400
                badge_bg = ft.Colors.with_opacity(0.15, ft.Colors.ORANGE)
                badge_icon = ft.Icons.VERIFIED_OUTLINED
                badge_text = "Ya Creado en BD"
            elif es_valido:
                badge_color = ft.Colors.BLUE_400
                badge_bg = ft.Colors.with_opacity(0.15, ft.Colors.BLUE)
                badge_icon = ft.Icons.CHECK_CIRCLE_OUTLINE
                badge_text = "Listo para Cargar"
            elif estado == "DUPLICADO_ARCHIVO":
                badge_color = ft.Colors.AMBER_400
                badge_bg = ft.Colors.with_opacity(0.15, ft.Colors.AMBER)
                badge_icon = ft.Icons.CONTENT_COPY
                badge_text = "Repetido en Archivo"
            else:
                badge_color = ft.Colors.RED_400
                badge_bg = ft.Colors.with_opacity(0.15, ft.Colors.RED)
                badge_icon = ft.Icons.ERROR_OUTLINE
                badge_text = "Error de Formato"

            badge_estado = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(badge_icon, size=13, color=badge_color),
                        ft.Text(badge_text, size=11, weight=ft.FontWeight.W_500, color=badge_color),
                    ],
                    spacing=4,
                ),
                padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                border_radius=ft.BorderRadius.all(12),
                bgcolor=badge_bg,
            )

            # Badge de Unidad / Medida (Priorizando Docena)
            es_docena = "DOC" in unidad
            badge_unidad = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(
                            ft.Icons.AUTO_AWESOME_MOTION if es_docena else ft.Icons.SELL_OUTLINED,
                            size=12,
                            color=ft.Colors.BLUE_400 if es_docena else ft.Colors.AMBER_500,
                        ),
                        ft.Text(
                            "DOCENA (x12)" if es_docena else "UNIDAD (x1)",
                            size=11,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.BLUE_400 if es_docena else ft.Colors.AMBER_500,
                        ),
                    ],
                    spacing=4,
                ),
                padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                border_radius=ft.BorderRadius.all(12),
                bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.BLUE if es_docena else ft.Colors.AMBER),
            )

            stock_val = float(art.get("stock_inicial", 0.0) or 0.0)
            sufijo_stock = "DOC" if es_docena else "UND"

            fila = ft.DataRow(
                cells=[
                    ft.DataCell(badge_estado),
                    ft.DataCell(ft.Text(art.get("codigo", ""), weight=ft.FontWeight.W_600, size=12)),
                    ft.DataCell(ft.Text(art.get("descripcion", ""), size=12, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)),
                    ft.DataCell(ft.Text(art.get("referencia", "") or "-", size=11)),
                    ft.DataCell(ft.Text(art.get("modelo", "") or "-", size=11)),
                    ft.DataCell(ft.Text(art.get("linea") or "-", size=11)),
                    ft.DataCell(ft.Text(art.get("sublinea") or "-", size=11)),
                    ft.DataCell(ft.Text(art.get("categoria") or "-", size=11)),
                    ft.DataCell(ft.Text(art.get("almacen") or "-", size=11)),
                    ft.DataCell(badge_unidad),
                    ft.DataCell(ft.Text(f"{stock_val:g} {sufijo_stock}", size=11, weight=ft.FontWeight.W_500)),
                    ft.DataCell(ft.Text(f"${art.get('precio_1', 0.0):.2f}", size=11)),
                    ft.DataCell(ft.Text(f"${art.get('precio_2', 0.0):.2f}", size=11)),
                    ft.DataCell(ft.Text(f"${art.get('precio_3', 0.0):.2f}", size=11)),
                    ft.DataCell(ft.Text(f"${art.get('precio_4', 0.0):.2f}", size=11)),
                    ft.DataCell(ft.Text(f"${art.get('precio_5', 0.0):.2f}", size=11)),
                    ft.DataCell(
                        ft.Text(
                            mensaje,
                            size=11,
                            color=ft.Colors.OUTLINE if es_valido else badge_color,
                        )
                    ),
                ]
            )
            filas.append(fila)

        self.data_table.rows = filas
        self.update()
