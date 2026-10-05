"""
Controlador principal de la aplicación MasivoProfit.
Orquesta los modelos, la configuración y el estado global.
"""

import os
from typing import List, Dict, Optional, Tuple
from models.database_model import DatabaseModel
from models.auditoria_model import AuditoriaModel, set_global_db_model, registrar_auditoria
from models.articulo_model import ArticuloModel
from models.migracion_model import MigracionModel
from models.config_model import ConfigModel
from controllers.import_controller import ImportController
from controllers.template_controller import TemplateController
from controllers.config_controller import ConfigController
from controllers.migration_controller import MigrationController


class AppController:
    def __init__(self):
        # Cargar configuración persistente
        self.config_data = ConfigModel.cargar()

        self.db_model = DatabaseModel(
            server=self.config_data.get("sql_server", r"localhost\SQLEXPRESS"),
            trusted_connection=self.config_data.get("trusted_connection", True),
            username=self.config_data.get("db_user", ""),
            password=self.config_data.get("db_password", ""),
        )
        self.auditoria_model = AuditoriaModel(self.db_model)
        self.articulo_model = ArticuloModel(self.db_model)
        self.migracion_model = MigracionModel(self.db_model)

        self.import_controller = ImportController(self.articulo_model)
        self.template_controller = TemplateController(self.articulo_model)
        self.config_controller = ConfigController(self.db_model)
        self.migration_controller = MigrationController(self.migracion_model)

        # Estado global
        self.bases_datos: List[str] = []
        self.base_datos_activa: Optional[str] = None
        self.articulos_cargados: List[Dict] = []
        self.resumen_carga: Dict = {
            "total": 0,
            "validos": 0,
            "errores": 0,
            "docenas": 0,
            "unidades": 0,
        }
        self.filtro_busqueda: str = ""

    def inicializar_sistema(self) -> Tuple[bool, str]:
        """Carga las bases de datos y selecciona la configurada o disponible."""
        try:
            self.bases_datos = self.db_model.list_databases()
            if not self.bases_datos:
                return False, "No se detectaron bases de datos de usuario en SQL Server."

            # Preferir la configurada si existe, sino DEMOA, sino la primera
            bd_configurada = self.config_data.get("database", "DEMOA")
            db_inicial = (
                bd_configurada
                if bd_configurada in self.bases_datos
                else ("DEMOA" if "DEMOA" in self.bases_datos else self.bases_datos[0])
            )
            self.cambiar_base_datos(db_inicial)
            return True, f"Conectado exitosamente a SQL Server. BD activa: {db_inicial}"
        except Exception as err:
            return False, f"Error al inicializar conexión: {str(err)}"

    def cambiar_base_datos(self, nombre_bd: str) -> bool:
        """Cambia la base de datos de trabajo, asegura auditoría y audita el cambio."""
        exito = self.db_model.set_active_database(nombre_bd)
        if exito:
            self.base_datos_activa = nombre_bd
            self.config_data["database"] = nombre_bd
            set_global_db_model(self.db_model)
            # Asegurar tabla auditoria y migraciones en la BD
            self.auditoria_model.asegurar_tabla_auditoria(nombre_bd)
            self.migracion_model.asegurar_tabla(nombre_bd)
            # Registrar auditoría de inicio/cambio de contexto
            operador = self.config_data.get("operador_usuario", "ADMIN")
            registrar_auditoria(
                modulo="sistema",
                tipo_accion="CAMBIO_BD",
                descripcion=f"Selección de base de datos activa: {nombre_bd}",
                registro_id=nombre_bd,
                db_model=self.db_model,
            )
            # Si ya había artículos cargados, reanalizar contra la nueva BD
            if self.articulos_cargados:
                self.revalidar_articulos()
            return True
        return False

    def cargar_archivo(self, ruta_archivo: str) -> Dict:
        """Procesa y valida un archivo cargado."""
        resultado = self.import_controller.analizar_archivo(ruta_archivo)
        self.articulos_cargados = resultado["articulos"]
        self.resumen_carga = resultado["resumen"]

        # Auditar la carga del archivo para revisión
        nombre_base = os.path.basename(ruta_archivo.replace("\\", "/"))
        registrar_auditoria(
            modulo="inventario",
            tipo_accion="CARGA_ARCHIVO",
            descripcion=(
                f"Análisis de archivo para carga masiva: {resultado['resumen']['total']} registros analizados "
                f"({resultado['resumen']['validos']} válidos, {resultado['resumen']['errores']} errores, "
                f"{resultado['resumen']['docenas']} docenas, {resultado['resumen']['unidades']} unidades)."
            ),
            registro_id=nombre_base[:255],
            db_model=self.db_model,
        )

        return resultado

    def revalidar_articulos(self):
        """Revalida los artículos en memoria (por ejemplo al cambiar de BD)."""
        if not self.articulos_cargados:
            return

        todos_codigos = [art["codigo"] for art in self.articulos_cargados if art.get("codigo")]
        codigos_existentes_bd = self.articulo_model.obtener_articulos_existentes(todos_codigos)

        codigos_vistos_lote = set()
        total_validos = 0
        total_errores = 0

        for art in self.articulos_cargados:
            codigo = art.get("codigo", "")
            from utils.validators import validar_articulo

            es_valido, estado_visual, mensaje = validar_articulo(
                art=art,
                codigos_existentes_bd=codigos_existentes_bd,
                codigos_vistos_lote=codigos_vistos_lote,
            )
            if codigo and es_valido:
                codigos_vistos_lote.add(codigo)

            art["es_valido"] = es_valido
            art["estado"] = estado_visual
            art["mensaje_estado"] = mensaje

            if es_valido:
                total_validos += 1
            else:
                total_errores += 1

        self.resumen_carga["validos"] = total_validos
        self.resumen_carga["errores"] = total_errores

    def procesar_lote_actual(self, callback_progreso=None) -> Tuple[bool, int, List[str]]:
        """Ejecuta la inserción masiva en la BD activa firmada por el operador configurado con progreso en tiempo real."""
        operador = self.config_data.get("operador_usuario", "ADMIN")
        exito, insertados, errores = self.import_controller.ejecutar_carga_masiva(
            self.articulos_cargados,
            usuario_id=operador,
            callback_progreso=callback_progreso,
        )
        # Recalcular métricas
        total_validos = sum(1 for a in self.articulos_cargados if a.get("es_valido"))
        self.resumen_carga["validos"] = total_validos
        return exito, insertados, errores

    def verificar_existencia_articulos(self) -> Tuple[int, int]:
        """Consulta en tiempo real contra saArticulo y refresca el estado de todos los artículos."""
        existentes, no_existentes = self.articulo_model.verificar_estado_articulos(self.articulos_cargados)
        total_validos = sum(1 for a in self.articulos_cargados if a.get("es_valido"))
        self.resumen_carga["validos"] = total_validos
        self.resumen_carga["errores"] = len(self.articulos_cargados) - total_validos
        return existentes, no_existentes

    def obtener_articulos_filtrados(self) -> List[Dict]:
        """Retorna los artículos aplicando el filtro de búsqueda en mayúsculas."""
        if not self.filtro_busqueda:
            return self.articulos_cargados

        termino = self.filtro_busqueda.strip().upper()
        return [
            art
            for art in self.articulos_cargados
            if termino in art.get("codigo", "").upper()
            or termino in art.get("descripcion", "").upper()
            or termino in art.get("referencia", "").upper()
            or termino in art.get("modelo", "").upper()
        ]
