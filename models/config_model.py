"""
Modelo de configuración y persistencia local para MasivoProfit.
Gestiona el archivo config.json con parámetros de conexión, usuario operador y Profit Plus.
"""

import os
import json
from typing import Dict, Any
from config import DEFAULT_SQL_SERVER, DEFAULT_ODBC_DRIVER, DEFAULT_TRUSTED_CONNECTION, PROFIT_DEFAULTS

CONFIG_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")


class ConfigModel:
    @staticmethod
    def obtener_configuracion_predeterminada() -> Dict[str, Any]:
        return {
            "sql_server": DEFAULT_SQL_SERVER,
            "odbc_driver": DEFAULT_ODBC_DRIVER,
            "database": "DEMOA",
            "trusted_connection": DEFAULT_TRUSTED_CONNECTION,
            "db_user": "",
            "db_password": "",
            "operador_usuario": "ADMIN",
            "profit_defaults": dict(PROFIT_DEFAULTS),
        }

    @staticmethod
    def cargar() -> Dict[str, Any]:
        """Carga la configuración desde config.json o crea los valores por defecto."""
        defaults = ConfigModel.obtener_configuracion_predeterminada()
        if not os.path.exists(CONFIG_FILE_PATH):
            ConfigModel.guardar(defaults)
            return defaults

        try:
            with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
                datos = json.load(f)
                # Asegurar que todas las claves requeridas existan
                for k, v in defaults.items():
                    if k not in datos:
                        datos[k] = v
                return datos
        except Exception as err:
            print(f"Error al leer config.json: {err}. Usando valores predeterminados.")
            return defaults

    @staticmethod
    def guardar(datos: Dict[str, Any]) -> bool:
        """Guarda la configuración en config.json."""
        try:
            with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(datos, f, indent=4, ensure_ascii=False)
            return True
        except Exception as err:
            print(f"Error al guardar config.json: {err}")
            return False
