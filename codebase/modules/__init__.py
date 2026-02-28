"""
Módulos del proyecto Estelar
"""

from .data_loader import cargar_datos_historias, cargar_archivo_externo
from .story_generator import (
    generar_elementos_historia,
    generar_historia_aleatoria,
    inicializar_generador,
)
from .story_storage import guardar_historia, guardar_escenas_markdown
from .image_generator import (
    generar_imagen_personaje,
    generar_imagen_personaje_con_prompt,
    generar_tres_vistas_personaje,
    generar_imagenes_escena,
    crear_imagen_placeholder,
)
from .utils import (
    obtener_nombre_personaje,
    extraer_titulo_historia,
    extraer_escenas_historia,
    generar_prompt_imagen_escena,
    generar_prompt_video_escena,
)
from .token_tracker import tracker

__all__ = [
    # Data loader
    "cargar_datos_historias",
    "cargar_archivo_externo",
    # Story generator
    "generar_elementos_historia",
    "generar_historia_aleatoria",
    "inicializar_generador",
    # Story storage
    "guardar_historia",
    "guardar_escenas_markdown",
    # Image generator
    "generar_imagen_personaje",
    "generar_imagen_personaje_con_prompt",
    "generar_tres_vistas_personaje",
    "generar_imagenes_escena",
    "crear_imagen_placeholder",
    # Utils
    "obtener_nombre_personaje",
    "extraer_titulo_historia",
    "extraer_escenas_historia",
    "generar_prompt_imagen_escena",
    "generar_prompt_video_escena",
    # Token tracker
    "tracker",
]
