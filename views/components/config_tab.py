"""
Componente de Vista para la Pestaña de Configuración y Migraciones.
Permite configurar credenciales de SQL Server, usuario operador, parámetros Profit
y administrar las migraciones estilo Django (migrate / makemigrations).
"""

import pyodbc
import flet as ft
from typing import Callable, Dict, Any, List
from controllers.config_controller import ConfigController
from controllers.migration_controller import MigrationController


class ConfigTabComponent(ft.Container):
    def __init__(
        self,
        config_controller: ConfigController,
        migration_controller: MigrationController,
        on_notify: Callable[[str, Any], None],
        on_db_updated: Callable[[str], None],
    ):
        super().__init__()
        self.config_controller = config_controller
        self.migration_controller = migration_controller
        self.on_notify = on_notify
        self.on_db_updated = on_db_updated

        self.padding = ft.Padding.all(16)
        self.expand = True

        cfg = self.config_controller.obtener_configuracion()
        p_def = cfg.get("profit_defaults", {})

        # --- Controladores ODBC del Sistema ---
        drivers_instalados = pyodbc.drivers()
        driver_actual = cfg.get("odbc_driver", "ODBC Driver 17 for SQL Server")

        self.dropdown_driver = ft.Dropdown(
            label="Controladores ODBC Existentes en el Sistema",
            value=driver_actual if driver_actual in drivers_instalados else (drivers_instalados[0] if drivers_instalados else None),
            options=[ft.DropdownOption(key=d, text=d) for d in drivers_instalados],
            dense=True,
            border_radius=8,
            expand=True,
            on_select=self._on_driver_dropdown_change,
        )

        self.txt_driver = ft.TextField(
            label="Asignar Controlador Manualmente",
            value=driver_actual,
            dense=True,
            border_radius=8,
            expand=True,
            helper="Nombre exacto del driver ODBC",
        )

        # --- Campos de Conexión ---
        self.txt_server = ft.TextField(
            label="Servidor SQL Server",
            value=cfg.get("sql_server", r"localhost\SQLEXPRESS"),
            dense=True,
            border_radius=8,
            expand=True,
        )
        self.txt_database = ft.TextField(
            label="Base de Datos",
            value=cfg.get("database", "DEMOA"),
            dense=True,
            border_radius=8,
            width=220,
        )
        self.switch_trusted = ft.Switch(
            label="Autenticación de Windows (Trusted Connection)",
            value=cfg.get("trusted_connection", True),
            on_change=self._toggle_auth_mode,
        )
        self.txt_db_user = ft.TextField(
            label="Usuario SQL Server",
            value=cfg.get("db_user", ""),
            dense=True,
            border_radius=8,
            disabled=cfg.get("trusted_connection", True),
            expand=True,
        )
        self.txt_db_pass = ft.TextField(
            label="Contraseña SQL Server",
            value=cfg.get("db_password", ""),
            password=True,
            can_reveal_password=True,
            dense=True,
            border_radius=8,
            disabled=cfg.get("trusted_connection", True),
            expand=True,
        )
        self.txt_operador = ft.TextField(
            label="Usuario Operador (Auditoría)",
            value=cfg.get("operador_usuario", "ADMIN"),
            dense=True,
            border_radius=8,
            width=220,
            helper="Firma auditorías y migraciones",
        )

        # --- Campos Parámetros Profit ---
        self.txt_co_lin = ft.TextField(label="Línea Defecto", value=p_def.get("co_lin", "006"), width=120, dense=True, border_radius=8)
        self.txt_co_subl = ft.TextField(label="Sublínea", value=p_def.get("co_subl", "012"), width=120, dense=True, border_radius=8)
        self.txt_co_cat = ft.TextField(label="Categoría", value=p_def.get("co_cat", "001"), width=120, dense=True, border_radius=8)
        self.txt_co_color = ft.TextField(label="Color", value=p_def.get("co_color", "001"), width=120, dense=True, border_radius=8)
        self.txt_co_alma = ft.TextField(label="Almacén", value=p_def.get("co_ubicacion", "ALM"), width=120, dense=True, border_radius=8)
        self.txt_co_us_in = ft.TextField(label="Usuario Profit", value=p_def.get("co_us_in", "001"), width=120, dense=True, border_radius=8)
        self.txt_co_mone = ft.TextField(label="Moneda", value=p_def.get("co_mone", "USD"), width=120, dense=True, border_radius=8)

        # --- Campos de Migraciones ---
        self.lbl_mig_resumen = ft.Text("", size=13, weight=ft.FontWeight.W_500)
        self.txt_nueva_migracion = ft.TextField(
            label="Nombre de nueva migración (makemigrations)",
            hint_text="ej: agregar_indices_inventario",
            dense=True,
            border_radius=8,
            expand=True,
        )

        self.btn_crear_migracion = ft.OutlinedButton(
            content="Crear Migración",
            icon=ft.Icons.NOTE_ADD_OUTLINED,
            style=ft.ButtonStyle(padding=ft.Padding.symmetric(horizontal=16, vertical=14)),
            on_click=self._handle_crear_migracion,
        )

        self.btn_ejecutar_migraciones = ft.ElevatedButton(
            content="Ejecutar Migraciones (migrate)",
            icon=ft.Icons.PLAY_ARROW_ROUNDED,
            style=ft.ButtonStyle(
                padding=ft.Padding.symmetric(horizontal=18, vertical=14),
                bgcolor=ft.Colors.GREEN_700,
                color=ft.Colors.WHITE,
            ),
            on_click=self._handle_ejecutar_migraciones,
        )

        # Tabla de Migraciones
        self.tabla_migraciones = ft.DataTable(
            heading_row_color=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            heading_row_height=38,
            data_row_min_height=34,
            columns=[
                ft.DataColumn(ft.Text("Estado", weight=ft.FontWeight.BOLD, size=11)),
                ft.DataColumn(ft.Text("Migración", weight=ft.FontWeight.BOLD, size=11)),
                ft.DataColumn(ft.Text("Lote", weight=ft.FontWeight.BOLD, size=11), numeric=True),
                ft.DataColumn(ft.Text("Ejecutado Por", weight=ft.FontWeight.BOLD, size=11)),
                ft.DataColumn(ft.Text("Fecha de Ejecución", weight=ft.FontWeight.BOLD, size=11)),
            ],
            rows=[],
        )

        self._construir_interfaz()
        self.actualizar_estado_migraciones()

    def _construir_interfaz(self):
        # 1. Tarjeta Conexión
        card_conexion = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.STORAGE_ROUNDED, color=ft.Colors.BLUE_400),
                            ft.Text("Conexión a SQL Server, Controlador y Credenciales", size=15, weight=ft.FontWeight.BOLD),
                        ],
                        spacing=8,
                    ),
                    ft.Row(controls=[self.dropdown_driver, self.txt_driver], spacing=12),
                    ft.Row(controls=[self.txt_server, self.txt_database, self.txt_operador], spacing=12),
                    self.switch_trusted,
                    ft.Row(controls=[self.txt_db_user, self.txt_db_pass], spacing=12),
                    ft.Row(
                        controls=[
                            ft.OutlinedButton(
                                content="Probar Conexión",
                                icon=ft.Icons.NETWORK_CHECK,
                                style=ft.ButtonStyle(padding=ft.Padding.symmetric(horizontal=16, vertical=14)),
                                on_click=self._handle_probar_conexion,
                            ),
                            ft.ElevatedButton(
                                content="Guardar Configuración",
                                icon=ft.Icons.SAVE_OUTLINED,
                                style=ft.ButtonStyle(
                                    padding=ft.Padding.symmetric(horizontal=20, vertical=14),
                                    bgcolor=ft.Colors.BLUE_700,
                                    color=ft.Colors.WHITE,
                                ),
                                on_click=self._handle_guardar_configuracion,
                            ),
                        ],
                        spacing=12,
                    ),
                ],
                spacing=12,
            ),
            padding=ft.Padding.all(16),
            border_radius=ft.BorderRadius.all(10),
            bgcolor=ft.Colors.SURFACE,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        )

        # 2. Tarjeta Parámetros Profit
        card_profit = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.SETTINGS_APPLICATIONS_ROUNDED, color=ft.Colors.AMBER_400),
                            ft.Text("Parámetros por Defecto para Artículos (Profit Plus)", size=15, weight=ft.FontWeight.BOLD),
                        ],
                        spacing=8,
                    ),
                    ft.Text(
                        "Valores de respaldo automático (fallback) únicamente si una fila del Excel no especifica Línea, Sublínea, Categoría, Color o Almacén.",
                        size=12,
                        color=ft.Colors.OUTLINE,
                    ),
                    ft.Row(
                        controls=[
                            self.txt_co_lin,
                            self.txt_co_subl,
                            self.txt_co_cat,
                            self.txt_co_color,
                            self.txt_co_alma,
                            self.txt_co_us_in,
                            self.txt_co_mone,
                        ],
                        wrap=True,
                        spacing=10,
                    ),
                ],
                spacing=10,
            ),
            padding=ft.Padding.all(16),
            border_radius=ft.BorderRadius.all(10),
            bgcolor=ft.Colors.SURFACE,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        )

        # 3. Tarjeta Migraciones
        card_migraciones = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.DYNAMIC_FEED_ROUNDED, color=ft.Colors.PURPLE_400),
                                    ft.Text("Gestión de Migraciones (Estilo Django)", size=15, weight=ft.FontWeight.BOLD),
                                ],
                                spacing=8,
                            ),
                            self.lbl_mig_resumen,
                        ],
                    ),
                    # Formulario makemigrations
                    ft.Row(
                        controls=[
                            self.txt_nueva_migracion,
                            self.btn_crear_migracion,
                            self.btn_ejecutar_migraciones,
                        ],
                        spacing=12,
                    ),
                    ft.Divider(height=6, color=ft.Colors.OUTLINE_VARIANT),
                    # Lista de migraciones
                    ft.Column(
                        controls=[
                            ft.Row(controls=[self.tabla_migraciones], scroll=ft.ScrollMode.ADAPTIVE),
                        ],
                        scroll=ft.ScrollMode.ADAPTIVE,
                        height=220,
                    ),
                ],
                spacing=12,
            ),
            padding=ft.Padding.all(16),
            border_radius=ft.BorderRadius.all(10),
            bgcolor=ft.Colors.SURFACE,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        )

        self.content = ft.Column(
            controls=[
                card_conexion,
                card_profit,
                card_migraciones,
            ],
            spacing=14,
            scroll=ft.ScrollMode.ADAPTIVE,
            expand=True,
        )

    def _on_driver_dropdown_change(self, e):
        if self.dropdown_driver.value:
            self.txt_driver.value = self.dropdown_driver.value
            try:
                self.txt_driver.update()
            except RuntimeError:
                pass

    def _toggle_auth_mode(self, e):
        es_trusted = self.switch_trusted.value
        self.txt_db_user.disabled = es_trusted
        self.txt_db_pass.disabled = es_trusted
        self.update()

    def _handle_probar_conexion(self, e):
        ok, msg = self.config_controller.probar_conexion(
            server=self.txt_server.value.strip(),
            database=self.txt_database.value.strip(),
            trusted_connection=self.switch_trusted.value,
            db_user=self.txt_db_user.value.strip(),
            db_password=self.txt_db_pass.value.strip(),
            driver=self.txt_driver.value.strip(),
        )
        self.on_notify(msg, ft.Colors.GREEN_400 if ok else ft.Colors.RED_400)

    def _handle_guardar_configuracion(self, e):
        nueva_config = {
            "sql_server": self.txt_server.value.strip(),
            "odbc_driver": self.txt_driver.value.strip(),
            "database": self.txt_database.value.strip(),
            "trusted_connection": self.switch_trusted.value,
            "db_user": self.txt_db_user.value.strip(),
            "db_password": self.txt_db_pass.value.strip(),
            "operador_usuario": self.txt_operador.value.strip() or "ADMIN",
            "profit_defaults": {
                "co_lin": self.txt_co_lin.value.strip(),
                "co_subl": self.txt_co_subl.value.strip(),
                "co_cat": self.txt_co_cat.value.strip(),
                "co_color": self.txt_co_color.value.strip(),
                "co_ubicacion": self.txt_co_alma.value.strip(),
                "co_us_in": self.txt_co_us_in.value.strip(),
                "co_mone": self.txt_co_mone.value.strip(),
                "tipo": "V",
                "tipo_imp": "1",
                "garantia": "n/a",
                "co_sucu_in": "01",
                "co_precio": "01",
                "alma_precio": self.txt_co_alma.value.strip(),
                "unidad_docena": "DOC",
                "unidad_pieza": "PZA",
                "factor_docena": 12.0,
                "factor_unidad": 1.0,
            },
        }

        ok, msg = self.config_controller.guardar_configuracion(
            nueva_config=nueva_config,
            operador=self.txt_operador.value.strip() or "ADMIN",
        )

        if ok:
            self.on_notify(msg, ft.Colors.GREEN_400)
            self.on_db_updated(self.txt_database.value.strip())
            self.actualizar_estado_migraciones()
        else:
            self.on_notify(msg, ft.Colors.RED_400)

    def _handle_crear_migracion(self, e):
        nombre = self.txt_nueva_migracion.value.strip()
        if not nombre:
            self.on_notify("Ingresa un nombre para la nueva migración.", ft.Colors.ORANGE_400)
            return

        try:
            archivo_creado = self.migration_controller.crear_nueva_migracion(nombre)
            self.txt_nueva_migracion.value = ""
            self.actualizar_estado_migraciones()
            self.on_notify(f"Migración creada: migraciones/{archivo_creado}", ft.Colors.GREEN_400)
        except Exception as err:
            self.on_notify(f"Error al crear migración: {str(err)}", ft.Colors.RED_400)

    def _handle_ejecutar_migraciones(self, e):
        operador = self.txt_operador.value.strip() or "ADMIN"
        ok, ejecutadas, errores = self.migration_controller.ejecutar_migraciones(
            operador_usuario=operador,
            database_name=self.txt_database.value.strip(),
        )

        self.actualizar_estado_migraciones()
        if ok and ejecutadas:
            self.on_notify(f"¡Migraciones aplicadas con éxito!: {', '.join(ejecutadas)}", ft.Colors.GREEN_400)
        elif not ejecutadas and not errores:
            self.on_notify("La base de datos ya se encuentra al día. No había pendientes.", ft.Colors.BLUE_400)
        else:
            msg_err = errores[0] if errores else "Fallo durante las migraciones."
            self.on_notify(msg_err, ft.Colors.RED_400)

    def actualizar_estado_migraciones(self):
        """Consulta el estado de migraciones y refresca la tabla."""
        estado = self.migration_controller.obtener_estado_migraciones(
            self.txt_database.value.strip()
        )
        aplicadas = estado["aplicadas"]
        pendientes = estado["pendientes"]
        total_disco = estado["total_disco"]

        nombres_aplicadas = {m["nombre"] for m in aplicadas}
        cant_pendientes = len(pendientes)
        cant_aplicadas = len(aplicadas)

        self.lbl_mig_resumen.value = f"{cant_aplicadas} aplicadas / {cant_pendientes} pendientes (Total: {total_disco})"
        self.btn_ejecutar_migraciones.disabled = cant_pendientes == 0

        filas = []

        # 1. Agregar filas aplicadas
        for m in aplicadas:
            filas.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(
                            ft.Container(
                                content=ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.CHECK_CIRCLE, size=13, color=ft.Colors.GREEN_400),
                                        ft.Text("Aplicada", size=11, color=ft.Colors.GREEN_400, weight=ft.FontWeight.BOLD),
                                    ],
                                    spacing=4,
                                ),
                                bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.GREEN),
                                padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                                border_radius=ft.BorderRadius.all(10),
                            )
                        ),
                        ft.DataCell(ft.Text(m.get("nombre", ""), weight=ft.FontWeight.W_500, size=12)),
                        ft.DataCell(ft.Text(str(m.get("lote", 1)), size=11)),
                        ft.DataCell(ft.Text(m.get("ejecutado_por", "ADMIN"), size=11)),
                        ft.DataCell(ft.Text(str(m.get("fecha_hora", ""))[:19], size=11, color=ft.Colors.OUTLINE)),
                    ]
                )
            )

        # 2. Agregar filas pendientes
        for p in pendientes:
            filas.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(
                            ft.Container(
                                content=ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.SCHEDULE, size=13, color=ft.Colors.ORANGE_400),
                                        ft.Text("Pendiente", size=11, color=ft.Colors.ORANGE_400, weight=ft.FontWeight.BOLD),
                                    ],
                                    spacing=4,
                                ),
                                bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.ORANGE),
                                padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                                border_radius=ft.BorderRadius.all(10),
                            )
                        ),
                        ft.DataCell(ft.Text(p, weight=ft.FontWeight.W_500, size=12, italic=True)),
                        ft.DataCell(ft.Text("-", size=11)),
                        ft.DataCell(ft.Text("-", size=11)),
                        ft.DataCell(ft.Text("Por aplicar en disco", size=11, color=ft.Colors.OUTLINE)),
                    ]
                )
            )

        self.tabla_migraciones.rows = filas
        try:
            self.update()
        except RuntimeError:
            pass
