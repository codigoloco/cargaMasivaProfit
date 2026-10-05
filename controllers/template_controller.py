"""
Controlador para la gestión y descarga de plantillas de carga masiva.
"""

import os
from typing import Optional, Dict
from utils.excel_helper import generar_plantilla_excel


class TemplateController:
    def __init__(self, articulo_model=None):
        self.articulo_model = articulo_model

    @staticmethod
    def obtener_ruta_descarga_predeterminada() -> str:
        """Retorna una ruta predeterminada en el escritorio o descargas del usuario."""
        home = os.path.expanduser("~")
        desktop = os.path.join(home, "Desktop")
        if os.path.exists(desktop):
            return os.path.join(desktop, "Plantilla_Carga_Masiva_Profit.xlsx")
        downloads = os.path.join(home, "Downloads")
        if os.path.exists(downloads):
            return os.path.join(downloads, "Plantilla_Carga_Masiva_Profit.xlsx")
        return os.path.join(os.getcwd(), "Plantilla_Carga_Masiva_Profit.xlsx")

    def descargar_plantilla(self, ruta_destino: str = "", catalogos: Optional[Dict] = None) -> str:
        """Genera la plantilla en la ruta indicada o predeterminada incorporando los catálogos maestros."""
        destino = ruta_destino if ruta_destino else self.obtener_ruta_descarga_predeterminada()
        if not catalogos and self.articulo_model:
            catalogos = self.articulo_model.obtener_catalogos_maestros()
        exito = generar_plantilla_excel(destino, catalogos=catalogos)
        if exito:
            return destino
        raise RuntimeError("No se pudo generar la plantilla Excel.")
