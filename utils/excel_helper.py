"""
Helper para la generación y lectura de plantillas Excel/CSV.
Utiliza openpyxl para estilizar plantillas y pandas para lectura flexible.
"""

import os
from typing import List, Dict
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from utils.validators import normalizar_texto, normalizar_precio, normalizar_unidad


def generar_plantilla_excel(ruta_destino: str, catalogos: Dict = None) -> bool:
    """
    Genera un archivo Excel (.xlsx) estructurado con:
    - Hoja 1: Plantilla_Articulos (con columnas personalizadas de clasificación masiva por fila).
    - Hoja 2: Catalogo_Lineas_Sublineas (relación de líneas y sublíneas activas en Profit).
    - Hoja 3: Catalogo_Categorias (catálogo de categorías).
    - Hoja 4: Catalogo_Almacenes_Colores (catálogo de almacenes y colores disponibles).
    """
    try:
        wb = Workbook()

        # --- HOJA 1: Plantilla de Carga Masiva de Artículos ---
        ws = wb.active
        ws.title = "Plantilla_Articulos"

        encabezados = [
            "CODIGO",
            "DESCRIPCION",
            "REFERENCIA",
            "MODELO",
            "LINEA",
            "SUBLINEA",
            "CATEGORIA",
            "COLOR",
            "ALMACEN",
            "UNIDAD_TIPO",
            "STOCK_INICIAL",
            "PRECIO_1",
            "PRECIO_2",
            "PRECIO_3",
            "PRECIO_4",
            "PRECIO_5",
        ]

        # Estilos para el encabezado principal
        header_fill = PatternFill(start_color="1A365D", end_color="1A365D", fill_type="solid")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
        thin_border = Border(
            left=Side(style="thin", color="CBD5E1"),
            right=Side(style="thin", color="CBD5E1"),
            top=Side(style="thin", color="CBD5E1"),
            bottom=Side(style="thin", color="CBD5E1"),
        )

        ws.append(encabezados)

        # Aplicar estilos al encabezado de la Hoja 1
        for col_num, _ in enumerate(encabezados, 1):
            cell = ws.cell(row=1, column=col_num)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = center_align
            cell.border = thin_border

        # Filas de ejemplo demostrativo con clasificaciones reales de Profit
        ejemplos = [
            [
                "BLU-0010-S",
                "BLUSA DE DAMA CASUAL MANGAS CORTAS",
                "REF-BLU10",
                "MOD-VERANO",
                "003",
                "002",
                "018",
                "001",
                "01",
                "DOCENA",
                25.0,
                24.50,
                22.00,
                20.00,
                19.50,
                18.00,
            ],
            [
                "PAN-0025-M",
                "PANTALON CLASICO CABALLERO",
                "REF-PAN25",
                "MOD-EJECUTIVO",
                "003",
                "007",
                "019",
                "003",
                "01",
                "DOCENA",
                50.0,
                36.00,
                34.00,
                32.50,
                30.00,
                28.00,
            ],
            [
                "ACC-0099-U",
                "CINTURON DE CUERO NEGRO",
                "REF-ACC99",
                "MOD-UNISEX",
                "010",
                "001",
                "030",
                "003",
                "01",
                "UNIDAD",
                100.0,
                5.00,
                4.50,
                4.20,
                4.00,
                3.80,
            ],
        ]

        for fila in ejemplos:
            ws.append(fila)

        # Estilizar filas de datos de ejemplo
        data_font = Font(name="Calibri", size=10)
        for row in ws.iter_rows(min_row=2, max_row=len(ejemplos) + 1, min_col=1, max_col=len(encabezados)):
            for cell in row:
                cell.font = data_font
                cell.border = thin_border
                if cell.column in (11, 12, 13, 14, 15, 16):
                    cell.alignment = Alignment(horizontal="right")
                else:
                    cell.alignment = Alignment(horizontal="left")

        # Ajuste dinámico de ancho de columnas en Hoja 1
        anchos = {
            "A": 18,  # CODIGO
            "B": 42,  # DESCRIPCION
            "C": 18,  # REFERENCIA
            "D": 18,  # MODELO
            "E": 12,  # LINEA
            "F": 12,  # SUBLINEA
            "G": 14,  # CATEGORIA
            "H": 12,  # COLOR
            "I": 12,  # ALMACEN
            "J": 16,  # UNIDAD_TIPO
            "K": 16,  # STOCK_INICIAL
            "L": 14,  # PRECIO_1
            "M": 14,  # PRECIO_2
            "N": 14,  # PRECIO_3
            "O": 14,  # PRECIO_4
            "P": 14,  # PRECIO_5
        }
        for col_letter, width in anchos.items():
            ws.column_dimensions[col_letter].width = width

        # Estilos para encabezados de catálogos
        cat_fill = PatternFill(start_color="2B6CB0", end_color="2B6CB0", fill_type="solid")
        cat_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")

        # --- HOJA 2: Catálogo de Líneas y Sublíneas ---
        ws_lineas = wb.create_sheet(title="Catalogo_Lineas_Sublineas")
        headers_ls = ["COD_LINEA", "NOMBRE_LINEA", "COD_SUBLINEA", "NOMBRE_SUBLINEA"]
        ws_lineas.append(headers_ls)
        for col_idx in range(1, 5):
            c = ws_lineas.cell(row=1, column=col_idx)
            c.fill = cat_fill
            c.font = cat_font
            c.alignment = center_align

        if catalogos and catalogos.get("lineas_sublineas"):
            for row in catalogos["lineas_sublineas"]:
                ws_lineas.append([row[0], row[1], row[2], row[3]])
        ws_lineas.column_dimensions["A"].width = 16
        ws_lineas.column_dimensions["B"].width = 34
        ws_lineas.column_dimensions["C"].width = 16
        ws_lineas.column_dimensions["D"].width = 34

        # --- HOJA 3: Catálogo de Categorías ---
        ws_cat = wb.create_sheet(title="Catalogo_Categorias")
        headers_cat = ["COD_CATEGORIA", "NOMBRE_CATEGORIA"]
        ws_cat.append(headers_cat)
        for col_idx in range(1, 3):
            c = ws_cat.cell(row=1, column=col_idx)
            c.fill = cat_fill
            c.font = cat_font
            c.alignment = center_align

        if catalogos and catalogos.get("categorias"):
            for row in catalogos["categorias"]:
                ws_cat.append([row[0], row[1]])
        ws_cat.column_dimensions["A"].width = 18
        ws_cat.column_dimensions["B"].width = 40

        # --- HOJA 4: Catálogo de Almacenes y Colores ---
        ws_alm_col = wb.create_sheet(title="Catalogo_Almacenes_Colores")
        headers_ac = ["COD_ALMACEN", "NOMBRE_ALMACEN", "", "COD_COLOR", "NOMBRE_COLOR"]
        ws_alm_col.append(headers_ac)
        for col_idx in (1, 2, 4, 5):
            c = ws_alm_col.cell(row=1, column=col_idx)
            c.fill = cat_fill
            c.font = cat_font
            c.alignment = center_align

        alms = catalogos.get("almacenes", []) if catalogos else []
        cols = catalogos.get("colores", []) if catalogos else []
        max_filas = max(len(alms), len(cols))
        for i in range(max_filas):
            a_cod = alms[i][0] if i < len(alms) else ""
            a_des = alms[i][1] if i < len(alms) else ""
            c_cod = cols[i][0] if i < len(cols) else ""
            c_des = cols[i][1] if i < len(cols) else ""
            ws_alm_col.append([a_cod, a_des, "", c_cod, c_des])

        ws_alm_col.column_dimensions["A"].width = 16
        ws_alm_col.column_dimensions["B"].width = 32
        ws_alm_col.column_dimensions["C"].width = 6
        ws_alm_col.column_dimensions["D"].width = 16
        ws_alm_col.column_dimensions["E"].width = 30

        wb.save(ruta_destino)
        return True
    except Exception as err:
        print(f"Error al generar plantilla Excel estructurada: {err}")
        return False


