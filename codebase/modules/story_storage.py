"""
Módulo de almacenamiento de historias
Maneja la guardación de historias y escenas en archivos
"""

from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

from config.config import (
    OUTPUTS_HISTORIAS_DIR,
    TIMESTAMP_FORMAT,
    DATETIME_FORMAT
)
from .utils import extraer_titulo_historia, extraer_escenas_historia, generar_prompt_imagen_escena, generar_prompt_video_escena


def guardar_escenas_markdown(titulo: str, escenas: List[str], historia_dict: Dict[str, Any]) -> List[Path]:
    """
    Crea archivos pdf para cada escena con prompts de imagen y video.
    
    Args:
        titulo (str): Título formateado de la historia
        escenas (list): Lista de descripciones de escenas
        historia_dict (dict): Diccionario con información de la historia
        
    Returns:
        list: Lista de rutas de archivos creados
    """
    rutas_creadas = []
    
    try:
        # Crear carpeta prompts-scenas
        ruta_prompts = historia_dict["ruta_historia_dir"] / "prompts-scenas"
        ruta_prompts.mkdir(parents=True, exist_ok=True)
        
        # Crear archivo para cada escena
        for num_escena, descripcion_escena in enumerate(escenas, 1):
            nombre_archivo = f"escena{num_escena}.md"
            ruta_archivo = ruta_prompts / nombre_archivo
            
            # Generar prompts
            prompt_imagen = generar_prompt_imagen_escena(num_escena, descripcion_escena, historia_dict)
            prompt_video = generar_prompt_video_escena(num_escena, descripcion_escena, historia_dict)
            
            # Contenido del archivo markdown
            contenido_md = f"""# Escena {num_escena}

## Descripción de la Escena
{descripcion_escena}

---

## 🎬 Prompt para Generar Imagen

{prompt_imagen}

---

## 🎥 Prompt para Generar Video

{prompt_video}

---

"""
            
            # Guardar archivo
            with open(ruta_archivo, 'w', encoding='utf-8') as f:
                f.write(contenido_md)
            
            rutas_creadas.append(ruta_archivo)
            print(f"  ✅ {nombre_archivo} creado")
        
        return rutas_creadas
        
    except Exception as e:
        print(f"❌ Error al guardar escenas markdown: {e}")
        return []


def guardar_historia(
    historia_dict: Dict[str, Any],
    carpeta_salida: str = "outputs/historias/revision"
) -> Dict[str, str]:
    """
    Guarda la historia generada en una estructura de carpetas organizada.
    Crea: TITULO/TITULO-YYYYMMDD-HHMMSS.txt y TITULO/prompts-scenas/escenaN.md
    
    Args:
        historia_dict (dict): Diccionario con la historia generada
        carpeta_salida (str): Ruta de salida relativa o absoluta
        
    Returns:
        dict: Información sobre archivos guardados
    """
    try:
        # Extraer el contenido
        contenido = historia_dict.get("historia", "")
        
        # Extraer título y generar timestamp
        titulo = extraer_titulo_historia(contenido)
        timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)
        
        # Crear ruta de carpeta por título
        if Path(carpeta_salida).is_absolute():
            ruta_base = Path(carpeta_salida)
        else:
            # Ruta relativa desde el directorio del proyecto
            ruta_base = Path(__file__).parent.parent.parent / carpeta_salida
        
        ruta_historia_dir = ruta_base / titulo
        ruta_historia_dir.mkdir(parents=True, exist_ok=True)
        
        # Crear nombre de archivo
        nombre_archivo = f"{titulo}-{timestamp}.txt"
        ruta_archivo = ruta_historia_dir / nombre_archivo
        
        # Preparar contenido a guardar
        contenido_final = f"""{'='*80}
HISTORIA GENERADA - KIRA Y TOBY
{'='*80}
Fecha y hora: {datetime.now().strftime(DATETIME_FORMAT)}
{'='*80}

{contenido}

{'='*80}
ELEMENTOS UTILIZADOS:
{'='*80}
"""
        
        # Agregar elementos
        elementos = historia_dict.get("elementos", {})
        for key, value in elementos.items():
            if key == "personaje_secundario" and isinstance(value, dict):
                contenido_final += f"  {key}: {value.get('nombre', 'desconocido')}\n"
            else:
                contenido_final += f"  {key}: {value}\n"
        
        # Agregar tokens si está disponible
        if "tokens" in historia_dict:
            contenido_final += f"\n📊 Tokens utilizados: {historia_dict['tokens']}"
        
        # Guardar archivo principal
        with open(ruta_archivo, 'w', encoding='utf-8') as f:
            f.write(contenido_final)
        
        print(f"\n✅ Historia guardada en: {ruta_archivo}")
        
        # Extraer escenas y guardar archivos markdown
        escenas = extraer_escenas_historia(contenido)
        
        if escenas:
            print(f"\n📝 Generando {len(escenas)} archivos de escenas...")
            historia_dict["ruta_historia_dir"] = ruta_historia_dir
            rutas_escenas = guardar_escenas_markdown(titulo, escenas, historia_dict)
            print(f"\n✅ Carpeta de escenas creada en: {ruta_historia_dir}/prompts-scenas")
        else:
            print("⚠️ No se extrajeron escenas")
        
        return {
            "ruta_historia": str(ruta_archivo),
            "ruta_directorio": str(ruta_historia_dir),
            "titulo": titulo,
            "timestamp": timestamp,
            "elementos": elementos,  # ✅ Retornar elementos para generar imágenes
            "historia": contenido  # ✅ Retornar historia también
        }
        
    except Exception as e:
        print(f"\n❌ Error al guardar la historia: {e}")
        return None
