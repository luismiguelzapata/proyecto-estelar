"""
STORY_STORAGE.PY - Guardado de historias y escenas

Guarda la historia generada en disco con toda la información de tokens,
y opcionalmente lanza el scene_generator para crear los prompts de video IA.

Crea la estructura:
  outputs/historias/revision/
    └── TITULO/
        ├── TITULO-YYYYMMDD-HHMMSS.txt   ← historia completa + tokens
        └── prompts-scenas/
            ├── escena1.md               ← prompt enriquecido para video IA
            ├── escenaN.md
            ├── RESUMEN_FINAL.md         ← reporte de coherencia
            └── coherence_report_v1.json
"""

from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import json

from config.config import (
    OUTPUTS_HISTORIAS_DIR,
    TIMESTAMP_FORMAT,
    DATETIME_FORMAT,
    JSON_INPUT_FILE,
)
from .utils import (
    extraer_titulo_historia,
    extraer_escenas_historia,
    generar_prompt_imagen_escena,
    generar_prompt_video_escena,
    normalizar_nombre_archivo,
)


def guardar_escenas_markdown(
    escenas: List[str],
    historia_dict: Dict[str, Any],
    ruta_prompts: Path,
) -> List[Path]:
    """
    Crea un archivo .md por cada escena con sus prompts de imagen y video.

    Args:
        escenas:       lista de descripciones de escenas
        historia_dict: diccionario completo de la historia
        ruta_prompts:  directorio donde guardar los .md

    Returns:
        lista de rutas creadas
    """
    ruta_prompts.mkdir(parents=True, exist_ok=True)
    rutas = []

    for i, descripcion in enumerate(escenas, 1):
        prompt_img   = generar_prompt_imagen_escena(i, descripcion, historia_dict)
        prompt_video = generar_prompt_video_escena(i, descripcion, historia_dict)

        contenido = (
            f"# Escena {i}\n\n"
            f"## Descripción de la Escena\n{descripcion}\n\n"
            f"---\n\n"
            f"## 🎬 Prompt para Generar Imagen\n\n{prompt_img}\n\n"
            f"---\n\n"
            f"## 🎥 Prompt para Generar Video\n\n{prompt_video}\n\n"
            f"---\n"
        )

        ruta = ruta_prompts / f"escena{i}.md"
        ruta.write_text(contenido, encoding="utf-8")
        rutas.append(ruta)
        print(f"  ✅ escena{i}.md")

    return rutas


def _formatear_tokens(historia_dict: Dict[str, Any]) -> str:
    """Genera el bloque de información de tokens para el archivo .txt"""
    tokens = historia_dict.get("tokens", {})
    costo  = historia_dict.get("costo_estimado_usd", 0.0)

    if not tokens:
        return ""

    return (
        f"\n{'='*70}\n"
        f"📊 CONSUMO DE TOKENS\n"
        f"{'='*70}\n"
        f"  Tokens de entrada   (prompt):     {tokens.get('prompt', 0):>10,}\n"
        f"  Tokens de salida    (completion): {tokens.get('completion', 0):>10,}\n"
        f"  {'─'*45}\n"
        f"  TOTAL TOKENS:                     {tokens.get('total', 0):>10,}\n"
        f"  Costo estimado:                   ${costo:>10.4f} USD\n"
        f"{'='*70}\n"
        f"  ℹ️  Los costos son estimaciones basadas en precios públicos de OpenAI.\n"
        f"  ℹ️  Consulta logs/token_usage.json para el historial acumulado.\n"
    )


