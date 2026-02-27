from pathlib import Path
from typing import Dict, Any, List, Optional
from config.personajes import PERSONAJES
from modules.image_generator import generar_imagenes_escena

# ----------------------
# Funciones auxiliares
# ----------------------
def agregar_descripciones_principales(prompt_base: str) -> str:
    kira_desc = PERSONAJES.get("kira", "")
    toby_desc = PERSONAJES.get("toby", "")
    return f"{prompt_base}\n\n--- DESCRIPCIÓN DE PERSONAJES PRINCIPALES ---\n{kira_desc}\n{toby_desc}"

def construir_prompt_imagen_escena(descripcion_escena: str,
                                   locacion: str,
                                   personaje_secundario_desc: str,
                                   elemento_destacado: Optional[str] = None) -> str:
    prompt_base = f"Escena: {descripcion_escena}\nLocación: {locacion}\nPersonaje secundario: {personaje_secundario_desc}\n"
    if elemento_destacado:
        prompt_base += f"Elemento destacado: {elemento_destacado}\n"
    return agregar_descripciones_principales(prompt_base)

def construir_prompt_video_escena(descripcion_escena: str,
                                  locacion: str,
                                  personaje_secundario_desc: str,
                                  acciones: Optional[List[str]] = None,
                                  elemento_destacado: Optional[str] = None,
                                  duracion: str = "15-30 segundos") -> str:
    prompt_base = f"VIDEO ANIMADO - Escena\nDescripción: {descripcion_escena}\nDuración: {duracion}\nLocación: {locacion}\nPersonaje secundario: {personaje_secundario_desc}\n"
    if acciones:
        prompt_base += "Acciones dinámicas:\n" + "\n".join([f"- {a}" for a in acciones]) + "\n"
    if elemento_destacado:
        prompt_base += f"Elemento destacado: {elemento_destacado}\n"
    prompt_base += "\nEstilo: Película animada 3D de alta calidad, dirigida a audiencia infantil\nIluminación: cálida, dorada, mágica, con profundidad y realismo\nMúsica: orquestal suave, caprichosa y aventurera\nCalidad: 4K, animación suave y emotiva\n"
    return agregar_descripciones_principales(prompt_base)

# ----------------------
# Funciones principales
# ----------------------
def guardar_historia(historia: Dict[str, Any], ruta_markdown: Path):
    """Guarda la historia completa en un markdown estructurado"""
    ruta_markdown.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta_markdown, 'w', encoding='utf-8') as f:
        for idx, escena in enumerate(historia.get("escenas", []), start=1):
            f.write(f"# Escena {idx}\n\n")
            f.write(f"## Descripción de la Escena\n{escena['descripcion']}\n\n")
            # Prompt imagen
            f.write("---\n\n## 🎬 Prompt para Generar Imagen\n")
            f.write(construir_prompt_imagen_escena(
                escena['descripcion'],
                escena.get('locacion', 'Lugar indefinido'),
                escena.get('personaje_secundario_desc', ''),
                escena.get('elemento_destacado')
            ))
            # Prompt video
            f.write("\n\n---\n\n## 🎥 Prompt para Generar Video\n")
            f.write(construir_prompt_video_escena(
                escena['descripcion'],
                escena.get('locacion', 'Lugar indefinido'),
                escena.get('personaje_secundario_desc', ''),
                acciones=escena.get('acciones'),
                elemento_destacado=escena.get('elemento_destacado'),
                duracion=escena.get('duracion', '15-30 segundos')
            ))
            f.write("\n\n---\n\n")

def generar_imagenes_escenas(historia: Dict[str, Any], generar_tres_vistas: bool = True):
    """Genera imágenes para cada escena usando image_generator"""
    resultados = []
    for escena in historia.get("escenas", []):
        personaje_secundario_dict = escena.get("personaje_secundario_dict")
        if personaje_secundario_dict:
            resultado = generar_imagenes_escena({"elementos": {
                "personaje_secundario_nombre": personaje_secundario_dict.get("nombre"),
                "personaje_secundario": personaje_secundario_dict
            }}, generar_tres_vistas=generar_tres_vistas)
            resultados.append(resultado)
    return resultados