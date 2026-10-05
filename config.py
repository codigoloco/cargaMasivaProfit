"""
Configuraciones globales y parámetros predeterminados para MasivoProfit.
"""

import os

# Configuración del servidor SQL Server
DEFAULT_SQL_SERVER = os.environ.get("SQL_SERVER", r"localhost\SQLEXPRESS")
DEFAULT_ODBC_DRIVER = os.environ.get("ODBC_DRIVER", "ODBC Driver 17 for SQL Server")
DEFAULT_TRUSTED_CONNECTION = True

# Valores por defecto para inserciones en Profit Plus
PROFIT_DEFAULTS = {
    "co_lin": "006",
    "co_subl": "012",
    "co_cat": "001",
    "co_color": "001",
    "co_ubicacion": "ALM",
    "cod_proc": "001",
    "tipo": "V",
    "tipo_imp": "1",
    "garantia": "n/a",
    "co_us_in": "001",
    "co_sucu_in": "01",
    "co_precio": "01",
    "co_mone": "USD",
    "alma_precio": "01",
    "unidad_docena": "DOC",
    "unidad_pieza": "PZA",
    "factor_docena": 12.0,
    "factor_unidad": 1.0,
}

# Configuración de apariencia
APP_TITLE = "MasivoProfit - Carga Masiva de Inventario"
DEFAULT_WINDOW_WIDTH = 1200
DEFAULT_WINDOW_HEIGHT = 800
