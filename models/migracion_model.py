"""
Modelo para la tabla de control de migraciones en SQL Server.
Permite rastrear cada migración ejecutada de forma atómica y auditable.
"""

from typing import List, Dict, Set, Optional
from models.database_model import DatabaseModel


class MigracionModel:
    def __init__(self, db_model: DatabaseModel):
        self.db_model = db_model

    def asegurar_tabla(self, database_name: Optional[str] = None) -> bool:
        """Crea la tabla migraciones en la base de datos seleccionada si no existe."""
        ddl = """
        IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'migraciones')
        BEGIN
            CREATE TABLE migraciones (
                id INT IDENTITY(1,1) PRIMARY KEY,
                nombre VARCHAR(255) NOT NULL UNIQUE,
                lote INT NOT NULL,
                ejecutado_por VARCHAR(100) NOT NULL,
                fecha_hora DATETIME DEFAULT GETDATE(),
                descripcion NVARCHAR(MAX) NULL,
                estado VARCHAR(20) NOT NULL DEFAULT 'exitoso'
            );
            CREATE INDEX idx_migraciones_nombre ON migraciones(nombre);
        END
        """
        try:
            with self.db_model.get_connection(database_name) as conn:
                cursor = conn.cursor()
                cursor.execute(ddl)
                conn.commit()
                return True
        except Exception as err:
            print(f"Error al asegurar tabla migraciones: {err}")
            return False

    def listar_ejecutadas(self, database_name: Optional[str] = None) -> List[Dict]:
        """Obtiene la lista de migraciones registradas en la base de datos."""
        self.asegurar_tabla(database_name)
        sql = "SELECT id, nombre, lote, ejecutado_por, fecha_hora, descripcion, estado FROM migraciones ORDER BY id ASC"
        try:
            with self.db_model.get_connection(database_name) as conn:
                cursor = conn.cursor()
                cursor.execute(sql)
                columnas = [col[0].lower() for col in cursor.description]
                filas = [dict(zip(columnas, row)) for row in cursor.fetchall()]
                return filas
        except Exception as err:
            print(f"Error al listar migraciones ejecutadas: {err}")
            return []

    def obtener_nombres_ejecutadas(self, database_name: Optional[str] = None) -> Set[str]:
        """Obtiene el conjunto de nombres de migraciones ya aplicadas."""
        ejecutadas = self.listar_ejecutadas(database_name)
        return {m["nombre"] for m in ejecutadas if m.get("estado") == "exitoso"}

    def siguiente_lote(self, database_name: Optional[str] = None) -> int:
        """Calcula el número del siguiente lote (batch) de ejecución."""
        self.asegurar_tabla(database_name)
        sql = "SELECT ISNULL(MAX(lote), 0) + 1 FROM migraciones"
        try:
            with self.db_model.get_connection(database_name) as conn:
                cursor = conn.cursor()
                cursor.execute(sql)
                row = cursor.fetchone()
                return int(row[0]) if row and row[0] else 1
        except Exception as err:
            print(f"Error al obtener siguiente lote: {err}")
            return 1

    def registrar(
        self,
        nombre: str,
        lote: int,
        ejecutado_por: str,
        descripcion: str = "",
        estado: str = "exitoso",
        database_name: Optional[str] = None,
    ) -> bool:
        """Inserta el registro de una migración ejecutada."""
        sql = """
        INSERT INTO migraciones (nombre, lote, ejecutado_por, fecha_hora, descripcion, estado)
        VALUES (?, ?, ?, GETDATE(), ?, ?);
        """
        try:
            with self.db_model.get_connection(database_name) as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (nombre, lote, ejecutado_por, descripcion, estado))
                conn.commit()
                return True
        except Exception as err:
            print(f"Error al registrar migración {nombre}: {err}")
            return False
