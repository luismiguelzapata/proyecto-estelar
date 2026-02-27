"""
Constructor de prompts optimizados para generación de video
Especializado para Google / Gemini
"""

from typing import Dict


def generar_prompt_video_google(
    num_escena: int,
    descripcion_enriquecida: str,
    historia_dict: Dict,
    personajes: Dict,
    estado_visual: Dict
) -> str:
    """
    Genera prompt optimizado para Google Nano Banana / Gemini
    garantizando consistencia multi-escena.
    """

    lugar = historia_dict.get("elementos", {}).get("lugar", "")
    objeto_magico = historia_dict.get("elementos", {}).get("objeto_magico", "")
    personaje_secundario = historia_dict.get("elementos", {}).get("personaje_secundario_nombre", "")

    prompt = f"""
ANIMATED 3D CINEMATIC SCENE – Escena {num_escena}

STYLE:
High quality Pixar/Disney style 3D animation.
Soft volumetric lighting.
Pastel cinematic color grading.
Ultra consistent character design. No redesign allowed.

SCENE DESCRIPTION:
{descripcion_enriquecida}

CHARACTERS:
Kira and Toby must maintain EXACT proportions, colors and facial features.
Do not alter fur colors.
Do not change eye colors.
Do not change body proportions.

SECONDARY CHARACTER:
{personaje_secundario}

MAGICAL ELEMENT:
{objeto_magico}

LOCATION:
{lugar}

LIGHTING:
{estado_visual.get("hora_dia", "soft daylight")}

CAMERA:
Gentle cinematic movement.
Soft focus depth of field.
Child-friendly composition.

DURATION:
15–20 seconds.

QUALITY:
4K, smooth animation, emotionally warm atmosphere.
"""
    return prompt.strip()