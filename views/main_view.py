"""
Vista principal de la aplicación MasivoProfit.
Integra navegación por pestañas entre Carga Masiva y Configuración/Migraciones.
"""

import os
import flet as ft
from controllers.app_controller import AppController
from views.components.header import HeaderComponent
from views.components.file_picker import FilePickerComponent
from views.components.preview_table import PreviewTableComponent
from views.components.config_tab import ConfigTabComponent
from utils.dialog_helper import abrir_dialogo_archivo, abrir_dialogo_guardar


class MainView:
    def __init__(self, page: ft.Page, controller: AppController):
        self.page = page
        self.controller = controller

        # Indicadores de progreso flotante y barra de carga en tiempo real
        self.progress_ring = ft.ProgressRing(width=18, height=18, stroke_width=2, visible=False)
        self.lbl_progreso = ft.Text("", size=12, visible=False)
        self.lbl_progreso_contador = ft.Text("", size=12, weight=ft.FontWeight.BOLD, visible=False)
        self.progress_bar = ft.ProgressBar(
            value=0.0,
            visible=False,
            color=ft.Colors.BLUE_400,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            border_radius=ft.BorderRadius.all(4),
            height=6,
        )

        self.progress_container = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Row(
                                controls=[
                                    self.progress_ring,
                                    self.lbl_progreso,
                                ],
                                spacing=8,
                            ),
                            self.lbl_progreso_contador,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    self.progress_bar,
                ],
                spacing=6,
            ),
            padding=ft.Padding.symmetric(horizontal=4, vertical=2),
            visible=False,
        )

        # Componente Header
        self.header = HeaderComponent(
            bases_datos=self.controller.bases_datos,
            base_datos_activa=self.controller.base_datos_activa,
            on_db_change=self._on_db_change,
            on_theme_toggle=self._on_theme_toggle,
            is_dark_mode=self.page.theme_mode == ft.ThemeMode.DARK,
        )

        # Componente Panel de Archivos
        self.file_panel = FilePickerComponent(
            on_file_selected=self._iniciar_seleccion_archivo,
            on_download_template=self._iniciar_descarga_plantilla,
            on_process_batch=self._abrir_dialogo_confirmacion,
        )

        # Componente Tabla de Previsualización con verificación de existencia
        self.preview_table = PreviewTableComponent(
            on_search_change=self._on_search_change,
            on_verify_status=self._handle_verificar_existencia,
        )

        # Componente Pestaña de Configuración y Migraciones
        self.config_tab = ConfigTabComponent(
            config_controller=self.controller.config_controller,
            migration_controller=self.controller.migration_controller,
            on_notify=self._mostrar_notificacion,
            on_db_updated=self._on_db_updated_from_config,
        )
        self.config_tab.visible = False

        # Navegador de Pestañas (SegmentedButton)
        self.nav_tabs = ft.SegmentedButton(
            selected=["carga"],
            allow_multiple_selection=False,
            allow_empty_selection=False,
            segments=[
                ft.Segment(
                    value="carga",
                    label="Carga Masiva de Inventario",
                    icon=ft.Icons.UPLOAD_FILE_ROUNDED,
                ),
                ft.Segment(
                    value="config",
                    label="Configuración y Migraciones",
                    icon=ft.Icons.SETTINGS_SUGGEST_ROUNDED,
                ),
            ],
            on_change=self._handle_tab_change,
        )

        # Contenedor de la pestaña de Carga Masiva
        self.carga_panel = ft.Column(
            controls=[
                ft.Row(controls=[self.file_panel]),
                self.progress_container,
                self.preview_table,
            ],
            spacing=14,
            expand=True,
            visible=True,
        )

    def build(self) -> ft.Control:
        """Ensambla el contenedor principal de la interfaz."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    self.header,
                    ft.Row(
                        controls=[self.nav_tabs],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    self.carga_panel,
                    self.config_tab,
                ],
                spacing=12,
                expand=True,
            ),
            padding=16,
            expand=True,
        )

    # --- Manejadores de Eventos de Navegación y Configuración ---

    def _handle_tab_change(self, e):
        seleccionado = self.nav_tabs.selected
        es_carga = "carga" in seleccionado
        self.carga_panel.visible = es_carga
        self.config_tab.visible = not es_carga
        if not es_carga:
            # Al entrar a configuración, refrescar estado de migraciones
            self.config_tab.actualizar_estado_migraciones()
        self.page.update()

    def _on_db_updated_from_config(self, nueva_bd: str):
        """Callback cuando se guarda nueva BD desde la pestaña de configuración."""
        self._on_db_change(nueva_bd)

    def _on_db_change(self, nueva_bd: str):
        exito = self.controller.cambiar_base_datos(nueva_bd)
        if exito:
            self.header.actualizar_bases_datos(self.controller.bases_datos, nueva_bd)
            self.file_panel.actualizar_metricas(self.controller.resumen_carga)
            self.preview_table.actualizar_filas(self.controller.obtener_articulos_filtrados())
            self.config_tab.txt_database.value = nueva_bd
            self.config_tab.actualizar_estado_migraciones()
            self._mostrar_notificacion(
                f"Base de datos cambiada a: {nueva_bd}. Contexto y migraciones actualizados.",
                color=ft.Colors.GREEN_400,
            )
        else:
            self._mostrar_notificacion(
                f"No se pudo conectar a la base de datos: {nueva_bd}",
                color=ft.Colors.RED_400,
            )

    def _on_theme_toggle(self):
        self.page.theme_mode = (
            ft.ThemeMode.LIGHT
            if self.page.theme_mode == ft.ThemeMode.DARK
            else ft.ThemeMode.DARK
        )
        self.page.update()

    # --- Carga y Gestión de Archivos ---

    def _iniciar_seleccion_archivo(self, ruta_param: str = ""):
        ruta = abrir_dialogo_archivo()
        if not ruta:
            return

        nombre = os.path.basename(ruta)
        self._mostrar_progreso("Analizando archivo y validando contra Profit Plus...")
        try:
            resultado = self.controller.cargar_archivo(ruta)
            self.file_panel.actualizar_metricas(resultado["resumen"], nombre)
            self.preview_table.actualizar_filas(self.controller.obtener_articulos_filtrados())
            self._ocultar_progreso()

            resumen = resultado["resumen"]
            self._mostrar_notificacion(
                f"Archivo analizado: {resumen['validos']} listos para registrar, {resumen['errores']} con observación.",
                color=ft.Colors.GREEN_400 if resumen["validos"] > 0 else ft.Colors.ORANGE_400,
            )
        except Exception as err:
            self._ocultar_progreso()
            self._mostrar_notificacion(f"Error al leer archivo: {str(err)}", color=ft.Colors.RED_400)

    def _iniciar_descarga_plantilla(self):
        ruta_guardado = abrir_dialogo_guardar()
        if not ruta_guardado:
            return
        try:
            ruta = self.controller.template_controller.descargar_plantilla(ruta_guardado)
            self._mostrar_notificacion(
                f"Plantilla generada con éxito en: {ruta}",
                color=ft.Colors.GREEN_400,
            )
        except Exception as err:
            self._mostrar_notificacion(
                f"Error al guardar plantilla: {str(err)}",
                color=ft.Colors.RED_400,
            )

    def _on_search_change(self, query: str):
        self.controller.filtro_busqueda = query
        self.preview_table.actualizar_filas(self.controller.obtener_articulos_filtrados())

    def _crear_dialogo_confirmacion(self) -> ft.AlertDialog:
        """Construye dinámicamente el diálogo de confirmación con el resumen actual."""
        resumen = self.controller.resumen_carga
        validos = resumen.get("validos", 0)
        docenas = resumen.get("docenas", 0)
        unidades = resumen.get("unidades", 0)
        bd = self.controller.base_datos_activa
        operador = self.controller.config_data.get("operador_usuario", "ADMIN")

        return ft.AlertDialog(
            modal=True,
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.HELP_OUTLINE, color=ft.Colors.BLUE_400),
                    ft.Text("Confirmar Carga Masiva"),
                ],
                spacing=10,
            ),
            content=ft.Column(
                tight=True,
                controls=[
                    ft.Text(f"¿Deseas procesar la carga masiva en la base de datos '{bd}'?"),
                    ft.Container(height=8),
                    ft.Text(f"• Artículos a insertar: {validos}", weight=ft.FontWeight.BOLD),
                    ft.Text(f"• En Docenas: {docenas} (factor 12 en saArtUnidad)"),
                    ft.Text(f"• En Unidades: {unidades} (factor 1 en saArtUnidad)"),
                    ft.Text(f"• Operador responsable: {operador}"),
                    ft.Container(height=8),
                    ft.Text(
                        "Esta operación creará los artículos en el catálogo maestro (saArticulo), sus listas de precios (1 al 5) en saArtPrecio, "
                        "sus unidades en saArtUnidad, inicializará sus existencias en saStockAlmacen (Almacén 01) y quedará registrada en la tabla de auditoría.",
                        size=12,
                        color=ft.Colors.OUTLINE,
                    ),
                ],
            ),
            actions=[
                ft.TextButton(content="Cancelar", on_click=self._cerrar_dialogo_confirmacion),
                ft.ElevatedButton(
                    content="Proceder con la Carga",
                    bgcolor=ft.Colors.BLUE_600,
                    color=ft.Colors.WHITE,
                    on_click=self._ejecutar_carga_confirmada,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def _abrir_dialogo_confirmacion(self):
        try:
            dialogo = self._crear_dialogo_confirmacion()
            self.page.show_dialog(dialogo)
        except Exception as err:
            print(f"Aviso al mostrar diálogo con show_dialog: {err}. Ejecutando carga directa.")
            self._ejecutar_carga_confirmada()

    def _cerrar_dialogo_confirmacion(self, e=None):
        try:
            self.page.pop_dialog()
        except Exception:
            pass

    def _handle_verificar_existencia(self):
        """Consulta en Profit Plus el estado actual de los artículos cargados."""
        if not self.controller.articulos_cargados:
            self._mostrar_notificacion("Carga o selecciona un archivo antes de verificar.", color=ft.Colors.ORANGE_400)
            return

        self._mostrar_progreso("Consultando catálogo de productos en Profit Plus (saArticulo)...")
        existentes, no_existentes = self.controller.verificar_existencia_articulos()
        self._ocultar_progreso()

        self.file_panel.actualizar_metricas(self.controller.resumen_carga)
        self.preview_table.actualizar_filas(self.controller.obtener_articulos_filtrados())
        self._mostrar_notificacion(
            f"Verificación completada: {existentes} productos ya están creados en Profit Plus, {no_existentes} listos para registrar.",
            color=ft.Colors.BLUE_400,
        )

    def _ejecutar_carga_confirmada(self, e=None):
        self._cerrar_dialogo_confirmacion()
        total_a_insertar = self.controller.resumen_carga.get("validos", 0)
        self._iniciar_progreso_barra("Insertando artículos y registrando auditoría en Profit Plus...", total_a_insertar)

        def callback_progreso(actual: int, total: int, art: dict):
            codigo = art.get("codigo", "")
            desc = art.get("descripcion", "")[:28]
            self._actualizar_progreso_barra(actual, total, f"Insertando: {codigo} - {desc}")

        exito, insertados, errores = self.controller.procesar_lote_actual(callback_progreso=callback_progreso)
        self._ocultar_progreso()

        if exito:
            self.file_panel.actualizar_metricas(self.controller.resumen_carga)
            self.preview_table.actualizar_filas(self.controller.obtener_articulos_filtrados())
            self._mostrar_notificacion(
                f"¡Carga masiva completada con éxito! Se insertaron {insertados} artículos.",
                color=ft.Colors.GREEN_400,
            )
        else:
            msg_error = errores[0] if errores else "Ocurrió un error inesperado."
            self._mostrar_notificacion(f"Error en la carga: {msg_error}", color=ft.Colors.RED_400)

    # --- Helpers de UI y Barra de Progreso ---

    def _iniciar_progreso_barra(self, mensaje: str, total: int):
        self.progress_container.visible = True
        self.progress_ring.visible = True
        self.progress_bar.visible = True
        self.progress_bar.value = 0.0
        self.lbl_progreso.value = mensaje
        self.lbl_progreso.visible = True
        self.lbl_progreso_contador.value = f"0 / {total}"
        self.lbl_progreso_contador.visible = True
        self.page.update()

    def _actualizar_progreso_barra(self, actual: int, total: int, detalle: str):
        porcentaje = (actual / total) if total > 0 else 1.0
        self.progress_bar.value = porcentaje
        self.lbl_progreso.value = detalle
        self.lbl_progreso_contador.value = f"{actual} / {total} ({int(porcentaje * 100)}%)"
        self.page.update()

    def _mostrar_progreso(self, mensaje: str):
        self.progress_container.visible = True
        self.progress_ring.visible = True
        self.progress_bar.visible = True
        self.progress_bar.value = None  # Modo indeterminado
        self.lbl_progreso.value = mensaje
        self.lbl_progreso.visible = True
        self.lbl_progreso_contador.visible = False
        self.page.update()

    def _ocultar_progreso(self):
        self.progress_container.visible = False
        self.progress_ring.visible = False
        self.progress_bar.visible = False
        self.progress_bar.value = 0.0
        self.lbl_progreso.visible = False
        self.lbl_progreso_contador.visible = False
        self.page.update()

    def _mostrar_notificacion(self, mensaje: str, color=ft.Colors.BLUE_400):
        snackbar = ft.SnackBar(
            content=ft.Text(mensaje, color=ft.Colors.WHITE, size=13),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            show_close_icon=True,
            duration=5000,
        )
        try:
            self.page.show_dialog(snackbar)
        except Exception:
            self.page.overlay.append(snackbar)
            snackbar.open = True
            self.page.update()
