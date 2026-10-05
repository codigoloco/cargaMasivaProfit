"""
Módulo de validadores y normalizadores de datos para MasivoProfit.
Garantiza coincidencia de cadenas en mayúsculas (UPPERCASE) y control de tipos.
"""

from typing import Dict, Set, Tuple, Optional


def normalizar_texto(valor: Optional[str]) -> str:
    """Elimina espacios extremos y convierte a MAYÚSCULAS."""
    if valor is None:
        return ""
    return str(valor).strip().upper()


def normalizar_precio(valor) -> float:
    """Convierte de forma segura cualquier representación de precio a float."""
    if valor is None:
        return 0.0
    if isinstance(valor, (int, float)):
        return max(0.0, float(valor))
    try:
        # Reemplazar posibles comas de miles/decimales
        val_str = str(valor).strip().replace("$", "").replace(" ", "")
        if "," in val_str and "." in val_str:
            # Caso 1,250.50 -> quitar coma
            val_str = val_str.replace(",", "")
        elif "," in val_str:
            # Caso 12,50 -> reemplazar por punto
            val_str = val_str.replace(",", ".")
        return max(0.0, float(val_str))
    except (ValueError, TypeError):
        return 0.0


def normalizar_unidad(valor: Optional[str]) -> str:
    """
    Normaliza el tipo de unidad a 'DOCENA' o 'UNIDAD'.
    Prioriza DOCENA según regla de negocio.
    """
    texto = normalizar_texto(valor)
    if "DOC" in texto or "DOZ" in texto or "12" in texto:
        return "DOCENA"
    if "UNI" in texto or "PZA" in texto or "PIE" in texto or "UND" in texto:
        return "UNIDAD"
    # Por defecto, regla de negocio: preferir siempre docenas
    return "DOCENA"


def validar_articulo(
    art: Dict,
    codigos_existentes_bd: Set[str],
    codigos_vistos_lote: Set[str],
) -> Tuple[bool, str, str]:
    """
    Valida la consistencia de una fila de artículo antes de procesar.
    Retorna: (es_valido, estado_visual, mensaje_detalle)
    """
    codigo = normalizar_texto(art.get("codigo"))
    descripcion = normalizar_texto(art.get("descripcion"))

    if not codigo:
        return False, "ERROR_CODIGO", "El código del artículo no puede estar vacío."

    if len(codigo) > 30:
        return False, "ERROR_LONGITUD", f"El código excede los 30 caracteres ({len(codigo)})."

    if not descripcion:
        return False, "ERROR_DESCRIPCION", "La descripción del artículo no puede estar vacía."

    if len(descripcion) > 120:
        return False, "ERROR_LONGITUD", f"La descripción excede 120 caracteres ({len(descripcion)})."

    # Validar duplicados en el mismo archivo cargado
    if codigo in codigos_vistos_lote:
        return False, "DUPLICADO_ARCHIVO", f"El código '{codigo}' está repetido en el archivo."

    # Validar existencia previa en la base de datos de Profit
    if codigo in codigos_existentes_bd:
        return False, "YA_EXISTE_BD", f"El código '{codigo}' ya existe en Profit Plus."

    return True, "VALIDO", "Listo para registrar."
