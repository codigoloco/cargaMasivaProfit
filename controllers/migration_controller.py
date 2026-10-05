"""
Controlador del sistema de migraciones para MasivoProfit.
Gestiona el descubrimiento, ejecución secuencial (migrate) y creación (makemigrations)
siguiendo la estructura estándar de Django.
"""

import os
import re
import importlib
from typing import List, Dict, Tuple, Optional
from models.migracion_model import MigracionModel
from models.auditoria_model import registrar_auditoria

_MIGRACIONES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "migraciones")
_PATRON_ARCHIVO = re.compile(r"^(\d{4})_(.+)\.py$")


class MigrationController:
    def __init__(self, migracion_model: MigracionModel):
        self.migracion_model = migracion_model

    def listar_migraciones_disco(self) -> List[str]:
        """Escanea la carpeta migraciones/ y retorna los nombres ordenados correlativamente."""
        if not os.path.exists(_MIGRACIONES_DIR):
            os.makedirs(_MIGRACIONES_DIR, exist_ok=True)

        archivos = []
        for f in os.listdir(_MIGRACIONES_DIR):
            match = _PATRON_ARCHIVO.match(f)
            if match:
                nombre_modulo = f[:-3]  # Quitar .py
                archivos.append(nombre_modulo)

        # Ordenar naturalmente por el prefijo numérico (0001, 0002, ...)
        return sorted(archivos)

    def obtener_estado_migraciones(self, database_name: Optional[str] = None) -> Dict:
        """
        Retorna el estado completo:
        - aplicadas: lista de migraciones registradas en BD
        - pendientes: lista de migraciones en disco pendientes por aplicar
        """
        self.migracion_model.asegurar_tabla(database_name)
        aplicadas = self.migracion_model.listar_ejecutadas(database_name)
        nombres_aplicadas = {m["nombre"] for m in aplicadas if m.get("estado") == "exitoso"}

        disco = self.listar_migraciones_disco()
        pendientes = [m for m in disco if m not in nombres_aplicadas]

        return {
            "aplicadas": aplicadas,
            "pendientes": pendientes,
            "total_disco": len(disco),
        }

    def ejecutar_migraciones(
        self,
        operador_usuario: str = "ADMIN",
        database_name: Optional[str] = None,
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Aplica todas las migraciones pendientes en orden secuencial dentro de SQL Server.
        Registra cada una en la tabla migraciones y audita el proceso.
        """
        estado = self.obtener_estado_migraciones(database_name)
        pendientes = estado["pendientes"]

        if not pendientes:
            return True, [], ["No hay migraciones pendientes. La base de datos está al día."]

        lote = self.migracion_model.siguiente_lote(database_name)
        ejecutadas: List[str] = []
        errores: List[str] = []

        try:
            with self.migracion_model.db_model.get_connection(database_name) as conn:
                cursor = conn.cursor()

                for nombre_migracion in pendientes:
                    try:
                        # Importar dinámicamente el módulo de la migración
                        modulo = importlib.import_module(f"migraciones.{nombre_migracion}")
                        # Forzar recarga si ya estaba en caché
                        importlib.reload(modulo)

                        funcion_up = getattr(modulo, "up", None)
                        if not callable(funcion_up):
                            raise AttributeError(f"La migración '{nombre_migracion}' no define una función up(cursor).")

                        # Ejecutar migración
                        funcion_up(cursor)

                        # Registrar en tabla migraciones
                        self.migracion_model.registrar(
                            nombre=nombre_migracion,
                            lote=lote,
                            ejecutado_por=operador_usuario,
                            descripcion="Migración aplicada exitosamente.",
                            estado="exitoso",
                            database_name=database_name,
                        )
                        ejecutadas.append(nombre_migracion)

                    except Exception as err_mig:
                        error_msg = f"Error en '{nombre_migracion}': {str(err_mig)}"
                        print(error_msg)
                        self.migracion_model.registrar(
                            nombre=nombre_migracion,
                            lote=lote,
                            ejecutado_por=operador_usuario,
                            descripcion=error_msg,
                            estado="error",
                            database_name=database_name,
                        )
                        errores.append(error_msg)
                        conn.rollback()
                        break

                if not errores:
                    conn.commit()

            # Auditar la ejecución de migraciones
            if ejecutadas:
                registrar_auditoria(
                    modulo="migraciones",
                    tipo_accion="MIGRATE",
                    descripcion=f"Ejecución de Lote {lote}: {len(ejecutadas)} migraciones aplicadas ({', '.join(ejecutadas)}).",
                    registro_id=f"LOTE_{lote}",
                    usuario_id=operador_usuario,
                    db_model=self.migracion_model.db_model,
                )

            return len(errores) == 0, ejecutadas, errores

        except Exception as err:
            return False, ejecutadas, [f"Error de conexión en migraciones: {str(err)}"]

    def crear_nueva_migracion(
        self,
        nombre_descriptivo: str,
        sentencias_sql: Optional[List[str]] = None,
    ) -> str:
        """
        Crea un nuevo archivo de migración con estructura correlativa estilo Django (makemigrations).
        Ejemplo: 0002_agregar_columna.py
        """
        limpio = re.sub(r"[^\w]+", "_", nombre_descriptivo.strip().lower()).strip("_")
        if not limpio:
            limpio = "auto_migracion"

        disco = self.listar_migraciones_disco()
        if disco:
            ultimo_nombre = disco[-1]
            ultimo_numero = int(ultimo_nombre[:4])
            nuevo_numero = f"{ultimo_numero + 1:04d}"
            dependencia_previa = f"['{ultimo_nombre}']"
        else:
            nuevo_numero = "0001"
            dependencia_previa = "[]"

        nombre_archivo = f"{nuevo_numero}_{limpio}.py"
        ruta_archivo = os.path.join(_MIGRACIONES_DIR, nombre_archivo)

        operaciones_str = ""
        if sentencias_sql:
            for sql in sentencias_sql:
                operaciones_str += f'    """{sql.strip()}""",\n'
        else:
            operaciones_str = '    # Escribe aquí tus sentencias SQL DDL o DML:\n    # """CREATE TABLE ejemplo (...);""",\n'

        plantilla = f'''"""
Migración {nuevo_numero}_{limpio}
Generado por el sistema de migraciones MasivoProfit.
"""

dependencies = {dependencia_previa}

operations = [
{operaciones_str}]


def up(cursor):
    """Sentencias SQL para aplicar la migración."""
    for sql in operations:
        cursor.execute(sql)


def down(cursor):
    """Sentencias SQL para revertir la migración si aplica."""
    pass
'''
        with open(ruta_archivo, "w", encoding="utf-8") as f:
            f.write(plantilla)

        return nombre_archivo
