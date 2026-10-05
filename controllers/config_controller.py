"""
Controlador de configuración para MasivoProfit.
Gestiona la prueba y guardado de parámetros de base de datos, usuario operador y Profit Plus.
"""

from typing import Dict, Any, Tuple
import pyodbc
from models.config_model import ConfigModel
from models.database_model import DatabaseModel
from models.auditoria_model import registrar_auditoria


class ConfigController:
    def __init__(self, db_model: DatabaseModel):
        self.db_model = db_model
        self.config_data = ConfigModel.cargar()

    def obtener_configuracion(self) -> Dict[str, Any]:
        """Retorna los datos de configuración actuales."""
        return self.config_data

    def probar_conexion(
        self,
        server: str,
        database: str,
        trusted_connection: bool,
        db_user: str = "",
        db_password: str = "",
        driver: str = "",
    ) -> Tuple[bool, str]:
        """Prueba una conexión a SQL Server con los parámetros y driver indicados."""
        driver_usar = driver.strip() if driver else self.db_model.driver
        conn_str = f"Driver={{{driver_usar}}};Server={server};"
        if database:
            conn_str += f"Database={database};"
        if trusted_connection:
            conn_str += "Trusted_Connection=yes;"
        else:
            if not db_user:
                return False, "Debes especificar el usuario de SQL Server."
            conn_str += f"UID={db_user};PWD={db_password};"

        try:
            with pyodbc.connect(conn_str, timeout=5) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT @@VERSION")
                ver = cursor.fetchone()
                return True, f"Conexión exitosa a SQL Server con '{driver_usar}' ({ver[0][:30]}...)"
        except Exception as err:
            return False, f"Fallo al conectar: {str(err)}"

    def guardar_configuracion(
        self,
        nueva_config: Dict[str, Any],
        operador: str = "ADMIN",
    ) -> Tuple[bool, str]:
        """Guarda la configuración y actualiza el modelo de base de datos en caliente."""
        exito = ConfigModel.guardar(nueva_config)
        if exito:
            self.config_data = nueva_config

            # Actualizar DatabaseModel en caliente
            self.db_model.driver = nueva_config.get("odbc_driver", self.db_model.driver)
            self.db_model.server = nueva_config.get("sql_server", self.db_model.server)
            self.db_model.trusted_connection = nueva_config.get("trusted_connection", True)
            self.db_model.username = nueva_config.get("db_user", "")
            self.db_model.password = nueva_config.get("db_password", "")
            if nueva_config.get("database"):
                self.db_model.set_active_database(nueva_config.get("database"))

            # Auditar el cambio de configuración
            registrar_auditoria(
                modulo="configuracion",
                tipo_accion="UPDATE",
                descripcion=f"Actualización de parámetros de configuración y credenciales por el usuario: {operador}.",
                usuario_id=operador,
                db_model=self.db_model,
            )

            return True, "Configuración guardada exitosamente."
        return False, "Error al escribir el archivo de configuración."