def leer_archivo_articulos(ruta_archivo: str) -> List[Dict]:
    """
    Lee un archivo Excel (.xlsx, .xls) o CSV y normaliza las columnas
    a los campos requeridos en mayúsculas.
    """
    if not os.path.exists(ruta_archivo):
        raise FileNotFoundError(f"No se encontró el archivo: {ruta_archivo}")

    _, ext = os.path.splitext(ruta_archivo.lower())
    if ext in (".xlsx", ".xls"):
        df = pd.read_excel(ruta_archivo, dtype=str)
    elif ext == ".csv":
        # Intentar con diferentes delimitadores comunes
        try:
            df = pd.read_csv(ruta_archivo, sep=";", dtype=str)
            if len(df.columns) <= 1:
                df = pd.read_csv(ruta_archivo, sep=",", dtype=str)
        except Exception:
            df = pd.read_csv(ruta_archivo, sep=",", dtype=str)
    else:
        raise ValueError("Formato de archivo no soportado. Use .xlsx, .xls o .csv")

    # Mapeo flexible de sinónimos de encabezados a nombres internos canónicos
    mapa_columnas = {}
    for col in df.columns:
        col_clean = normalizar_texto(col).replace(" ", "_")
        if col_clean in ("CODIGO", "COD", "CO_ART", "COD_ART", "ART_COD", "CODIGO_ARTICULO"):
            mapa_columnas[col] = "codigo"
        elif col_clean in ("DESCRIPCION", "DESC", "ART_DES", "NOMBRE", "DESCRIPCION_ARTICULO"):
            mapa_columnas[col] = "descripcion"
        elif col_clean in ("REFERENCIA", "REF", "COD_REF", "CODIGO_REFERENCIAL"):
            mapa_columnas[col] = "referencia"
        elif col_clean in ("MODELO", "MOD", "MODEL"):
            mapa_columnas[col] = "modelo"
        elif col_clean in ("LINEA", "LIN", "CO_LIN", "COD_LIN", "LINEA_ARTICULO"):
            mapa_columnas[col] = "linea"
        elif col_clean in ("SUBLINEA", "SUBLIN", "CO_SUBL", "COD_SUBL", "SUBLINEA_ARTICULO"):
            mapa_columnas[col] = "sublinea"
        elif col_clean in ("CATEGORIA", "CAT", "CO_CAT", "COD_CAT", "CATEGORIA_ARTICULO"):
            mapa_columnas[col] = "categoria"
        elif col_clean in ("COLOR", "COL", "CO_COLOR", "COD_COLOR"):
            mapa_columnas[col] = "color"
        elif col_clean in ("ALMACEN", "ALM", "CO_ALMA", "COD_ALMA", "DEPOSITO"):
            mapa_columnas[col] = "almacen"
        elif col_clean in ("UNIDAD_TIPO", "UNIDAD", "TIPO_UNIDAD", "DOCENA_UNIDAD", "MEDIDA", "TIPO"):
            mapa_columnas[col] = "unidad_tipo"
        elif col_clean in ("STOCK_INICIAL", "STOCK", "CANTIDAD", "EXISTENCIA", "EXISTENCIA_INICIAL", "CANT"):
            mapa_columnas[col] = "stock_inicial"
        elif col_clean in ("PRECIO_1", "PRECIO1", "P1", "MONTO", "PRECIO"):
            mapa_columnas[col] = "precio_1"
        elif col_clean in ("PRECIO_2", "PRECIO2", "P2"):
            mapa_columnas[col] = "precio_2"
        elif col_clean in ("PRECIO_3", "PRECIO3", "P3"):
            mapa_columnas[col] = "precio_3"
        elif col_clean in ("PRECIO_4", "PRECIO4", "P4"):
            mapa_columnas[col] = "precio_4"
        elif col_clean in ("PRECIO_5", "PRECIO5", "P5"):
            mapa_columnas[col] = "precio_5"

    df_renombrado = df.rename(columns=mapa_columnas)

    articulos = []
    for _, fila in df_renombrado.iterrows():
        # Ignorar filas totalmente vacías
        codigo_raw = fila.get("codigo")
        desc_raw = fila.get("descripcion")
        if pd.isna(codigo_raw) and pd.isna(desc_raw):
            continue

        art = {
            "codigo": normalizar_texto(codigo_raw),
            "descripcion": normalizar_texto(desc_raw),
            "referencia": normalizar_texto(fila.get("referencia")),
            "modelo": normalizar_texto(fila.get("modelo")),
            "linea": normalizar_texto(fila.get("linea")),
            "sublinea": normalizar_texto(fila.get("sublinea")),
            "categoria": normalizar_texto(fila.get("categoria")),
            "color": normalizar_texto(fila.get("color")),
            "almacen": normalizar_texto(fila.get("almacen")),
            "unidad_tipo": normalizar_unidad(fila.get("unidad_tipo")),
            "stock_inicial": normalizar_precio(fila.get("stock_inicial", 0.0)),
            "precio_1": normalizar_precio(fila.get("precio_1")),
            "precio_2": normalizar_precio(fila.get("precio_2")),
            "precio_3": normalizar_precio(fila.get("precio_3")),
            "precio_4": normalizar_precio(fila.get("precio_4")),
            "precio_5": normalizar_precio(fila.get("precio_5")),
        }
        articulos.append(art)

    return articulos
