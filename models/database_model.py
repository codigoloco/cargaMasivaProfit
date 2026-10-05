"""
Modelo para la gestión de conexiones a Microsoft SQL Server mediante pyodbc.
Aplica principios SOLID (Responsabilidad Única e Inversión de Dependencias).
"""

import pyodbc
from typing import List, Optional
from config import DEFAULT_SQL_SERVER, DEFAULT_ODBC_DRIVER, DEFAULT_TRUSTED_CONNECTION


class DatabaseModel:
    def __init__(
        self,
        server: str = DEFAULT_SQL_SERVER,
        driver: str = DEFAULT_ODBC_DRIVER,
        trusted_connection: bool = DEFAULT_TRUSTED_CONNECTION,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self.server = server
        self.driver = driver
        self.trusted_connection = trusted_connection
        self.username = username
        self.password = password
        self.active_database: Optional[str] = None

    def build_connection_string(self, database: Optional[str] = None) -> str:
        """Construye la cadena de conexión ODBC con soporte para Trusted o SQL Auth."""
        conn_str = f"Driver={{{self.driver}}};Server={self.server};"
        if database:
            conn_str += f"Database={database};"
        if self.trusted_connection:
            conn_str += "Trusted_Connection=yes;"
        else:
            if self.username:
                conn_str += f"UID={self.username};"
            if self.password:
                conn_str += f"PWD={self.password};"
        return conn_str

    def get_connection(self, database: Optional[str] = None) -> pyodbc.Connection:
        """Obtiene un objeto de conexión activo a la base de datos."""
        target_db = database or self.active_database
        conn_str = self.build_connection_string(target_db)
        return pyodbc.connect(conn_str, autocommit=False)

    def list_databases(self) -> List[str]:
        """Obtiene el listado de bases de datos de usuario disponibles en la instancia."""
        system_dbs = ("master", "tempdb", "model", "msdb")
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name FROM sys.databases WHERE state_desc = 'ONLINE' ORDER BY name ASC"
                )
                databases = [
                    row[0]
                    for row in cursor.fetchall()
                    if row[0].lower() not in system_dbs
                ]
                return databases
        except Exception as err:
            print(f"Error al listar bases de datos: {err}")
            return []

    def set_active_database(self, database_name: str) -> bool:
        """Establece la base de datos activa tras validar conexión."""
        try:
            with self.get_connection(database_name) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                self.active_database = database_name
                return True
        except Exception as err:
            print(f"Error al cambiar a la base de datos {database_name}: {err}")
            return False
