"""
Funciones auxiliares del proyecto Estelar
"""

import re
from typing import Dict, List, Any, Union


def obtener_nombre_personaje(personaje_dict: Union[Dict, str]) -> str:
    """
    Extrae el nombre del personaje desde el dict.
    Si recibe un string (compatibilidad), lo devuelve directamente.
    
    Args:
        personaje_dict: dict o str con datos del personaje
        
    Returns:
        str: Nombre del personaje
    """
    if isinstance(personaje_dict, dict):
        return personaje_dict.get("nombre", "personaje desconocido")
    else:
        return str(personaje_dict)


def extraer_titulo_historia(contenido_historia: str) -> str:
    """
    Extrae el título de la historia desde el contenido generado.
    Busca el patrón: **TÍTULO:** [Nombre]
    
    Args:
        contenido_historia (str): Contenido completo de la historia
        
    Returns:
        str: Título limpio y formateado para usar en nombre de archivo
    """
    # Buscar el patrón **TÍTULO:** seguido del nombre
    match = re.search(r'\*\*TÍTULO:\*\*\s*(.+?)(?:\n|\*\*)', contenido_historia)
    if match:
        titulo = match.group(1).strip()
        # Reemplazar espacios y caracteres especiales por guiones bajos
        titulo = re.sub(r'[^a-záéíóúñA-ZÁÉÍÓÚÑ0-9]', '_', titulo)
        # Limpiar múltiples guiones bajos consecutivos
        titulo = re.sub(r'_+', '_', titulo)
        # Eliminar guiones bajos del inicio y final
        titulo = titulo.strip('_')
        return titulo
    return "Historia_Sin_Titulo"


def extraer_escenas_historia(contenido_historia: str) -> List[str]:
    """
    Extrae las descripciones de escenas del contenido generado.
    Busca la sección **ESCENAS:** y extrae cada línea numerada.
    
    Args:
        contenido_historia (str): Contenido completo de la historia
        
    Returns:
        list: Lista de descripciones de escenas
    """
    escenas = []
    # Buscar la sección ESCENAS: y extraer cada línea
    match = re.search(r'\*\*ESCENAS:\*\*(.+?)(?:\n\n|$)', contenido_historia, re.DOTALL)
    if match:
        texto_escenas = match.group(1)
        # Extraer líneas numeradas
        lineas = re.findall(r'\d+\.\s*(.+?)(?=\n\d+\.|$)', texto_escenas, re.DOTALL)
        escenas = [linea.strip() for linea in lineas if linea.strip()]
    return escenas


def normalizar_nombre_archivo(texto: str) -> str:
    """
    Normaliza texto para usarlo como nombre de archivo.
    Reemplaza caracteres especiales y múltiples espacios.
    
    Args:
        texto (str): Texto a normalizar
        
    Returns:
        str: Texto normalizado
    """
    # Reemplazar caracteres especiales por guiones bajos
    normalizado = re.sub(r'[^a-záéíóúñA-ZÁÉÍÓÚÑ0-9]', '_', texto)
    # Eliminar guiones bajos múltiples
    normalizado = re.sub(r'_+', '_', normalizado)
    # Eliminar guiones bajos del inicio y final
    normalizado = normalizado.strip('_')
    return normalizado


