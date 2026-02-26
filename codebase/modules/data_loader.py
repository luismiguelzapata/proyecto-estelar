"""
Módulo de carga de datos
Maneja la carga de JSON y archivos externos
"""

import json
from pathlib import Path
from typing import Dict, Any

from config.config import (
    JSON_INPUT_FILE,
    ELEMENTOS_REQUERIDOS_JSON
)


def cargar_archivo_externo(ruta: Path) -> str:
    """
    Carga el contenido de un archivo externo.
    
    Args:
        ruta (Path): Ruta al archivo
        
    Returns:
        str: Contenido del archivo
        
    Raises:
        FileNotFoundError: Si el archivo no existe
    """
    if not ruta.exists():
        raise FileNotFoundError(f"❌ No se encontró el archivo: {ruta}")
    
    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        raise Exception(f"❌ Error al cargar archivo {ruta}: {str(e)}")


def cargar_datos_historias(ruta_json: Path = None) -> Dict[str, Any]:
    """
    Carga los elementos de construcción de historias desde un archivo JSON externo.
    
    Args:
        ruta_json (Path): Ruta al archivo JSON. Si es None, usa la configuración por defecto.
        
    Returns:
        dict: Diccionario con todos los elementos cargados bajo 'construccionHistorias'
        
    Raises:
        FileNotFoundError: Si el archivo JSON no existe
        json.JSONDecodeError: Si el JSON es inválido
        ValueError: Si faltan elementos requeridos
    """
    
    # Usar ruta por defecto si no se especifica
    if ruta_json is None:
        ruta_json = JSON_INPUT_FILE
    else:
        ruta_json = Path(ruta_json)
    
    # Convertir a Path para mejor manejo de rutas
    archivo_json = Path(ruta_json) if not isinstance(ruta_json, Path) else ruta_json
    
    # Si es ruta relativa, buscar en el mismo directorio que este módulo
    if not archivo_json.is_absolute():
        archivo_json = Path(__file__).parent.parent / archivo_json
    
    if not archivo_json.exists():
        raise FileNotFoundError(f"❌ No se encontró el archivo: {archivo_json}")
    
    try:
        with open(archivo_json, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        
        # Extraer datos del contenedor 'construccionHistorias'
        contenedor = datos.get('construccionHistorias', {})
        
        # Validar que existan todos los elementos necesarios
        faltantes = [elem for elem in ELEMENTOS_REQUERIDOS_JSON if elem not in contenedor]
        if faltantes:
            raise ValueError(f"❌ Faltan elementos en el JSON: {faltantes}")
        
        print(f"✅ Datos cargados correctamente desde: {archivo_json}")
        return contenedor
        
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"❌ JSON inválido en {archivo_json}: {e.msg}", 
            e.doc, 
            e.pos
        )
    except Exception as e:
        raise Exception(f"❌ Error al cargar datos: {str(e)}")


def cargar_prompts(ruta_system: Path, ruta_template: Path) -> tuple[str, str]:
    """
    Carga los prompts del sistema y la plantilla.
    
    Args:
        ruta_system (Path): Ruta al archivo del prompt del sistema
        ruta_template (Path): Ruta al archivo de la plantilla de prompts
        
    Returns:
        tuple: (system_prompt, template_prompt)
    """
    try:
        system_prompt = cargar_archivo_externo(ruta_system)
        template_prompt = cargar_archivo_externo(ruta_template)
        print("✅ Prompts cargados correctamente")
        return system_prompt, template_prompt
    except Exception as e:
        print(f"❌ Error al cargar prompts: {str(e)}")
        raise
