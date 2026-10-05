"""
Migración 0001_initial
Generado con estructura estándar estilo Django.
Crea las tablas base de auditoría y migraciones en la base de datos de Profit Plus.
"""

dependencies = []

operations = [
    """
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
    """,
    """
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
    """,
]


def up(cursor):
    """Aplica las sentencias de la migración."""
    for sql in operations:
        cursor.execute(sql)


def down(cursor):
    """Revierte las sentencias de la migración si aplica."""
    cursor.execute("DROP TABLE IF EXISTS migraciones;")
    cursor.execute("DROP TABLE IF EXISTS auditoria;")