def generar_prompt_imagen_escena(num_escena: int, descripcion_escena: str, historia_dict: Dict[str, Any]) -> str:
    """
    Genera un prompt en español para generar una imagen de la escena.
    Sigue el estilo de película animada cinématica para audiencia infantil.
    Incluye características del personaje secundario para consistencia visual.
    
    Args:
        num_escena (int): Número de la escena
        descripcion_escena (str): Descripción de la escena
        historia_dict (dict): Diccionario con información de la historia
        
    Returns:
        str: Prompt para generar imagen
    """
    lugar = historia_dict.get("elementos", {}).get("lugar", "escena mágica")
    color_obj = historia_dict.get("elementos", {}).get("color_objeto", "mágico")
    objeto = historia_dict.get("elementos", {}).get("objeto_principal", "objeto")
    
    # Extraer características del personaje secundario
    personaje_sec = historia_dict.get("elementos", {}).get("personaje_secundario", {})
    nombre_personaje = obtener_nombre_personaje(personaje_sec)
    
    # Construir descripción del personaje secundario
    caracteristicas_personaje = ""
    if isinstance(personaje_sec, dict):
        species = personaje_sec.get("species", "")
        body_shape = personaje_sec.get("body_shape", "")
        height_ratio = personaje_sec.get("height_ratio", "")
        accessory = personaje_sec.get("accessory", "")
        forbidden = personaje_sec.get("forbidden_changes", "")
        
        # Agrupar colores por tipo
        colores_dict = {}
        for key in personaje_sec.keys():
            if "_color" in key or "color" in key:
                color_key = key.replace("_color", "").replace("color", "").strip("_")
                colores_dict[color_key] = personaje_sec[key]
        
        colores_str = ", ".join([f"{k}: {v}" for k, v in colores_dict.items()])
        
        caracteristicas_personaje = f"""
PERSONAJE SECUNDARIO - {nombre_personaje.upper()}:
- Especie: {species}
- Altura: {height_ratio}
- Forma del cuerpo: {body_shape}
- Colores: {colores_str}
- Accesorios: {accessory}
- PROHIBIDO (para consistencia visual): {forbidden}"""
    else:
        caracteristicas_personaje = f"PERSONAJE SECUNDARIO: {nombre_personaje}"
    
    prompt = f"""Escena cinematográfica de película animada.

Estilo: Similar a una película de animación 3D de alta calidad, mágica y acogedora.

Escena {num_escena}: {descripcion_escena}

Lugar: {lugar} con iluminación cálida de hora dorada, luz suave y soñadora.

{caracteristicas_personaje}

ELEMENTO DESTACADO: {objeto} de color {color_obj}

Atmósfera: Calorosa, mágica y envolvente. Música orquestal suave, tono caprichoso y aventurero.

Calidad técnica: Cinemática, animación altamente detallada, 4K, atmósfera emotiva y edificante.

Perfecto para una audiencia infantil."""
    
    return prompt


def generar_prompt_video_escena(num_escena: int, descripcion_escena: str, historia_dict: Dict[str, Any]) -> str:
    """
    Genera un prompt en español para generar un video de la escena.
    Incluye características del personaje secundario para consistencia visual.
    
    Args:
        num_escena (int): Número de la escena
        descripcion_escena (str): Descripción de la escena
        historia_dict (dict): Diccionario con información de la historia
        
    Returns:
        str: Prompt para generar video
    """
    lugar = historia_dict.get("elementos", {}).get("lugar", "escena mágica")
    
    # Extraer características del personaje secundario
    personaje_sec = historia_dict.get("elementos", {}).get("personaje_secundario", {})
    nombre_personaje = obtener_nombre_personaje(personaje_sec)
    
    # Extraer accesorios y detalles del personaje
    accessory = ""
    if isinstance(personaje_sec, dict):
        accessory = personaje_sec.get("accessory", "")
    
    prompt = f"""VIDEO ANIMADO - Escena {num_escena}

Descripción: {descripcion_escena}

Duración: 15-30 segundos

Estilo: Película animada 3D de alta calidad, dirigida a audiencia infantil.

Locación: {lugar}

PERSONAJES EN PANTALLA:
- Kira y Toby interactuando de forma dinámica y expresiva
- {nombre_personaje} (con {accessory if accessory else 'características visuales consistentes'})

Elementos de cámara:
- Transiciones suaves
- Zoom progresivo cuando es necesario
- Movimiento de cámara envolvente

Sonido:
- Música de fondo: orquestal, suave y aventurera
- Efectos de sonido: subtiles y mágicos

Iluminación: Cálida, dorada, mágica. Profundidad y realismo.

Qualidad: 4K, animación suave, atmósfera emotiva y edificante."""
    
    return prompt
