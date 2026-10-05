"""
Modelo para la gestión de artículos, precios y unidades en Profit Plus.
Maneja las tablas saArticulo, saArtPrecio y saArtUnidad en SQL Server.
Aplica principios SOLID y garantiza integridad transaccional.
"""

from typing import List, Dict, Set, Tuple, Optional, Callable
from models.database_model import DatabaseModel
from models.auditoria_model import registrar_auditoria
from config import PROFIT_DEFAULTS


class ArticuloModel:
    def __init__(self, db_model: DatabaseModel):
        self.db_model = db_model

    def obtener_articulos_existentes(self, codigos: List[str]) -> Set[str]:
        """
        Retorna el conjunto de códigos que ya existen en saArticulo.
        Compara en MAYÚSCULAS para evitar discrepancias de caso.
        """
        if not codigos:
            return set()

        codigos_upper = [c.strip().upper() for c in codigos if c and c.strip()]
        if not codigos_upper:
            return set()

        # Evitar sobrepasar límite de parámetros dividiendo en lotes si es necesario
        existentes: Set[str] = set()
        lote_tamano = 500

        for i in range(0, len(codigos_upper), lote_tamano):
            sub_lote = codigos_upper[i : i + lote_tamano]
            placeholders = ",".join("?" for _ in sub_lote)
            query = f"SELECT UPPER(RTRIM(co_art)) FROM saArticulo WHERE UPPER(RTRIM(co_art)) IN ({placeholders})"

            try:
                with self.db_model.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(query, sub_lote)
                    for row in cursor.fetchall():
                        existentes.add(row[0].strip().upper())
            except Exception as err:
                print(f"Error al verificar artículos existentes: {err}")

        return existentes

    def insertar_lote(
        self,
        articulos: List[Dict],
        usuario_id: str = "ADMIN",
        ip_origen: str = "127.0.0.1",
        callback_progreso: Optional[Callable[[int, int, Dict], None]] = None,
    ) -> Tuple[bool, int, List[str]]:
        """
        Inserta un lote de artículos en saArticulo, saArtPrecio y saArtUnidad
        dentro de una única transacción atómica.
        Actualiza el estado de cada artículo a CREADO_EXITOSO y emite progreso.
        Registra la auditoría correspondiente con la cantidad y detalle.
        """
        if not articulos:
            return False, 0, ["No se proporcionaron artículos para procesar."]

        errores: List[str] = []
        insertados = 0
        total_articulos = len(articulos)

        # Sentencias SQL preparadas
        sql_articulo = """
        INSERT INTO saArticulo (
            co_art, art_des, tipo, anulado, fecha_reg, co_lin, co_subl, co_cat, co_color,
            co_ubicacion, cod_proc, modelo, ref, generico, maneja_serial, maneja_lote,
            maneja_lote_venc, margen_min, margen_max, tipo_imp, garantia, volumen, peso,
            stock_min, stock_max, stock_pedido, relac_unidad, punt_ven, punt_cli,
            lic_mon_ilc, lic_capacidad, lic_grado_al, prec_om, porc_margen_minimo,
            porc_margen_maximo, mont_comi, porc_arancel, co_us_in, co_sucu_in, fe_us_in,
            co_us_mo, co_sucu_mo, fe_us_mo, rowguid
        ) VALUES (
            ?, ?, ?, 0, GETDATE(), ?, ?, ?, ?,
            ?, ?, ?, ?, 0, 0, 0,
            0, 0, 0, ?, ?, 0, 0,
            0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0,
            0, 0, 0, ?, ?, GETDATE(),
            ?, ?, GETDATE(), NEWID()
        );
        """

        sql_precio = """
        INSERT INTO saArtPrecio (
            co_art, co_precio, desde, hasta, co_alma,
            monto, montoadi1, montoadi2, montoadi3, montoadi4,
            precioOm, co_us_in, co_sucu_in, fe_us_in, co_us_mo, co_sucu_mo, fe_us_mo,
            co_mone, Inactivo, rowguid
        ) VALUES (
            ?, ?, GETDATE(), '2035-12-31', ?,
            ?, ?, ?, ?, ?,
            1, ?, ?, GETDATE(), ?, ?, GETDATE(),
            ?, 0, NEWID()
        );
        """

        sql_unidad = """
        INSERT INTO saArtUnidad (
            co_art, co_uni, relacion, equivalencia, uso_venta, uso_compra,
            uni_principal, uso_principal, uni_secundaria, uso_secundaria,
            uso_numDecimales, num_decimales, co_us_in, co_sucu_in, fe_us_in,
            co_us_mo, co_sucu_mo, fe_us_mo, rowguid
        ) VALUES (
            ?, ?, 0, ?, 1, 1,
            ?, ?, ?, ?,
            0, 0, ?, ?, GETDATE(),
            ?, ?, GETDATE(), NEWID()
        );
        """

        sql_stock = """
        MERGE saStockAlmacen AS target
        USING (SELECT ? AS co_alma, ? AS co_art, ? AS tipo, ? AS stock) AS source
        ON (target.co_alma = source.co_alma AND target.co_art = source.co_art AND target.tipo = source.tipo)
        WHEN MATCHED THEN
            UPDATE SET target.stock = source.stock
        WHEN NOT MATCHED THEN
            INSERT (co_alma, co_art, tipo, stock, revisado, trasnfe)
            VALUES (source.co_alma, source.co_art, source.tipo, source.stock, NULL, NULL);
        """

        try:
            with self.db_model.get_connection() as conn:
                cursor = conn.cursor()

                for idx, art in enumerate(articulos, start=1):
                    codigo = str(art.get("codigo", "")).strip().upper()
                    descripcion = str(art.get("descripcion", "")).strip().upper()
                    referencia = str(art.get("referencia", "") or "").strip().upper()
                    modelo = str(art.get("modelo", "") or "").strip().upper()
                    unidad_tipo = str(art.get("unidad_tipo", "DOCENA")).strip().upper()

                    precio1 = float(art.get("precio_1", 0.0) or 0.0)
                    precio2 = float(art.get("precio_2", 0.0) or 0.0)
                    precio3 = float(art.get("precio_3", 0.0) or 0.0)
                    precio4 = float(art.get("precio_4", 0.0) or 0.0)
                    precio5 = float(art.get("precio_5", 0.0) or 0.0)

                    # Atributos personalizados por producto (con fallback a valores configurados)
                    co_lin = str(art.get("linea") or PROFIT_DEFAULTS["co_lin"]).strip().upper()
                    co_subl = str(art.get("sublinea") or PROFIT_DEFAULTS["co_subl"]).strip().upper()
                    co_cat = str(art.get("categoria") or PROFIT_DEFAULTS["co_cat"]).strip().upper()
                    co_color = str(art.get("color") or PROFIT_DEFAULTS["co_color"]).strip().upper()
                    co_alma = str(art.get("almacen") or PROFIT_DEFAULTS["alma_precio"]).strip().upper()

                    # 1. Insertar saArticulo
                    cursor.execute(
                        sql_articulo,
                        (
                            codigo,
                            descripcion,
                            PROFIT_DEFAULTS["tipo"],
                            co_lin,
                            co_subl,
                            co_cat,
                            co_color,
                            PROFIT_DEFAULTS["co_ubicacion"],
                            PROFIT_DEFAULTS["cod_proc"],
                            modelo if modelo else None,
                            referencia if referencia else None,
                            PROFIT_DEFAULTS["tipo_imp"],
                            PROFIT_DEFAULTS["garantia"],
                            PROFIT_DEFAULTS["co_us_in"],
                            PROFIT_DEFAULTS["co_sucu_in"],
                            PROFIT_DEFAULTS["co_us_in"],
                            PROFIT_DEFAULTS["co_sucu_in"],
                        ),
                    )

                    # 2. Insertar saArtPrecio
                    cursor.execute(
                        sql_precio,
                        (
                            codigo,
                            PROFIT_DEFAULTS["co_precio"],
                            co_alma,
                            precio1,
                            precio2,
                            precio3,
                            precio4,
                            precio5,
                            PROFIT_DEFAULTS["co_us_in"],
                            PROFIT_DEFAULTS["co_sucu_in"],
                            PROFIT_DEFAULTS["co_us_in"],
                            PROFIT_DEFAULTS["co_sucu_in"],
                            PROFIT_DEFAULTS["co_mone"],
                        ),
                    )

                    # 3. Insertar saArtUnidad
                    # Si es DOCENA: Principal DOC (equiv 12), Secundaria PZA (equiv 1)
                    # Si es UNIDAD: Principal PZA (equiv 1), Secundaria DOC (equiv 12)
                    es_docena = "DOC" in unidad_tipo
                    if es_docena:
                        uni_primaria = PROFIT_DEFAULTS["unidad_docena"]
                        factor_primaria = PROFIT_DEFAULTS["factor_docena"]
                        uni_secundaria = PROFIT_DEFAULTS["unidad_pieza"]
                        factor_secundaria = PROFIT_DEFAULTS["factor_unidad"]
                    else:
                        uni_primaria = PROFIT_DEFAULTS["unidad_pieza"]
                        factor_primaria = PROFIT_DEFAULTS["factor_unidad"]
                        uni_secundaria = PROFIT_DEFAULTS["unidad_docena"]
                        factor_secundaria = PROFIT_DEFAULTS["factor_docena"]

                    # Inserción Unidad Principal
                    cursor.execute(
                        sql_unidad,
                        (
                            codigo,
                            uni_primaria,
                            factor_primaria,
                            1,  # uni_principal
                            1,  # uso_principal
                            0,  # uni_secundaria
                            0,  # uso_secundaria
                            PROFIT_DEFAULTS["co_us_in"],
                            PROFIT_DEFAULTS["co_sucu_in"],
                            PROFIT_DEFAULTS["co_us_in"],
                            PROFIT_DEFAULTS["co_sucu_in"],
                        ),
                    )

                    # Inserción Unidad Secundaria
                    cursor.execute(
                        sql_unidad,
                        (
                            codigo,
                            uni_secundaria,
                            factor_secundaria,
                            0,  # uni_principal
                            0,  # uso_principal
                            1,  # uni_secundaria
                            1,  # uso_secundaria
                            PROFIT_DEFAULTS["co_us_in"],
                            PROFIT_DEFAULTS["co_sucu_in"],
                            PROFIT_DEFAULTS["co_us_in"],
                            PROFIT_DEFAULTS["co_sucu_in"],
                        ),
                    )

                    # 4. Insertar existencias en saStockAlmacen (Almacén del artículo o configurado)
                    stock_inicial = float(art.get("stock_inicial", 0.0) or 0.0)

                    # Stock actual disponible (ACT)
                    cursor.execute(sql_stock, (co_alma, codigo, "ACT ", stock_inicial))
                    # Stock comprometido (COM), despachado (DES) y por llegar (LLE)
                    cursor.execute(sql_stock, (co_alma, codigo, "COM ", 0.0))
                    cursor.execute(sql_stock, (co_alma, codigo, "DES ", 0.0))
                    cursor.execute(sql_stock, (co_alma, codigo, "LLE ", 0.0))

                    insertados += 1
                    art["estado"] = "CREADO_EXITOSO"
                    art["mensaje_estado"] = f"Creado en Profit con existencia inicial: {stock_inicial}"
                    art["es_valido"] = False

                    if callback_progreso:
                        callback_progreso(idx, total_articulos, art)

                # Confirmar transacción completa
                conn.commit()

            # Registrar auditoría de la operación masiva
            co_alma = PROFIT_DEFAULTS.get("alma_precio", "01")
            desc_auditoria = (
                f"Carga masiva exitosa de {insertados} artículos en Profit Plus (BD: {self.db_model.active_database}). "
                f"Lote procesado: catálogo (saArticulo), precios 1-5 (saArtPrecio), "
                f"unidades principales/secundarias (saArtUnidad) y existencias en almacén {co_alma} (saStockAlmacen)."
            )
            registrar_auditoria(
                modulo="articulos",
                tipo_accion="INSERT_MASIVO",
                descripcion=desc_auditoria,
                registro_id=f"LOTE_{insertados}_ITEMS",
                usuario_id=usuario_id,
                ip_origen=ip_origen,
                db_model=self.db_model,
            )

            return True, insertados, []

        except Exception as err:
            error_msg = f"Error transaccional durante la inserción: {str(err)}"
            print(error_msg)
            errores.append(error_msg)
            return False, 0, errores

    def verificar_estado_articulos(self, articulos: List[Dict]) -> Tuple[int, int]:
        """
        Verifica en tiempo real contra saArticulo cuáles artículos ya existen.
        Actualiza el estado de cada artículo in-place.
        Retorna (existentes_count, no_existentes_count).
        """
        if not articulos:
            return 0, 0

        todos_codigos = [art.get("codigo", "") for art in articulos if art.get("codigo")]
        existentes_bd = self.obtener_articulos_existentes(todos_codigos)

        cant_existentes = 0
        cant_no_existentes = 0

        for art in articulos:
            cod = str(art.get("codigo", "")).strip().upper()
            if cod in existentes_bd:
                art["estado"] = "YA_EXISTE_BD"
                art["mensaje_estado"] = "Confirmado: Ya creado en Profit Plus (saArticulo)"
                art["es_valido"] = False
                cant_existentes += 1
            elif art.get("estado") == "CREADO_EXITOSO":
                cant_existentes += 1
            elif art.get("estado") not in ("ERROR_CODIGO", "ERROR_LONGITUD", "DUPLICADO_ARCHIVO"):
                art["estado"] = "VALIDO"
                art["mensaje_estado"] = "Listo para registrar (no existe en Profit)"
                art["es_valido"] = True
                cant_no_existentes += 1

        return cant_existentes, cant_no_existentes

    def obtener_catalogos_maestros(self) -> Dict[str, List]:
        """
        Consulta y retorna las listas de Líneas, Sublíneas, Categorías,
        Almacenes y Colores registrados en la BD activa de Profit Plus.
        """
        catalogos = {
            "lineas_sublineas": [],
            "categorias": [],
            "almacenes": [],
            "colores": [],
        }
        try:
            with self.db_model.get_connection() as conn:
                cur = conn.cursor()
                # 1. Líneas y Sublíneas vinculadas
                cur.execute(
                    """
                    SELECT 
                        RTRIM(l.co_lin) as co_lin, 
                        RTRIM(l.lin_des) as lin_des, 
                        ISNULL(RTRIM(s.co_subl), '') as co_subl, 
                        ISNULL(RTRIM(s.subl_des), '') as subl_des
                    FROM saLineaArticulo l
                    LEFT JOIN saSubLinea s ON l.co_lin = s.co_lin
                    ORDER BY l.co_lin, s.co_subl
                    """
                )
                catalogos["lineas_sublineas"] = cur.fetchall()

                # 2. Categorías
                cur.execute(
                    """
                    SELECT RTRIM(co_cat) as co_cat, RTRIM(cat_des) as cat_des 
                    FROM saCatArticulo 
                    ORDER BY co_cat
                    """
                )
                catalogos["categorias"] = cur.fetchall()

                # 3. Almacenes
                cur.execute(
                    """
                    SELECT RTRIM(co_alma) as co_alma, RTRIM(des_alma) as des_alma 
                    FROM saAlmacen 
                    ORDER BY co_alma
                    """
                )
                catalogos["almacenes"] = cur.fetchall()

                # 4. Colores
                cur.execute(
                    """
                    SELECT RTRIM(co_color) as co_color, RTRIM(des_color) as des_color 
                    FROM saColor 
                    ORDER BY co_color
                    """
                )
                catalogos["colores"] = cur.fetchall()

        except Exception as err:
            print(f"Aviso al consultar catálogos maestros: {err}")

        return catalogos
