"""
Helper para la apertura de diálogos nativos de selección y guardado de archivos
mediante tkinter en entornos de escritorio (Windows).
Evita el error 'Unknown control: FilePicker' en versiones recientes de Flet.
"""

from typing import Optional
import tkinter as tk
from tkinter import filedialog


def abrir_dialogo_archivo(
    titulo: str = "Seleccionar archivo de artículos",
    tipos_archivo=None,
) -> Optional[str]:
    """Abre el diálogo nativo de selección de archivo en Windows."""
    if tipos_archivo is None:
        tipos_archivo = [
            ("Archivos de Excel y CSV", "*.xlsx *.xls *.csv"),
            ("Libros de Excel (*.xlsx)", "*.xlsx"),
            ("Archivos CSV (*.csv)", "*.csv"),
            ("Todos los archivos", "*.*"),
        ]

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        ruta = filedialog.askopenfilename(
            title=titulo,
            filetypes=tipos_archivo,
        )
        return ruta if ruta else None
    finally:
        root.destroy()


def abrir_dialogo_guardar(
    titulo: str = "Guardar Plantilla de Artículos",
    nombre_sugerido: str = "Plantilla_Carga_Masiva_Profit.xlsx",
) -> Optional[str]:
    """Abre el diálogo nativo de guardado de archivo en Windows."""
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        ruta = filedialog.asksaveasfilename(
            title=titulo,
            initialfile=nombre_sugerido,
            defaultextension=".xlsx",
            filetypes=[("Libro de Excel (*.xlsx)", "*.xlsx")],
        )
        return ruta if ruta else None
    finally:
        root.destroy()
