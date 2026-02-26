"""
Módulo generador de imágenes
Maneja la generación de imágenes usando Gemini Flash 2.0
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
import base64
import requests

from config.config import (
    GOOGLE_API_KEY,
    GEMINI_MODEL,
    ASSETS_PERSONAJES_DIR,
    get_personaje_dir,
    get_personaje_image_path
)
from .utils import obtener_nombre_personaje, normalizar_nombre_archivo


# ========================================
# CONFIGURACIÓN DE POSES
# ========================================

POSES_PERSONAJE = {
    "front": {
        "nombre": "Vista Frontal",
        "descripcion": "full body front view, centered composition",
        "archivo": "front.png"
    },
    "side": {
        "nombre": "Perfil Derecho",
        "descripcion": "left side profile view, full body visible from nose to tail tip",
        "archivo": "side.png"
    },
    "quarter": {
        "nombre": "Vista 3/4",
        "descripcion": "three-quarter view at 45-degree angle, full body visible",
        "archivo": "quarter.png"
    # },
    # "back": {
    #     "nombre": "Vista Trasera",
    #     "descripcion": "full body back view, character facing away from camera",
    #     "archivo": "back.png"
    # },
    # "pose_happy": {
    #     "nombre": "Pose Feliz",
    #     "descripcion": "jumping happily with arms raised",
    #     "archivo": "happy.png"
    # },
    # "pose_running": {
    #     "nombre": "Pose Corriendo",
    #     "descripcion": "running forward, dynamic pose",
    #     "archivo": "running.png"
    }
}


def construir_prompt_vista(prompt_base: str, descripcion_pose: str) -> str:
    """
    Construye un prompt estructurado y consistente para cada pose
    """
    return f"""
    {prompt_base}

    STYLE REQUIREMENTS:
    - Pure white background
    - Studio lighting
    - No shadows on background
    - Same character proportions
    - Same clothing and colors
    - Same facial expression
    - No new accessories
    - Character turnaround consistency
    - High detail 3D cartoon render
    - Pixar-style rendering
    - Full body visible

    POSE REQUIREMENT:
    The pose MUST be: {descripcion_pose}
    """


def generar_imagen_personaje_con_prompt(nombre_personaje: str, prompt_3d: str) -> Optional[Path]:
    """
    Genera UNA imagen de un personaje usando el prompt 3D proporcionado.
    Nota: Para generar 3 vistas, usa generar_tres_vistas_personaje()
    
    Args:
        nombre_personaje (str): Nombre del personaje
        prompt_3d (str): Prompt detallado para generar la imagen 3D
        
    Returns:
        Path: Ruta donde se guardó la imagen, o None si hubo error
    """
    
    if not GOOGLE_API_KEY:
        print("❌ GOOGLE_API_KEY no configurada. Agrega tu clave de API de Google.")
        return None
    
    try:
        # Normalizar nombre del personaje
        nombre_normalizado = normalizar_nombre_archivo(nombre_personaje)
        
        # Obtener directorio
        personaje_dir = get_personaje_dir(nombre_personaje)
        
        print(f"\n🎨 Generando imagen para: {nombre_personaje}")
        print(f"📂 Directorio: {personaje_dir}")
        
        # Llamar a la API de Gemini
        imagen_bytes = _llamar_gemini_imagen(prompt_3d)
        
        if imagen_bytes is None:
            print(f"❌ No se pudo generar imagen para {nombre_personaje}")
            return None
        
        # Guardar imagen (single image)
        imagen_path = personaje_dir / f"{nombre_normalizado}.png"
        with open(imagen_path, 'wb') as f:
            f.write(imagen_bytes)
        
        print(f"✅ Imagen guardada en: {imagen_path}")
        return imagen_path
        
    except Exception as e:
        print(f"❌ Error al generar imagen de {nombre_personaje}: {str(e)}")
        return None


def generar_tres_vistas_personaje(nombre_personaje: str, prompt_3d: str) -> Dict[str, Optional[Path]]:
    """
    Genera TRES vistas (front, side, quarter) de un personaje con poses específicas.
    Guarda las imágenes en: /assets/personajes/{nombre}/{front|side|quarter}.png
    
    Args:
        nombre_personaje (str): Nombre del personaje
        prompt_3d (str): Prompt detallado base para generar la imagen 3D
        
    Returns:
        dict: Diccionario con rutas de las 3 imágenes generadas
              Ejemplo: {"front": Path(...), "side": Path(...), "quarter": Path(...)}
    """
    
    if not GOOGLE_API_KEY:
        print("❌ GOOGLE_API_KEY no configurada. Agrega tu clave de API de Google.")
        return {}
    
    try:
        # Obtener directorio
        personaje_dir = get_personaje_dir(nombre_personaje)
        
        print(f"\n🎨 Generando 3 vistas para: {nombre_personaje}")
        print(f"📂 Directorio: {personaje_dir}")
        
        imagenes_generadas = {}
        
        # Generar cada vista
        for pose_key, pose_info in POSES_PERSONAJE.items():
            print(f"\n  📸 Vista: {pose_info['nombre']}...")
            
            # Agregar instrucción de pose al prompt
            prompt_con_pose = construir_prompt_vista(
                prompt_3d,
                pose_info["descripcion"]
            )
            
            # Llamar a Gemini
            imagen_bytes = _llamar_gemini_imagen(prompt_con_pose)
            
            if imagen_bytes is None:
                print(f"  ❌ No se pudo generar vista {pose_key}")
                imagenes_generadas[pose_key] = None
                continue
            
            # Guardar imagen con nombre específico
            imagen_path = personaje_dir / pose_info['archivo']
            with open(imagen_path, 'wb') as f:
                f.write(imagen_bytes)
            
            imagenes_generadas[pose_key] = imagen_path
            print(f"  ✅ {pose_info['nombre']} guardada en: {imagen_path}")
        
        return imagenes_generadas
        
    except Exception as e:
        print(f"❌ Error al generar vistas de {nombre_personaje}: {str(e)}")
        return {}


def generar_imagen_personaje(personaje_dict: Dict[str, Any], generar_tres_vistas: bool = True) -> Optional[Dict[str, Optional[Path]]]:
    """
    Genera imagen(s) de un personaje usando los datos del diccionario.
    Por defecto genera 3 vistas (front, side, quarter).
    
    Si generar_tres_vistas=False, genera solo una imagen.
    Si el personaje tiene campo 'prompt-3D', lo usa directamente.
    
    Args:
        personaje_dict (dict): Diccionario con datos del personaje
        generar_tres_vistas (bool): Si True genera 3 vistas, si False genera 1
        
    Returns:
        Dict o Path: 
            - Si generar_tres_vistas=True: Dict con rutas de las 3 imágenes
            - Si generar_tres_vistas=False: Path de la imagen única
            - None si hubo error
    """
    
    # Obtener nombre del personaje
    nombre = obtener_nombre_personaje(personaje_dict)
    
    # Si es string, no tiene prompt detallado
    if isinstance(personaje_dict, str):
        print(f"⚠️ {nombre} no tiene especificaciones 3D disponibles")
        return None
    
    # Verificar si tiene prompt 3D
    if 'prompt-3D' not in personaje_dict:
        print(f"⚠️ {nombre} no tiene campo 'prompt-3D'")
        return None
    
    prompt_3d = personaje_dict['prompt-3D']
    
    # Generar 3 vistas o 1 sola
    if generar_tres_vistas:
        return generar_tres_vistas_personaje(nombre, prompt_3d)
    else:
        return generar_imagen_personaje_con_prompt(nombre, prompt_3d)


def _llamar_gemini_imagen(prompt: str, output_format: str = "PNG") -> Optional[bytes]:
    """
    Llamada interna a Gemini usando el SDK moderno google-genai.
    Devuelve los bytes de la imagen generada listos para guardar en disco.

    Args:
        prompt (str): Prompt detallado para la generación de la imagen
        output_format (str): "PNG" o "JPEG" (por defecto PNG)

    Returns:
        bytes | None: Bytes de la imagen, o None si hubo error
    """
    try:
        from google import genai
        import base64
        import io
        from PIL import Image

        client = genai.Client(api_key=GOOGLE_API_KEY)
        IMAGE_MODEL = "imagen-4.0-fast-generate-001"

        response = client.models.generate_images(
            model=IMAGE_MODEL,
            prompt=prompt
        )

        if not response.generated_images:
            print("⚠️ No se generaron imágenes")
            return None

        image_obj = response.generated_images[0].image

        # =====> SDK moderno puede devolver la imagen en bytes o base64
        if hasattr(image_obj, "image_bytes") and image_obj.image_bytes:
            # Ya son bytes listos
            return image_obj.image_bytes
        elif hasattr(image_obj, "b64_json") and image_obj.b64_json:
            # Decodificar base64
            return base64.b64decode(image_obj.b64_json)
        elif hasattr(image_obj, "as_pil"):
            # Si tiene método as_pil(), convertir a bytes
            pil_img = image_obj.as_pil()
        else:
            # Intentar asumir que es PIL.Image
            pil_img = image_obj

        # Convertir PIL.Image a bytes
        buffer = io.BytesIO()
        pil_img.save(buffer, format=output_format.upper())
        return buffer.getvalue()

    except ImportError:
        print("⚠️ Pillow no está instalado. Ejecuta: pip install Pillow")
        return None
    except Exception as e:
        print(f"❌ Error al llamar Gemini: {e}")
        return None

def generar_imagenes_escena(historia_dict: Dict[str, Any], generar_tres_vistas: bool = True) -> Dict[str, Any]:
    """
    Genera imágenes de los personajes secundarios en una escena
    """
    try:
        elementos = historia_dict.get("elementos", {})
        
        # ✅ CORRECCIÓN: Usar el nombre del personaje, no el dict completo
        nombre_personaje = elementos.get("personaje_secundario_nombre")
        personaje_dict = elementos.get("personaje_secundario")
        
        if not nombre_personaje or not personaje_dict:
            print("❌ No se encontró personaje secundario")
            return {}
        
        # Obtener prompt 3D del personaje
        prompt_3d = personaje_dict.get("prompt-3D")
        if not prompt_3d:
            print(f"⚠️ El personaje '{nombre_personaje}' no tiene prompt-3D definido")
            return {}
        
        print(f"🎨 Generando imágenes para: {nombre_personaje}")
        
        # Generar las 3 vistas
        if generar_tres_vistas:
            vistas = generar_tres_vistas_personaje(nombre_personaje, prompt_3d)
            return {
                "personaje": nombre_personaje,
                "vistas": vistas,
                "total_imagenes": 3
            }
        else:
            imagen = generar_imagen_personaje_con_prompt(nombre_personaje, prompt_3d)
            return {
                "personaje": nombre_personaje,
                "imagen": imagen,
                "total_imagenes": 1
            }
    
    except Exception as e:
        print(f"❌ Error generando imágenes de escena: {e}")
        return {}


# Función auxiliar para crear imagen placeholder (para testing)
def crear_imagen_placeholder(nombre_personaje: str) -> Optional[Path]:
    """
    Crea una imagen placeholder para testing sin usar API.
    
    Args:
        nombre_personaje (str): Nombre del personaje
        
    Returns:
        Path: Ruta de la imagen creada
    """
    
    try:
        from PIL import Image, ImageDraw
        
        imagen_path = get_personaje_image_path(nombre_personaje)
        
        # Crear imagen simple
        img = Image.new('RGB', (400, 400), color='lightblue')
        draw = ImageDraw.Draw(img)
        
        # Dibujar texto
        nombre_normalizado = normalizar_nombre_archivo(nombre_personaje)
        draw.text((50, 180), f"{nombre_normalizado}", fill='black')
        
        img.save(imagen_path)
        print(f"✅ Imagen placeholder guardada: {imagen_path}")
        
        return imagen_path
        
    except ImportError:
        print("⚠️ Pillow no esta instalado. Usa: pip install Pillow")
        return None
    except Exception as e:
        print(f"❌ Error al crear imagen placeholder: {str(e)}")
        return None
