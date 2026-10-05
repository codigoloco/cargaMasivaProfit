"""
Controlador de importación, validación y procesamiento masivo de artículos.
"""

from typing import List, Dict, Tuple, Set
from utils.excel_helper import leer_archivo_articulos
from utils.validators import validar_articulo
from models.articulo_model import ArticuloModel


class ImportController:
    def __init__(self, articulo_model: ArticuloModel):
        self.articulo_model = articulo_model

    def analizar_archivo(self, ruta_archivo: str) -> Dict:
        """
        Lee el archivo, consulta la base de datos para verificar existencia previa,
        y asigna estado de validación a cada fila.
        """
        articulos_crudos = leer_archivo_articulos(ruta_archivo)
        if not articulos_crudos:
            return {
                "articulos": [],
                "resumen": {
                    "total": 0,
                    "validos": 0,
                    "errores": 0,
                    "docenas": 0,
                    "unidades": 0,
                },
            }

        # Extraer todos los códigos del archivo para consultar la BD en un solo viaje
        todos_codigos = [art["codigo"] for art in articulos_crudos if art.get("codigo")]
        codigos_existentes_bd: Set[str] = self.articulo_model.obtener_articulos_existentes(todos_codigos)

        codigos_vistos_lote: Set[str] = set()
        articulos_procesados: List[Dict] = []

        total_validos = 0
        total_errores = 0
        conteo_docenas = 0
        conteo_unidades = 0

        for art in articulos_crudos:
            codigo = art.get("codigo", "")
            es_valido, estado_visual, mensaje = validar_articulo(
                art=art,
                codigos_existentes_bd=codigos_existentes_bd,
                codigos_vistos_lote=codigos_vistos_lote,
            )

            # Si es válido, lo agregamos a los vistos en este lote para detectar duplicados siguientes
            if codigo and es_valido:
                codigos_vistos_lote.add(codigo)

            if es_valido:
                total_validos += 1
            else:
                total_errores += 1

            if art.get("unidad_tipo") == "DOCENA":
                conteo_docenas += 1
            else:
                conteo_unidades += 1

            art_info = dict(art)
            art_info["es_valido"] = es_valido
            art_info["estado"] = estado_visual
            art_info["mensaje_estado"] = mensaje
            articulos_procesados.append(art_info)

        return {
            "articulos": articulos_procesados,
            "resumen": {
                "total": len(articulos_procesados),
                "validos": total_validos,
                "errores": total_errores,
                "docenas": conteo_docenas,
                "unidades": conteo_unidades,
            },
        }

    def ejecutar_carga_masiva(
        self,
        articulos: List[Dict],
        usuario_id: str = "ADMIN",
        callback_progreso=None,
    ) -> Tuple[bool, int, List[str]]:
        """
        Filtra solo los artículos válidos y ejecuta la inserción transaccional emitiendo progreso.
        """
        articulos_validos = [art for art in articulos if art.get("es_valido")]
        if not articulos_validos:
            return False, 0, ["No hay artículos válidos para registrar en la base de datos."]

        return self.articulo_model.insertar_lote(
            articulos=articulos_validos,
            usuario_id=usuario_id,
            callback_progreso=callback_progreso,
        )
