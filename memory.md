# Memoria del Proyecto - MasivoProfit

## 1. Descripción General
**MasivoProfit** es una aplicación de escritorio desarrollada en **Python con Flet**, diseñada para la gestión, validación y carga masiva de inventario hacia bases de datos de **Profit Plus Administrativo 2K8/2K12** sobre **Microsoft SQL Server**.

## 2. Pila Tecnológica y Dependencias
- **Lenguaje:** Python 3.14
- **Framework UI:** Flet (`flet 0.86.3`)
- **Motor de Base de Datos:** Microsoft SQL Server (Instancia `localhost\SQLEXPRESS`)
- **Conector BD:** `pyodbc` con `ODBC Driver 17 for SQL Server`
- **Manejo de Archivos:** `openpyxl` (Excel .xlsx), `pandas`
- **Patrón de Arquitectura:** MVC (Modelo - Vista - Controlador) aplicando principios SOLID

## 3. Reglas de Negocio y Estándares
1. **Auditoría Obligatoria:**
   - Toda operación transaccional, carga masiva o cambio de estado debe quedar registrado en la tabla `auditoria` de la base de datos de Profit seleccionada mediante la función `registrar_auditoria()`.
   - La tabla se crea de forma idempotente (`IF NOT EXISTS`) con columnas: `id`, `fecha_hora`, `modulo`, `tipo_accion`, `usuario_id`, `descripcion`, `registro_id`, `ip_origen`.
2. **Especificación de Unidades y Docenas:**
   - Todo producto y vista previa debe especificar claramente si se comercializa por **DOCENA** o por **UNIDAD** (preferencia por docenas).
   - En `saArtUnidad`, para DOCENA se registra la equivalencia en 12.0 y para UNIDAD en 1.0.
3. **Normalización de Datos:**
   - Todo match o comparación de códigos y nombres se realiza en mayúsculas (`UPPERCASE`) para evitar inconsistencias por diferencias de caso.
4. **Soporte de Tema:**
   - La interfaz soporta Modo Oscuro (Dark) y Modo Claro (Light) asegurando contraste y legibilidad.

## 4. Estructura de Tablas Profit Plus Involucradas
- **`saArticulo`:**
  - `co_art`: Código único del artículo (char 30, en mayúsculas).
  - `art_des`: Descripción del artículo (varchar 120, en mayúsculas).
  - `tipo`: `'V'` (Mercancía para la venta).
  - `modelo`, `ref`: Modelo y referencia comercial.
  - Campos por defecto requeridos por Profit Plus: `co_lin`, `co_subl`, `co_cat`, `co_color`, `co_ubicacion`, `tipo_imp`, `garantia`, `co_us_in`, `co_sucu_in`.
- **`saArtPrecio`:**
  - `co_art`: Relación con el artículo.
  - `co_precio`: `'01'` (Precio base).
  - `monto`: Precio 1.
  - `montoadi1` a `montoadi4`: Precios 2, 3, 4 y 5.
  - `co_mone`: Moneda `'USD'`.
  - Fechas de vigencia y usuario de inserción.
- **`saArtUnidad`:**
  - `co_art`: Código del artículo.
  - `co_uni`: `'DOC'` o `'UND'`.
  - `equivalencia`: 12.00000 para docena, 1.00000 para unidad.
  - `uni_principal`: `1`.

## 5. Registro de Cambios y Estado Actual
- **2026-10-05:**
  - Inicialización del proyecto y definición de estándares.
  - Plan de arquitectura MVC aprobado por el usuario.
  - Creación del archivo `memory.md`.
  - Configuración de `config.py` con parámetros validados en la BD `DEMOA` (líneas, categorías, almacén, unidades DOC y PZA).
  - Implementación de `models/database_model.py` (conexión ODBC a SQLEXPRESS, soporte para Windows Trusted y SQL Server Auth con usuario y clave).
  - Implementación de `models/config_model.py` y archivo persistente `config.json`.
  - Implementación de `models/auditoria_model.py` (creación idempotente de tabla `auditoria` y función estándar `registrar_auditoria`).
  - Implementación de `models/articulo_model.py` (inserción atómica en `saArticulo`, `saArtPrecio` y `saArtUnidad` con soporte dual docena/unidad y factor 12 o 1).
  - Implementación de `utils/validators.py` y `utils/excel_helper.py` (validaciones, mayúsculas UPPERCASE, exportación y lectura de plantilla Excel).
  - Implementación de `utils/dialog_helper.py` para apertura y guardado nativo en Windows Explorer.
  - Implementación de motor de migraciones estilo Django en `migraciones/` y `controllers/migration_controller.py`:
    - Secuencia correlativa (`0001_initial.py`, etc.).
    - Atributos estándar: `dependencies`, `operations`, `def up(cursor)`, `def down(cursor)`.
    - Tabla de control `migraciones` en SQL Server con control de lotes (`lote`), operador y estado.
    - Soporte para ejecutar migraciones (`migrate`) y crear nuevas migraciones (`makemigrations`).
  - Implementación de pestaña de Configuración (`views/components/config_tab.py`) con control de credenciales, parámetros por defecto de Profit Plus, usuario operador y panel interactivo de migraciones.
  - Implementación de navegador de pestañas SegmentedButton en `views/main_view.py` alternando entre "Carga Masiva" y "Configuración y Migraciones".
  - Implementación de verificación en tiempo real de estatus de artículos contra Profit Plus (`saArticulo`):
    - Botón "Verificar Existencia en Profit" en la barra de herramientas de la tabla.
    - Badges de estado dinámicos en cada fila: "Creado en Profit", "Existe en BD", "Listo para Cargar", "Repetido en Archivo" y "Error de Formato".
    - Actualización in-place del estado tras la consulta directa a SQL Server.
  - Implementación de barra de carga en tiempo real (`ft.ProgressBar`):
    - Contador interactivo `actual / total` con cálculo de porcentaje en vivo.
    - Visualización detallada del código y descripción del artículo procesado en cada ciclo de inserción transaccional.
    - Actualización progresiva en el modelo de artículo (`CREADO_EXITOSO`) conforme avanza la carga.
  - Corrección de apertura de diálogo de confirmación y notificaciones para Flet 0.86+:
    - Sustitución de `page.dialog` obsoleto por `page.show_dialog()` y `page.pop_dialog()`.
    - Generación dinámica de `ft.AlertDialog` para asegurar datos y métricas actualizadas en cada clic.
  - Implementación de creación completa de producto y existencias en almacén:
    - Integración de `saStockAlmacen` con sentencia atómica `MERGE` para registrar el stock actual disponible (`ACT`), comprometido (`COM`), despachado (`DES`) y por llegar (`LLE`) en el almacén por defecto.
    - Soporte para columna opcional `STOCK_INICIAL` en la plantilla Excel descargable y en el lector de archivos.
    - Clarificación semántica en interfaz: botón *"Verificar si ya está Creado en Profit"* e insignia *"Ya Creado en BD"*.
    - Nueva columna *"Stock Inicial"* en la tabla de previsualización con desglose de docenas vs. unidades.
  - Corrección de inserción en saArtPrecio (Error 42000 / 271):
    - Se removió la columna calculada `co_alma_calculado` del `INSERT`, permitiendo que SQL Server la calcule nativamente desde `co_alma`.
  - Pruebas integrales de flujo y renderizado completadas satisfactoriamente.