def guardar_historia(
    historia_dict: Dict[str, Any],
    carpeta_salida: Optional[str] = None,
    generar_escenas_video: bool = True,
    characters_json_path: Optional[str] = None,
    coherence_threshold: int = 85,
) -> Optional[Dict[str, Any]]:
    """
    Guarda la historia generada y lanza el generador de escenas para video IA.

    Estructura generada:
        TITULO/
        ├── TITULO-YYYYMMDD-HHMMSS.txt   ← historia + tokens
        └── prompts-scenas/
            ├── escena1.md               ← prompt enriquecido para video IA
            ├── escenaN.md
            ├── RESUMEN_FINAL.md         ← reporte de coherencia
            └── coherence_report_v1.json

    Args:
        historia_dict:         resultado de generar_historia_aleatoria()
        carpeta_salida:        ruta base (usa OUTPUTS_HISTORIAS_DIR si es None)
        generar_escenas_video: si True, lanza scene_generator automáticamente
        characters_json_path:  ruta al characters.json
                               (si es None, construye el dict desde los elementos)
        coherence_threshold:   umbral de coherencia para el agente editor (default: 85)

    Returns:
        dict con rutas y metadata completa, o None si hubo error
    """
    try:
        contenido = historia_dict.get("historia", "")

        titulo    = extraer_titulo_historia(contenido)
        timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)

        # Resolver carpeta base
        if carpeta_salida:
            ruta_base = Path(carpeta_salida)
            if not ruta_base.is_absolute():
                ruta_base = Path(__file__).parent.parent.parent / carpeta_salida
        else:
            ruta_base = OUTPUTS_HISTORIAS_DIR

        ruta_dir = ruta_base / titulo
        ruta_dir.mkdir(parents=True, exist_ok=True)

        # ── 1. Archivo principal .txt ──────────────────────────────────────
        nombre_archivo = f"{titulo}-{timestamp}.txt"
        ruta_archivo   = ruta_dir / nombre_archivo
        elementos      = historia_dict.get("elementos", {})

        elementos_str = ""
        for k, v in elementos.items():
            if k == "personaje_secundario" and isinstance(v, dict):
                elementos_str += f"  {k}: {v.get('nombre', '?')}\n"
            else:
                elementos_str += f"  {k}: {v}\n"

        contenido_final = (
            f"{'='*70}\n"
            f"HISTORIA GENERADA — KIRA Y TOBY\n"
            f"{'='*70}\n"
            f"Fecha y hora: {datetime.now().strftime(DATETIME_FORMAT)}\n"
            f"Modelo: {historia_dict.get('modelo', 'gpt-4o')}\n"
            f"{'='*70}\n\n"
            f"{contenido}\n\n"
            f"{'='*70}\n"
            f"ELEMENTOS UTILIZADOS:\n"
            f"{'='*70}\n"
            f"{elementos_str}"
            f"{_formatear_tokens(historia_dict)}"
        )

        ruta_archivo.write_text(contenido_final, encoding="utf-8")
        print(f"\n✅ Historia guardada: {ruta_archivo}")

        historia_dict["ruta_historia_dir"] = ruta_dir
        ruta_escenas = ruta_dir / "escenas"

        resultado_escenas = {}

        # ── 2. Generar prompts de escenas para video IA ────────────────────
        if generar_escenas_video:
            print(f"\n{'─'*60}")
            print("  🎬 Iniciando generador de escenas para video IA...")
            print(f"{'─'*60}")

            characters_data = _build_characters_data(
                elementos, characters_json_path
            )

            try:
                from .scene_generator import generar_escenas_desde_historia

                resultado_escenas = generar_escenas_desde_historia(
                    story_text=contenido_final,   # el .txt completo con cabecera
                    characters_data=characters_data,
                    output_dir=ruta_escenas,
                    threshold=coherence_threshold,
                    historia_titulo=titulo,
                )
            except Exception as e:
                print(f"\n  ⚠️  Error en scene_generator: {e}")
                print("  → Se generarán los prompts básicos como respaldo...\n")
                _guardar_escenas_basicas(contenido, historia_dict, ruta_escenas)
        else:
            # Solo prompts básicos (sin agente de coherencia)
            escenas = extraer_escenas_historia(contenido)
            if escenas:
                print(f"\n📝 Generando {len(escenas)} prompts básicos de escenas...")
                _guardar_escenas_basicas(contenido, historia_dict, ruta_escenas)

        return {
            "ruta_historia":      str(ruta_archivo),
            "ruta_directorio":    str(ruta_dir),
            "ruta_escenas":       str(ruta_escenas),
            "titulo":             titulo,
            "timestamp":          timestamp,
            "elementos":          elementos,
            "historia":           contenido,
            "tokens":             historia_dict.get("tokens", {}),
            "costo_estimado_usd": historia_dict.get("costo_estimado_usd", 0.0),
            "escenas":            resultado_escenas,
        }

    except Exception as e:
        print(f"\n❌ Error al guardar la historia: {e}")
        return None


# ── Helpers internos ──────────────────────────────────────────────────────────

def _build_characters_data(
    elementos: Dict[str, Any],
    characters_json_path: Optional[str],
) -> dict:
    """
    Construye el dict de personajes para el scene_generator.

    Prioridad:
      1. characters_json_path (si se pasa explícitamente)
      2. JSON_INPUT_FILE del proyecto (inputs.opt2.json) para los secundarios
      3. Fallback mínimo construido desde los elementos de la historia
    """

    # Opción 1: ruta explícita al characters.json
    if characters_json_path and Path(characters_json_path).exists():
        with open(characters_json_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # Opción 2: construir desde el JSON del proyecto
    personaje_secundario = elementos.get("personaje_secundario", {})

    # Personajes principales fijos de Kira y Toby
    principales = [
        {
            "nombre": "Kira",
            "species": "perro (Shiba Inu inspired)",
            "fur_color": "#FFF9D4",
            "eye_color": "#5C4033",
            "accessory": "heart-shaped spot on RIGHT cheek only, peach-orange #FFB380",
            "forbidden_changes": "no cambiar color amarillo pastel, no quitar marca de corazón",
        },
        {
            "nombre": "Toby",
            "species": "perro (Husky inspired)",
            "fur_color": "#E8E3F0",
            "eye_color": "HETEROCHROMIA: left #6BB6D6 blue, right #8B6F47 brown",
            "accessory": "lightning bolt on left flank #A8D8EA, neck mane #D4C9E0",
            "forbidden_changes": "no cambiar heterocromía, no quitar rayo del costado",
        },
    ]

    secundarios = [personaje_secundario] if isinstance(personaje_secundario, dict) else []

    return {
        "personajesPrincipales":  principales,
        "personajesSecundarios":  secundarios,
    }


def _guardar_escenas_basicas(
    contenido: str,
    historia_dict: Dict[str, Any],
    ruta_prompts: Path,
) -> List[Path]:
    """Genera prompts básicos de escenas (respaldo sin agente de coherencia)."""
    escenas = extraer_escenas_historia(contenido)
    return guardar_escenas_markdown(escenas, historia_dict, ruta_prompts)
