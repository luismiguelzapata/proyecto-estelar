"""
UTILS.PY - Funciones auxiliares del proyecto Estelar
"""

import re
from typing import Dict, List, Any, Union


def obtener_nombre_personaje(personaje: Union[Dict, str]) -> str:
    """Extrae el nombre de un personaje (dict o string)."""
    if isinstance(personaje, dict):
        return personaje.get("nombre", "personaje desconocido")
    return str(personaje)


def normalizar_nombre_archivo(texto: str) -> str:
    """Convierte texto en nombre de archivo seguro."""
    n = re.sub(r"[^a-záéíóúñA-ZÁÉÍÓÚÑ0-9]", "_", texto)
    n = re.sub(r"_+", "_", n)
    return n.strip("_")


def extraer_titulo_historia(contenido: str) -> str:
    """
    Extrae el título de la historia.
    Soporta dos formatos que GPT puede generar:
      - **TÍTULO:** El nombre        (negrita, formato pedido en el prompt)
      - ### TÍTULO: El nombre        (heading markdown, formato alternativo)
    """
    match = re.search(
        r"(?:\*\*TÍTULO:\*\*|#{1,3}\s*TÍTULO:)\s*(.+?)(?:\n|$|\*\*)",
        contenido,
    )
    if match:
        titulo = match.group(1).strip()
        return normalizar_nombre_archivo(titulo) or "Historia_Sin_Titulo"
    return "Historia_Sin_Titulo"


def extraer_escenas_historia(contenido: str) -> List[str]:
    """
    Extrae las escenas de la sección ESCENAS.
    Soporta **ESCENAS:** y ### ESCENAS: (con o sin línea en blanco tras el header).
    Captura hasta el primer separador --- o bloque === o fin de texto.
    """
    match = re.search(
        r"(?:\*\*ESCENAS:\*\*|#{1,3}\s*ESCENAS:)\s*\n+(.*?)(?=\n---|\n={10,}|\Z)",
        contenido,
        re.DOTALL,
    )
    if not match:
        return []
    texto = match.group(1)
    lineas = re.findall(r"\d+\.\s*(.+?)(?=\n\d+\.|$)", texto, re.DOTALL)
    return [l.strip() for l in lineas if l.strip()]


def generar_prompt_imagen_escena(
    num_escena: int,
    descripcion: str,
    historia_dict: Dict[str, Any],
) -> str:
    """Genera prompt de imagen para una escena específica."""
    elementos       = historia_dict.get("elementos", {})
    lugar           = elementos.get("lugar", "escena mágica")
    color_obj       = elementos.get("color_objeto", "mágico")
    objeto          = elementos.get("objeto_principal", "objeto")
    personaje_sec   = elementos.get("personaje_secundario", {})
    nombre_p        = obtener_nombre_personaje(personaje_sec)

    # Construir descripción del personaje
    caract = ""
    if isinstance(personaje_sec, dict):
        species     = personaje_sec.get("species", "")
        body_shape  = personaje_sec.get("body_shape", "")
        height      = personaje_sec.get("height_ratio", "")
        accessory   = personaje_sec.get("accessory", "")
        forbidden   = personaje_sec.get("forbidden_changes", "")
        colores     = {
            k.replace("_color", "").strip("_"): v
            for k, v in personaje_sec.items()
            if "color" in k
        }
        colores_str = ", ".join(f"{k}: {v}" for k, v in colores.items())

        caract = (
            f"\nPERSONAJE SECUNDARIO — {nombre_p.upper()}:\n"
            f"- Especie: {species}\n"
            f"- Altura relativa: {height}\n"
            f"- Forma: {body_shape}\n"
            f"- Colores: {colores_str}\n"
            f"- Accesorio: {accessory}\n"
            f"- ⚠️ PROHIBIDO cambiar: {forbidden}"
        )
    else:
        caract = f"PERSONAJE SECUNDARIO: {nombre_p}"

    return (
        f"Escena cinematográfica de película animada 3D.\n\n"
        f"Escena {num_escena}: {descripcion}\n\n"
        f"Lugar: {lugar}, iluminación cálida de hora dorada.\n"
        f"{caract}\n\n"
        f"Elemento destacado: {objeto} de color {color_obj}\n\n"
        f"Estilo: Pixar/Disney 3D CGI, 4K, atmósfera mágica y acogedora, "
        f"perfecta para audiencia infantil 3-6 años."
    )


def generar_prompt_video_escena(
    num_escena: int,
    descripcion: str,
    historia_dict: Dict[str, Any],
) -> str:
    """Genera prompt de video para una escena específica."""
    elementos     = historia_dict.get("elementos", {})
    lugar         = elementos.get("lugar", "escena mágica")
    personaje_sec = elementos.get("personaje_secundario", {})
    nombre_p      = obtener_nombre_personaje(personaje_sec)
    accessory     = personaje_sec.get("accessory", "") if isinstance(personaje_sec, dict) else ""

    return (
        f"VIDEO ANIMADO — Escena {num_escena}\n\n"
        f"Descripción: {descripcion}\n\n"
        f"Duración: 15-30 segundos\n"
        f"Estilo: Película animada 3D Pixar/Disney, audiencia infantil 3-6 años.\n"
        f"Locación: {lugar}\n\n"
        f"PERSONAJES:\n"
        f"- Kira y Toby interactuando de forma dinámica y expresiva\n"
        f"- {nombre_p}"
        + (f" (con {accessory})" if accessory else "") + "\n\n"
        f"Cámara: transiciones suaves, zoom progresivo, movimiento envolvente.\n"
        f"Sonido: orquestal suave, efectos mágicos sutiles.\n"
        f"Iluminación: cálida, dorada, mágica. 4K, atmósfera emotiva."
    )
