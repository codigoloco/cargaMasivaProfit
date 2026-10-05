"""
Modelo y función estándar para registro de auditoría en MasivoProfit.
Garantiza trazabilidad de todas las operaciones transaccionales y de usuario.
"""

from typing import Optional
from models.database_model import DatabaseModel

# Variable global para mantener referencia al modelo de BD activo
_GLOBAL_DB_MODEL: Optional[DatabaseModel] = None


def set_global_db_model(db_model: DatabaseModel):
    """Establece el modelo de base de datos para la auditoría global."""
    global _GLOBAL_DB_MODEL
    _GLOBAL_DB_MODEL = db_model


class AuditoriaModel:
    def __init__(self, db_model: DatabaseModel):
        self.db_model = db_model

    def asegurar_tabla_auditoria(self, database_name: Optional[str] = None) -> bool:
        """Crea o ajusta de forma segura e idempotente la tabla auditoria."""
        ddl = """
        IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'auditoria')
        BEGIN
            CREATE TABLE auditoria (
                id INT IDENTITY(1,1) PRIMARY KEY,
                fecha_hora DATETIME DEFAULT GETDATE(),
                modulo VARCHAR(100) NOT NULL,
                tipo_accion VARCHAR(50) NOT NULL,
                usuario_id VARCHAR(100) NULL,
                descripcion NVARCHAR(MAX) NOT NULL,
                registro_id VARCHAR(255) NULL,
                ip_origen VARCHAR(45) NULL
            );
        END
        ELSE
        BEGIN
            IF EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'auditoria' AND COLUMN_NAME = 'registro_id' AND (CHARACTER_MAXIMUM_LENGTH < 255 OR CHARACTER_MAXIMUM_LENGTH IS NULL))
            BEGIN
                ALTER TABLE auditoria ALTER COLUMN registro_id VARCHAR(255) NULL;
            END
            IF EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'auditoria' AND COLUMN_NAME = 'tipo_accion' AND CHARACTER_MAXIMUM_LENGTH < 50)
            BEGIN
                ALTER TABLE auditoria ALTER COLUMN tipo_accion VARCHAR(50) NOT NULL;
            END
            IF EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'auditoria' AND COLUMN_NAME = 'usuario_id' AND CHARACTER_MAXIMUM_LENGTH < 100)
            BEGIN
                ALTER TABLE auditoria ALTER COLUMN usuario_id VARCHAR(100) NULL;
            END
        END
        """
        try:
            with self.db_model.get_connection(database_name) as conn:
                cursor = conn.cursor()
                cursor.execute(ddl)
                conn.commit()
                return True
        except Exception as err:
            print(f"Error al verificar/crear tabla auditoria: {err}")
            return False

    def registrar(
        self,
        modulo: str,
        tipo_accion: str,
        descripcion: str,
        registro_id: Optional[str] = None,
        usuario_id: Optional[str] = "ADMIN",
        ip_origen: Optional[str] = "127.0.0.1",
        database_name: Optional[str] = None,
    ) -> bool:
        """Registra un evento transaccional en la tabla auditoria protegiendo longitudes."""
        sql = """
        INSERT INTO auditoria (modulo, tipo_accion, descripcion, registro_id, usuario_id, ip_origen, fecha_hora)
        VALUES (?, ?, ?, ?, ?, ?, GETDATE());
        """
        try:
            mod_val = str(modulo).strip().lower()[:100]
            act_val = str(tipo_accion).strip().upper()[:50]
            desc_val = str(descripcion)
            reg_val = str(registro_id).strip()[:255] if registro_id is not None else None
            usr_val = str(usuario_id).strip()[:100] if usuario_id is not None else "ADMIN"
            ip_val = str(ip_origen).strip()[:45] if ip_origen is not None else "127.0.0.1"

            with self.db_model.get_connection(database_name) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    sql,
                    (
                        mod_val,
                        act_val,
                        desc_val,
                        reg_val,
                        usr_val,
                        ip_val,
                    ),
                )
                conn.commit()
                return True
        except Exception as err:
            print(f"Error al registrar auditoria: {err}")
            return False


def registrar_auditoria(
    modulo: str,
    tipo_accion: str,
    descripcion: str,
    registro_id: Optional[str] = None,
    usuario_id: Optional[str] = "ADMIN",
    ip_origen: Optional[str] = "127.0.0.1",
    db_model: Optional[DatabaseModel] = None,
) -> bool:
    """
    Función global obligatoria para auditar cualquier acción, cambio de estado
    o proceso transaccional en el sistema.
    """
    target_model = db_model or _GLOBAL_DB_MODEL
    if not target_model:
        print("Aviso: No se puede registrar auditoría porque no hay base de datos configurada.")
        return False

    auditoria_service = AuditoriaModel(target_model)
    return auditoria_service.registrar(
        modulo=modulo,
        tipo_accion=tipo_accion,
        descripcion=descripcion,
        registro_id=registro_id,
        usuario_id=usuario_id,
        ip_origen=ip_origen,
    )
