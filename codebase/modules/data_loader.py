"""
DATA_LOADER.PY - Carga de datos del proyecto

Maneja la carga del JSON de elementos y de archivos de texto externos.
"""

import json
from pathlib import Path
from typing import Dict, Any, Tuple

from config.config import (
    JSON_INPUT_FILE,
    ELEMENTOS_REQUERIDOS_JSON,
)


def cargar_archivo_externo(ruta: Path) -> str:
    """
    Lee el contenido de un archivo de texto.

    Raises:
        FileNotFoundError: si el archivo no existe
    """
    ruta = Path(ruta)
    if not ruta.exists():
        raise FileNotFoundError(f"❌ No se encontró: {ruta}")
    return ruta.read_text(encoding="utf-8")


def cargar_datos_historias(ruta_json: Path = None) -> Dict[str, Any]:
    """
    Carga los elementos de construcción de historias desde inputs.opt2.json.

    Returns:
        dict: contenido de 'construccionHistorias'

    Raises:
        FileNotFoundError: si el JSON no existe
        ValueError: si faltan elementos requeridos
    """
    archivo = Path(ruta_json) if ruta_json else JSON_INPUT_FILE

    if not archivo.is_absolute():
        archivo = Path(__file__).parent.parent / archivo

    if not archivo.exists():
        raise FileNotFoundError(f"❌ JSON no encontrado: {archivo}")

    with open(archivo, "r", encoding="utf-8") as f:
        datos = json.load(f)

    contenedor = datos.get("construccionHistorias", {})

    faltantes = [e for e in ELEMENTOS_REQUERIDOS_JSON if e not in contenedor]
    if faltantes:
        raise ValueError(f"❌ Faltan elementos en el JSON: {faltantes}")

    print(f"✅ Datos cargados: {archivo.name}  "
          f"({len(contenedor.get('personajesSecundarios', []))} personajes secundarios)")
    return contenedor


def cargar_prompts(ruta_system: Path, ruta_template: Path) -> Tuple[str, str]:
    """
    Carga el system prompt y la plantilla de historia.

    Returns:
        (system_prompt, template_prompt)
    """
    system   = cargar_archivo_externo(ruta_system)
    template = cargar_archivo_externo(ruta_template)
    print("✅ Prompts de narrador cargados")
    return system, template
