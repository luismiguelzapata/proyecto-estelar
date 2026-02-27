"""
Módulo para enriquecer descripciones de escenas
Convierte frases simples en acciones visuales más detalladas
"""

from typing import Dict


def enriquecer_descripcion_escena(
    descripcion_simple: str,
    historia_dict: Dict,
    estado_visual: Dict
) -> str:
    """
    Expande una descripción corta en una descripción
    más cinematográfica pero sin entrar aún en cámara/iluminación técnica.
    """

    lugar = historia_dict.get("elementos", {}).get("lugar", "")
    fenomeno = historia_dict.get("elementos", {}).get("fenomeno", "")
    sentimiento_kira = historia_dict.get("elementos", {}).get("sentimiento_kira", "")
    sentimiento_toby = historia_dict.get("elementos", {}).get("sentimiento_toby", "")

    descripcion = f"""
Acción principal:
{descripcion_simple}.

Entorno:
La escena ocurre en {lugar}. {fenomeno if fenomeno else ''}

Comportamiento:
Kira se mueve de forma {sentimiento_kira}.
Toby observa el entorno mostrando una actitud {sentimiento_toby}.
"""

    return descripcion.strip()