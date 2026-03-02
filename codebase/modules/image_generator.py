"""
IMAGE_GENERATOR.PY - Generador de imágenes con Google Imagen

Funcionalidades:
  1. Generar 3 vistas de personaje (front / side / quarter)
       → assets/personajes/{nombre-con-guiones}/front.png  side.png  quarter.png
       → SKIP automático si ya existen

  2. Generar ilustración de cuento para una escena específica
       → prompts-scenas/ilustracion_{N}.png
       → SKIP automático si ya existe
       → Prompt estilo libro ilustrado (sin ACTION, sin CAMERA, sin duración)
       → Incluye referencia visual completa de Kira, Toby y personaje secundario

Regla de normalización de nombres de personaje:
  El nombre en disco se obtiene con:  nombre.lower().replace(" ", "-")
  Ej: "hurón explorador" → "hurón-explorador"
  Misma lógica que get_personaje_dir() en config.py.
"""

import io
from pathlib import Path
from typing import Dict, Any, Optional

from config.config import (
    GOOGLE_API_KEY,
    RUNWAY_API_KEY,
    GEMINI_MODEL,
    IMAGE_MODEL,
    ASSETS_PERSONAJES_DIR,
    get_personaje_dir,
    get_personaje_image_path,
)
from .utils import obtener_nombre_personaje, normalizar_nombre_archivo
from .token_tracker import tracker


# ════════════════════════════════════════════════════════════════════════
# CONSTANTES
# ════════════════════════════════════════════════════════════════════════

POSES_PERSONAJE = {
    "front": {
        "nombre":      "Vista Frontal",
        "descripcion": "full body front view, centered composition, facing camera directly",
        "archivo":     "front.png",
    },
}


# ════════════════════════════════════════════════════════════════════════
# NORMALIZACIÓN — función única usada en todo el módulo
# ════════════════════════════════════════════════════════════════════════

def _nombre_a_carpeta(nombre_personaje: str) -> str:
    """
    Convierte el nombre de un personaje al nombre de carpeta en disco.
    Debe coincidir EXACTAMENTE con la lógica de get_personaje_dir() en config.py.

    Ejemplos:
      "hurón explorador"  → "hurón-explorador"
      "Conejito Blanco"   → "conejito-blanco"
      "León Mágico"       → "león-mágico"
    """
    return nombre_personaje.lower().replace(" ", "-")


# ════════════════════════════════════════════════════════════════════════
# PUNTO 1 — VALIDACIÓN: ¿YA EXISTE?
# ════════════════════════════════════════════════════════════════════════

def personaje_ya_generado(nombre_personaje: str, tres_vistas: bool = True) -> bool:
    """
    Comprueba si las imágenes del personaje ya existen en disco.

    Lógica:
      tres_vistas=True  → necesita front.png
      tres_vistas=False → necesita {nombre-con-guiones}.png

    Returns:
      True  → ya existen todas → SKIP (no regenerar)
      False → falta alguna    → hay que generar
    """
    carpeta_nombre = _nombre_a_carpeta(nombre_personaje)
    personaje_dir  = ASSETS_PERSONAJES_DIR / carpeta_nombre

    if not personaje_dir.exists():
        return False

    if tres_vistas:
        return all(
            (personaje_dir / pose["archivo"]).exists()
            for pose in POSES_PERSONAJE.values()
        )
    else:
        return (personaje_dir / f"{carpeta_nombre}.png").exists()


def listar_personajes_generados() -> list:
    """
    Devuelve la lista de nombres de carpeta de personajes que ya tienen
    imágenes en assets/personajes/.
    Útil para mostrar un resumen antes de iniciar un lote.
    """
    if not ASSETS_PERSONAJES_DIR.exists():
        return []
    return [
        d.name for d in sorted(ASSETS_PERSONAJES_DIR.iterdir())
        if d.is_dir() and (list(d.glob("*.png")) or list(d.glob("*.jpg")))
    ]


# ════════════════════════════════════════════════════════════════════════
# BACKENDS DE GENERACIÓN DE IMÁGENES
# ════════════════════════════════════════════════════════════════════════

def _llamar_gemini_api(prompt: str) -> Optional[bytes]:
    """
    Llama a Google Imagen 4 y devuelve los bytes PNG de la imagen.
    Soporta los distintos formatos de respuesta del SDK de Google.
    """
    if not GOOGLE_API_KEY:
        print("  ❌ GOOGLE_API_KEY no configurada en .env")
        return None

    try:
        from google import genai
        import base64

        client   = genai.Client(api_key=GOOGLE_API_KEY)
        response = client.models.generate_images(model=GEMINI_MODEL, prompt=prompt)

        if not response.generated_images:
            print("  ⚠️  La API no devolvió imágenes.")
            return None

        img_obj = response.generated_images[0].image

        if hasattr(img_obj, "image_bytes") and img_obj.image_bytes:
            return img_obj.image_bytes
        if hasattr(img_obj, "b64_json") and img_obj.b64_json:
            return base64.b64decode(img_obj.b64_json)

        # Fallback PIL
        from PIL import Image
        pil = img_obj.as_pil() if hasattr(img_obj, "as_pil") else img_obj
        buf = io.BytesIO()
        pil.save(buf, format="PNG")
        return buf.getvalue()

    except ImportError as e:
        print(f"  ⚠️  Dependencia no instalada: {e}")
        return None
    except Exception as e:
        print(f"  ❌ Error en Imagen API (Gemini): {e}")
        return None


def _llamar_runway_api(prompt: str) -> Optional[bytes]:
    """
    Llama a la API de Runway (Gen-4 Image) y devuelve los bytes PNG de la imagen.
    Usa .wait_for_task_output() del SDK oficial (bloquea hasta completar).
    Requiere: pip install runwayml
    """
    if not RUNWAY_API_KEY:
        print("  ❌ RUNWAY_API_KEY (kayroscreativeApiKey) no configurada en .env")
        return None

    try:
        import urllib.request
        from runwayml import RunwayML

        client = RunwayML(api_key=RUNWAY_API_KEY)

        RATIO = "1024:1024"
        print(f"    📡 Enviando a Runway Gen-4 Image ({len(prompt)} chars, ratio {RATIO})...")

        # El SDK Python usa keyword args en snake_case.
        # .wait_for_task_output() bloquea hasta que el task termina.
        task_obj = client.text_to_image.create(
            model="gen4_image",
            prompt_text=prompt,
            ratio=RATIO,
        )
        task_id = task_obj.id
        print(f"    🆔 Task ID: {task_id}")
        task = task_obj.wait_for_task_output()

        if not task.output:
            failure = getattr(task, "failure", None) or getattr(task, "error", None) or "sin detalle"
            print(f"  ⚠️  Runway: sin output. Status={task.status}. Motivo={failure}")
            return None

        print(f"    ✅ Runway completado ({task.status}) — descargando imagen...")
        with urllib.request.urlopen(task.output[0]) as resp:
            return resp.read()

    except ImportError as e:
        print(f"  ⚠️  Dependencia Runway no instalada: {e}")
        print("      Instala con: pip install runwayml")
        return None
    except Exception as e:
        # TaskFailedError expone e.task_details.failure con el motivo real del backend
        td = getattr(e, "task_details", None)
        if td is not None:
            code = getattr(td, "failure_code", None)
            msg  = getattr(td, "failure", str(e))
            print(f"  ❌ Runway task fallida [{code or 'sin código'}]: {msg}")
        else:
            details = []
            for attr in ("status_code", "status", "message", "body", "response", "failure"):
                val = getattr(e, attr, None)
                if val is not None:
                    details.append(f"{attr}={val}")
            extra = f"  [{', '.join(details)}]" if details else ""
            print(f"  ❌ Error en Runway API: {e}{extra}")
        return None


def _llamar_imagen_api(prompt: str, model: str = "gemini") -> Optional[bytes]:
    """
    Dispatcher: elige el backend de generación de imágenes.

    Args:
        prompt: texto del prompt
        model:  "gemini" → Google Imagen 4 (default)
                "runway" → Runway Gen-4 Image

    Returns:
        bytes PNG, o None si falló
    """
    if model == "runway":
        return _llamar_runway_api(prompt)
    return _llamar_gemini_api(prompt)


# ════════════════════════════════════════════════════════════════════════
# PUNTO 1 — GENERACIÓN DE VISTAS DE PERSONAJE (con skip automático)
# ════════════════════════════════════════════════════════════════════════

def _prompt_con_pose(prompt_base: str, descripcion_pose: str) -> str:
    """Añade los requisitos de pose y estilo al prompt base del personaje (solo 3D)."""
    return (
        f"{prompt_base}\n\n"
        "STYLE REQUIREMENTS:\n"
        "- Pure white background, studio lighting, no shadows on background\n"
        "- Exact same character proportions, colors and accessories as described above\n"
        "- Do NOT add new accessories or change any design element\n"
        "- Character turnaround sheet consistency\n"
        "- High detail 3D cartoon render, Pixar-style\n"
        "- Full body visible from head to toe\n\n"
        f"MANDATORY POSE:\n{descripcion_pose}"
    )


def _condensar_prompt_2D_para_runway(prompt: str) -> str:
    """
    Genera un prompt ≤ 990 chars para Runway Gen-4 siguiendo la plantilla:

      [personaje + estilo fijo]

      [descripcion fisica: items separados por coma].

      Happy, joyful expression. Soft even studio lighting. Smooth painted texture.

    Extrae los bullets de PHYSICAL DESCRIPTION del prompt-2D y los convierte
    en un párrafo continuo separado por comas, incluyendo tantos como quepan.
    """
    import re

    LIMIT = 990
    HEADER_SUFFIX = (
        "clean white studio background, full body visible. "
        "Flat 2D vector cartoon illustration ONLY — bold clean black outlines on ALL shapes, "
        "cel-shaded flat colors (no gradients, no volume), children's picture book art style."
    )
    FOOTER = "\nHappy, joyful expression. Soft even studio lighting. Smooth painted texture."

    # 1. Apertura: extraer "A single ... character" de la primera línea
    first_line = prompt.split("\n\n")[0].strip()
    m = re.search(r"(A single .+?character)", first_line)
    char_part = m.group(1) if m else first_line.split(",")[0]
    header = f"{char_part}, {HEADER_SUFFIX}"

    # 2. PHYSICAL DESCRIPTION → items sin el guión, separados por coma
    phys_items = []
    if "PHYSICAL DESCRIPTION:" in prompt:
        start = prompt.index("PHYSICAL DESCRIPTION:")
        end = next(
            (prompt.find(sec, start) for sec in ("\n\nPERSONALITY", "\n\nTECHNICAL")
             if sec in prompt[start:]),
            len(prompt),
        )
        for line in prompt[start:end].split("\n"):
            line = line.strip()
            if line.startswith("- "):
                phys_items.append(line[2:])

    # 3. Construir párrafo dentro del presupuesto disponible
    budget = LIMIT - len(header) - len(FOOTER) - 5
    phys_text = ""
    for item in phys_items:
        sep = ", " if phys_text else ""
        if len(phys_text) + len(sep) + len(item) <= budget:
            phys_text += sep + item
        else:
            break

    return f"{header}\n\n{phys_text}.\n{FOOTER}"


def _condensar_prompt_3D_para_runway(prompt: str, pose_descripcion: str) -> str:
    """
    Condensa un prompt-3D completo (~1400+ chars) a < 950 chars para Runway.

    Los prompts-3D no tienen sección STYLE MANDATE (a diferencia de los 2D).
    La pose se añade inline en lugar de usar _prompt_con_pose (que añadiría ~200 chars más).

    Estrategia:
      1. Apertura (primera línea — define especie + estilo Pixar/CGI)
      2. Líneas de PHYSICAL DESCRIPTION que quepan en el presupuesto
      3. Pose compacta inline
      4. Bloque compacto de negativas 3D
    """
    LIMIT = 950
    COMPACT_POSE = f"POSE: {pose_descripcion}, pure white studio background, full body visible head to toe."
    COMPACT_NEGATIVES = (
        "\nNEGATIVE: photorealistic, hyperrealistic, 2D flat cartoon, sketch, watercolor, "
        "extra limbs, anatomical errors, sad or angry expression, text, watermarks, cut-off body."
    )

    # 1. Apertura: todo antes del primer doble salto de línea
    apertura = prompt.split("\n\n")[0].strip()

    # 2. PHYSICAL DESCRIPTION: líneas que quepan en el presupuesto restante
    presupuesto = LIMIT - len(apertura) - len(COMPACT_POSE) - len(COMPACT_NEGATIVES) - 8
    phys_condensed = ""
    if "PHYSICAL DESCRIPTION:" in prompt:
        start = prompt.index("PHYSICAL DESCRIPTION:")
        end = next(
            (prompt.find(sec, start) for sec in ("\n\nPERSONALITY", "\n\nTECHNICAL", "\n\nNEGATIVE")
             if prompt.find(sec, start) != -1),
            len(prompt),
        )
        for line in prompt[start:end].split("\n"):
            if len(phys_condensed) + len(line) + 1 <= presupuesto:
                phys_condensed += line + "\n"
            else:
                break

    return f"{apertura}\n\n{phys_condensed.strip()}\n\n{COMPACT_POSE}{COMPACT_NEGATIVES}"


def generar_imagen_personaje_con_prompt(
    nombre_personaje: str,
    prompt_3d: str,
    forzar: bool = False,
    model: str = "gemini",
    estilo: str = "3D",
) -> Optional[Path]:
    """
    Genera UNA imagen frontal de un personaje.

    Args:
        nombre_personaje: nombre del personaje (ej: "hurón explorador")
        prompt_3d:        prompt visual completo del personaje
        forzar:           si True, regenera aunque ya exista en disco
        model:            "gemini" o "runway"
        estilo:           "3D" → aplica wrapper _prompt_con_pose (Pixar/CGI)
                          "2D" → envía el prompt tal cual (ya es auto-contenido)

    Returns:
        Path de la imagen guardada, o None si falló
    """
    carpeta_nombre = _nombre_a_carpeta(nombre_personaje)
    personaje_dir  = get_personaje_dir(nombre_personaje)
    ruta           = personaje_dir / f"{carpeta_nombre}.png"

    if not forzar and ruta.exists():
        print(f"  ⏭️  {nombre_personaje}: imagen ya existe → {ruta.name}  (pasa forzar=True para regenerar)")
        return ruta

    print(f"\n  🎨 Generando imagen: {nombre_personaje}  [{model}]  [{estilo}]")
    if estilo == "3D" and model == "runway":
        prompt_final = _condensar_prompt_3D_para_runway(prompt_3d, POSES_PERSONAJE["front"]["descripcion"])
    elif estilo == "3D":
        prompt_final = _prompt_con_pose(prompt_3d, POSES_PERSONAJE["front"]["descripcion"])
    elif model == "runway":
        prompt_final = _condensar_prompt_2D_para_runway(prompt_3d)
    else:
        prompt_final = prompt_3d  # 2D + Gemini: prompt completo sin modificar
    imagen_bytes = _llamar_imagen_api(prompt_final, model=model)

    if imagen_bytes is None:
        return None

    ruta.write_bytes(imagen_bytes)
    entry = tracker.register_image(
        operation="generar_imagen_personaje", model=IMAGE_MODEL, images_count=1,
        metadata={"personaje": nombre_personaje, "pose": "front", "backend": model},
    )
    tracker.print_entry(entry)
    print(f"  ✅ Guardada: {ruta}")
    return ruta


def generar_tres_vistas_personaje(
    nombre_personaje: str,
    prompt_3d: str,
    forzar: bool = False,
    model: str = "gemini",
    estilo: str = "3D",
) -> Dict[str, Optional[Path]]:
    """
    Genera las 3 vistas (front / side / quarter) de un personaje.

    Comportamiento del skip:
      - Si las 3 existen y forzar=False → devuelve las rutas existentes sin llamar a la API.
      - Si falta alguna vista → solo genera las que faltan (skip selectivo).
      - Si forzar=True → regenera todas.

    Args:
        nombre_personaje: nombre del personaje
        prompt_3d:        prompt visual completo (campo "prompt-3D" o "prompt-2D" del JSON)
        forzar:           si True regenera todo aunque ya exista
        model:            "gemini" o "runway"
        estilo:           "3D" → aplica _prompt_con_pose (añade wrapper Pixar/pose)
                          "2D" → envía el prompt tal cual (auto-contenido, sin wrapper 3D)

    Returns:
        {"front": Path|None, "side": Path|None, "quarter": Path|None}
    """
    carpeta_nombre = _nombre_a_carpeta(nombre_personaje)
    personaje_dir  = get_personaje_dir(nombre_personaje)

    # Skip: imagen ya existe
    if not forzar and personaje_ya_generado(nombre_personaje, tres_vistas=True):
        print(
            f"  ⏭️  {nombre_personaje}: imagen ya existe en assets/personajes/{carpeta_nombre}/\n"
            f"      (pasa forzar=True para regenerar)"
        )
        return {k: personaje_dir / v["archivo"] for k, v in POSES_PERSONAJE.items()}

    print(f"\n  🎨 Generando imagen: {nombre_personaje}  [{model}]  [{estilo}]")
    print(f"  📂 {personaje_dir}")

    imagenes: Dict[str, Optional[Path]] = {}

    for pose_key, pose_info in POSES_PERSONAJE.items():
        ruta_pose = personaje_dir / pose_info["archivo"]

        # Skip selectivo: esta vista concreta ya existe
        if not forzar and ruta_pose.exists():
            print(f"  ⏭️  {pose_info['nombre']}: ya existe → saltando")
            imagenes[pose_key] = ruta_pose
            continue

        print(f"  📸 Generando {pose_info['nombre']}...")
        if estilo == "3D" and model == "runway":
            prompt_final = _condensar_prompt_3D_para_runway(prompt_3d, pose_info["descripcion"])
        elif estilo == "3D":
            prompt_final = _prompt_con_pose(prompt_3d, pose_info["descripcion"])
        elif model == "runway":
            prompt_final = _condensar_prompt_2D_para_runway(prompt_3d)
        else:
            prompt_final = prompt_3d  # 2D + Gemini: prompt completo sin modificar
        imagen_bytes = _llamar_imagen_api(prompt_final, model=model)

        if imagen_bytes is None:
            print(f"  ❌ No se pudo generar {pose_key}")
            imagenes[pose_key] = None
            continue

        ruta_pose.write_bytes(imagen_bytes)
        entry = tracker.register_image(
            operation="generar_vista_personaje", model=IMAGE_MODEL, images_count=1,
            metadata={"personaje": nombre_personaje, "pose": pose_key, "backend": model},
        )
        tracker.print_entry(entry)
        imagenes[pose_key] = ruta_pose
        print(f"  ✅ {pose_info['nombre']} → {ruta_pose.name}")

    generadas = sum(1 for v in imagenes.values() if v)
    total = len(POSES_PERSONAJE)
    print(f"  📊 {generadas}/{total} imagen(es) completada(s) para: {nombre_personaje}")
    return imagenes


def generar_imagen_personaje(
    personaje_dict: Dict[str, Any],
    tres_vistas: bool = True,
    forzar: bool = False,
    model: str = "gemini",
) -> Optional[Any]:
    """
    Punto de entrada principal para generar imágenes de un personaje.

    Args:
        personaje_dict: dict del personaje (debe tener clave 'prompt-3D')
        tres_vistas:    True → genera front/side/quarter, False → solo frontal
        forzar:         True → regenera aunque ya exista en disco
        model:          "gemini" o "runway"

    Returns:
        dict de Paths si tres_vistas=True, Path si tres_vistas=False, None si error
    """
    nombre = obtener_nombre_personaje(personaje_dict)

    if isinstance(personaje_dict, str):
        print(f"  ⚠️  {nombre}: formato string, sin especificaciones 3D")
        return None
    if "prompt-3D" not in personaje_dict:
        print(f"  ⚠️  {nombre}: no tiene campo 'prompt-3D'")
        return None

    prompt = personaje_dict["prompt-3D"]
    if tres_vistas:
        return generar_tres_vistas_personaje(nombre, prompt, forzar=forzar, model=model)
    else:
        return generar_imagen_personaje_con_prompt(nombre, prompt, forzar=forzar, model=model)


def generar_imagenes_escena(
    historia_dict: Dict[str, Any],
    tres_vistas: bool = True,
    forzar: bool = False,
    model: str = "gemini",
) -> Dict[str, Any]:
    """
    Genera imágenes del personaje secundario de una historia.
    Respeta el skip automático.

    Args:
        historia_dict: dict con "elementos" que incluye "personaje_secundario"
        tres_vistas:   True → front/side/quarter, False → solo frontal
        forzar:        True → regenera aunque ya exista en disco
        model:         "gemini" o "runway"
    """
    elementos      = historia_dict.get("elementos", {})
    nombre         = elementos.get("personaje_secundario_nombre")
    personaje_dict = elementos.get("personaje_secundario")

    if not nombre or not personaje_dict:
        print("  ❌ No se encontró personaje secundario en la historia")
        return {}

    prompt = personaje_dict.get("prompt-3D") if isinstance(personaje_dict, dict) else None
    if not prompt:
        print(f"  ⚠️  '{nombre}' no tiene prompt-3D")
        return {}

    if tres_vistas:
        vistas = generar_tres_vistas_personaje(nombre, prompt, forzar=forzar, model=model)
        return {"personaje": nombre, "vistas": vistas, "total_imagenes": sum(1 for v in vistas.values() if v)}
    else:
        imagen = generar_imagen_personaje_con_prompt(nombre, prompt, forzar=forzar, model=model)
        return {"personaje": nombre, "imagen": imagen, "total_imagenes": 1 if imagen else 0}


# ════════════════════════════════════════════════════════════════════════
# PUNTO 2 — ILUSTRACIÓN DE CUENTO POR ESCENA
# ════════════════════════════════════════════════════════════════════════

def _bloque_referencia_personajes(characters_data: dict) -> str:
    """
    Construye el bloque de REFERENCIA VISUAL COMPLETA de todos los personajes.

    Este bloque va al inicio del prompt de ilustración para que la IA
    tenga contexto completo de Kira, Toby, el personaje secundario
    y los objetos importantes de la historia.

    Incluye:
      - Especie, proporciones, colores hex exactos
      - Accesorios y elementos identificativos
      - Restricciones absolutas (NEVER CHANGE)
    """
    campos_visuales = [
        ("height_ratio",       "height"),
        ("body_shape",         "body shape"),
        ("head_ratio",         "head size"),
        ("fur_color",          "fur color"),
        ("belly_color",        "belly color"),
        ("mask_color",         "mask color"),
        ("eye_color",          "eye color"),
        ("accessory",          "accessory"),
        ("personality_visual", "visual personality"),
    ]

    secciones = []

    # ── Protagonistas ──────────────────────────────────────────────────
    for p in characters_data.get("personajesPrincipales", []):
        nombre  = p.get("nombre", "?")
        species = p.get("species", "?")
        lineas  = [f"[ {nombre.upper()} — {species} — MAIN CHARACTER ]"]
        for campo, label in campos_visuales:
            if campo in p:
                lineas.append(f"  {label}: {p[campo]}")
        if "forbidden_changes" in p:
            lineas.append(f"  *** NEVER CHANGE: {p['forbidden_changes']}")
        secciones.append("\n".join(lineas))

    # ── Personaje secundario ───────────────────────────────────────────
    for p in characters_data.get("personajesSecundarios", []):
        nombre  = p.get("nombre", "?")
        species = p.get("species", "?")
        lineas  = [f"[ {nombre.upper()} — {species} — SECONDARY CHARACTER ]"]
        skip    = {"nombre", "species", "prompt-3D", "forbidden_changes"}
        for campo, label in campos_visuales:
            if campo in p:
                lineas.append(f"  {label}: {p[campo]}")
        # Campos extra que no están en campos_visuales
        for k, v in p.items():
            if k not in skip and k not in dict(campos_visuales):
                lineas.append(f"  {k.replace('_', ' ')}: {v}")
        if "forbidden_changes" in p:
            lineas.append(f"  *** NEVER CHANGE: {p['forbidden_changes']}")
        secciones.append("\n".join(lineas))

    # ── Objetos importantes ────────────────────────────────────────────
    for obj in characters_data.get("objectosImportantes", []):
        nombre = obj.get("nombre", "?")
        lineas = [f"[ OBJECT: {nombre.upper()} ]"]
        skip   = {"nombre", "forbidden_changes"}
        for k, v in obj.items():
            if k not in skip:
                lineas.append(f"  {k}: {v}")
        if "forbidden_changes" in obj:
            lineas.append(f"  *** NEVER CHANGE: {obj['forbidden_changes']}")
        secciones.append("\n".join(lineas))

    return "\n\n".join(secciones)


def construir_prompt_ilustracion(
    scene_number: int,
    paragraph: str,
    characters_data: dict,
    scene_context: Optional[Dict[str, str]] = None,
) -> str:
    """
    Construye el prompt completo para generar una ilustración de cuento infantil.

    DIFERENCIAS respecto al prompt de VIDEO (escenaN.md):
      ✗ Sin "ACTION & MOVEMENT"  (las ilustraciones son estáticas)
      ✗ Sin "CAMERA"             (no hay movimiento de cámara)
      ✗ Sin duración de clip
      ✓ Con "CHARACTER VISUAL REFERENCE" completa al inicio (hex, proporciones, restricciones)
      ✓ Con "ILLUSTRATION STYLE" específico para libros infantiles
      ✓ CONTINUITY NOTES adaptadas a ilustración (no a animación)

    Args:
        scene_number:    número de escena
        paragraph:       párrafo narrativo de la historia para esta escena
        characters_data: dict completo del characters.json
        scene_context:   dict opcional con contexto adicional de la escena:
                           "environment"  → descripción del entorno (puede venir del escenaN.md)
                           "mood"         → estado emocional / atmósfera
                           "continuity"   → CONTINUITY NOTES de la escena anterior
                           "objects"      → objetos presentes en escena

    Returns:
        str: prompt listo para enviar a Google Imagen / DALL-E 3 / Midjourney
    """
    ctx        = scene_context or {}
    env        = ctx.get("environment", "").strip()
    mood       = ctx.get("mood", "").strip()
    continuity = ctx.get("continuity", "").strip()
    objects    = ctx.get("objects", "").strip()

    ref_personajes = _bloque_referencia_personajes(characters_data)

    # Extraer datos de Kira y Toby para las CONTINUITY NOTES finales
    kira = next((p for p in characters_data.get("personajesPrincipales", []) if p.get("nombre") == "Kira"), {})
    toby = next((p for p in characters_data.get("personajesPrincipales", []) if p.get("nombre") == "Toby"), {})

    kira_cont = (
        f"Kira: fur {kira.get('fur_color','#F5C542')}, "
        f"eyes {kira.get('eye_color','#1E90FF')}, "
        f"red bow on RIGHT ear only"
    )
    toby_cont = (
        f"Toby: fur {toby.get('fur_color','#8B6914')}, "
        f"eyes {toby.get('eye_color','#2E8B57')}, "
        f"navy collar {toby.get('accessory','#003366')}"
    )
    sec_cont_lines = [
        f"{p.get('nombre','?')}: fur {p.get('fur_color','')}, eyes {p.get('eye_color','')}, {p.get('accessory','')}"
        for p in characters_data.get("personajesSecundarios", [])
    ]
    obj_cont_lines = [
        f"{obj.get('nombre','?')}: {obj.get('forbidden_changes','maintain visual consistency')}"
        for obj in characters_data.get("objectosImportantes", [])
    ]

    # Personajes secundarios presentes (para CHARACTERS PRESENT)
    sec_present = []
    for p in characters_data.get("personajesSecundarios", []):
        nombre  = p.get("nombre", "?")
        species = p.get("species", "?")
        fur     = p.get("fur_color", "")
        eye     = p.get("eye_color", "")
        acc     = p.get("accessory", "")
        desc    = f"{nombre} ({species}"
        if fur: desc += f", fur {fur}"
        if eye: desc += f", eyes {eye}"
        if acc: desc += f", {acc}"
        desc += ")"
        sec_present.append(desc)

    lines = [
        f"STORYBOOK ILLUSTRATION — Scene {scene_number}",
        "=" * 65,
        "",
        "STORY PARAGRAPH (this illustration depicts):",
        f'"{paragraph}"',
        "",
        "─" * 65,
        "CHARACTER VISUAL REFERENCE",
        "(STRICT — use EXACT hex colors and proportions, never invent new traits)",
        "─" * 65,
        ref_personajes,
        "",
        "─" * 65,
        "",
        "ENVIRONMENT:",
        env if env else (
            "Infer carefully from the story paragraph above.\n"
            "Describe: location, time of day, weather, dominant color palette, "
            "textures, ambient details that enrich the scene."
        ),
        "",
        "CHARACTERS PRESENT:",
        f"- Kira (main, {kira.get('personality_visual','brave and expressive')})",
        f"- Toby (main, {toby.get('personality_visual','thoughtful and observant')})",
    ]

    for sp in sec_present:
        lines.append(f"- {sp}")

    if objects:
        lines.append(f"- Objects present: {objects}")

    lines += [
        "",
        "LIGHTING & MOOD:",
        mood if mood else (
            "Warm, magical, inviting. Soft golden ambient light with gentle shadows.\n"
            "Cozy and safe atmosphere — enchanting but never scary. Perfect for ages 3-6."
        ),
    ]

    if continuity:
        lines += [
            "",
            "CONTINUITY FROM PREVIOUS ILLUSTRATION (maintain these visual elements):",
            continuity,
        ]

    lines += [
        "",
        "─" * 65,
        "",
        "ILLUSTRATION STYLE (MANDATORY):",
        "- Medium: children's storybook illustration — warm digital art, soft brushwork,",
        "  blending hand-painted textures with Pixar CGI quality finish",
        "- Characters: big expressive eyes, rounded cute proportions, soft fur textures,",
        "  full of personality and emotion",
        "- Background: richly detailed with storytelling depth — plants, light rays,",
        "  ambient particles, reflections, textures that reward close looking",
        "- Colors: vibrant and harmonious palette, warm dominant tones,",
        "  complementary accents, no harsh or cold contrasts",
        "- Composition: cinematic framing, characters at center or rule-of-thirds,",
        "  full scene always visible, depth layers (foreground / midground / background)",
        "- Light: warm directional light source, soft cast shadows, optional magical glow",
        "  on special objects, ambient subsurface scattering on fur",
        "- Strictly NO text, NO speech bubbles, NO watermarks, NO UI elements",
        "- Single complete illustration (NOT a comic strip, NOT a sequence of panels)",
        "",
        "TECHNICAL:",
        "- 3D CGI animation style with storybook illustration warmth",
        "- Pixar/Disney rendering quality",
        "- 8K resolution, ultra-detailed, crisp clean edges",
        "- Soft studio lighting combined with environment color grade",
        "- Single static image optimized for children's book page layout",
        "",
        "CONTINUITY NOTES (maintain in all subsequent illustrations):",
        f"- {kira_cont}",
        f"- {toby_cont}",
    ]

    for sec in sec_cont_lines:
        lines.append(f"- {sec}")

    for obj in obj_cont_lines:
        lines.append(f"- {obj}")

    lines.append("- Preserve dominant color palette and lighting mood established in this scene")

    return "\n".join(lines)


def generar_ilustracion_escena(
    scene_number: int,
    paragraph: str,
    characters_data: dict,
    output_dir: Path,
    scene_context: Optional[Dict[str, str]] = None,
    forzar: bool = False,
    model: str = "gemini",
) -> Optional[Path]:
    """
    Genera UNA ilustración de cuento para una escena y la guarda en disco.

    Archivos generados:
      {output_dir}/ilustracion_{N}.png          ← la imagen
      {output_dir}/ilustracion_{N}_prompt.md    ← el prompt usado (para referencia y auditoría)

    Args:
        scene_number:    número de la escena (1, 2, 3...)
        paragraph:       párrafo narrativo de la historia para esta escena
        characters_data: dict completo del characters.json
        output_dir:      carpeta de salida (normalmente prompts-scenas/)
        scene_context:   dict opcional con contexto adicional:
                           "environment"  → descripción del entorno
                           "mood"         → atmósfera emocional
                           "continuity"   → CONTINUITY NOTES de la escena anterior
                           "objects"      → objetos presentes
        forzar:          si True regenera aunque ya exista

    Returns:
        Path de la imagen guardada, o None si falló
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    ruta_imagen  = output_dir / f"ilustracion_{scene_number}.png"
    ruta_prompt  = output_dir / f"ilustracion_{scene_number}_prompt.md"

    # ── Skip automático ────────────────────────────────────────────────
    if not forzar and ruta_imagen.exists():
        print(f"  ⏭️  ilustracion_{scene_number}.png ya existe → saltando  (pasa forzar=True para regenerar)")
        return ruta_imagen

    print(f"\n  🖼️  Generando ilustración escena {scene_number}...")

    # Construir prompt
    prompt = construir_prompt_ilustracion(
        scene_number=scene_number,
        paragraph=paragraph,
        characters_data=characters_data,
        scene_context=scene_context,
    )

    # Guardar prompt como referencia (siempre, aunque falle la imagen)
    ruta_prompt.write_text(
        f"# Prompt Ilustración — Escena {scene_number}\n\n```\n{prompt}\n```\n",
        encoding="utf-8",
    )

    imagen_bytes = _llamar_imagen_api(prompt, model=model)

    if imagen_bytes is None:
        print(f"  ❌ No se pudo generar ilustración de escena {scene_number}")
        return None

    ruta_imagen.write_bytes(imagen_bytes)
    entry = tracker.register_image(
        operation=f"ilustracion_escena_{scene_number}",
        model=IMAGE_MODEL,
        images_count=1,
        metadata={"escena": scene_number, "tipo": "ilustracion_cuento", "backend": model},
    )
    tracker.print_entry(entry)
    print(f"  ✅ Guardada: {ruta_imagen}")
    return ruta_imagen


def generar_ilustraciones_historia(
    paragraphs: list,
    characters_data: dict,
    output_dir: Path,
    scenes_context: Optional[Dict[int, Dict[str, str]]] = None,
    forzar: bool = False,
) -> Dict[int, Optional[Path]]:
    """
    Genera ilustraciones para TODAS las escenas de una historia.
    Salta automáticamente las que ya existen (skip por escena).

    El scenes_context puede construirse leyendo los escenaN.md ya generados
    por scene_generator.py — así el prompt de ilustración aprovecha el ambiente
    y continuidad ya calculados por el agente Director Creativo.

    Args:
        paragraphs:      lista de párrafos (un párrafo = una escena)
        characters_data: dict completo del characters.json
        output_dir:      carpeta de salida (normalmente prompts-scenas/)
        scenes_context:  dict {num_escena: {"environment": ..., "mood": ..., ...}}
                         Si es None la IA infiere todo desde el párrafo.
        forzar:          si True regenera todas aunque existan

    Returns:
        {num_escena: Path_o_None}
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    ya_hechas = sum(1 for i in range(1, len(paragraphs)+1) if (output_dir / f"ilustracion_{i}.png").exists())
    pendientes = len(paragraphs) - ya_hechas if not forzar else len(paragraphs)

    print(f"\n{'═'*62}")
    print(f"   🖼️  GENERADOR DE ILUSTRACIONES DE CUENTO")
    print(f"{'═'*62}")
    print(f"  Total escenas  : {len(paragraphs)}")
    print(f"  Ya generadas   : {ya_hechas}")
    print(f"  Por generar    : {pendientes}{' (nada que hacer)' if pendientes == 0 and not forzar else ''}")
    if forzar:
        print(f"  ⚠️  Modo forzar: regenerando todo")
    print()

    resultados = {}
    for i, paragraph in enumerate(paragraphs, start=1):
        ctx  = (scenes_context or {}).get(i, {})
        ruta = generar_ilustracion_escena(
            scene_number=i,
            paragraph=paragraph,
            characters_data=characters_data,
            output_dir=output_dir,
            scene_context=ctx,
            forzar=forzar,
        )
        resultados[i] = ruta

    ok = sum(1 for r in resultados.values() if r)
    print(f"\n  📊 Ilustraciones completadas: {ok}/{len(paragraphs)}")
    print(f"  📁 Ubicación: {output_dir.resolve()}\n")
    return resultados


# ════════════════════════════════════════════════════════════════════════
# UTILIDADES
# ════════════════════════════════════════════════════════════════════════

def crear_imagen_placeholder(nombre_personaje: str) -> Optional[Path]:
    """
    Crea un placeholder simple para testing (sin API).
    Salta si ya existe. Requiere: pip install Pillow
    """
    ruta = get_personaje_image_path(nombre_personaje)

    if ruta.exists():
        print(f"  ⏭️  Placeholder ya existe: {ruta}")
        return ruta

    try:
        from PIL import Image, ImageDraw
        img  = Image.new("RGB", (400, 400), color="lightblue")
        draw = ImageDraw.Draw(img)
        draw.text((50, 180), normalizar_nombre_archivo(nombre_personaje), fill="black")
        img.save(ruta)
        print(f"  ✅ Placeholder creado: {ruta}")
        return ruta
    except ImportError:
        print("  ⚠️  Pillow no instalado: pip install Pillow")
        return None
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return None
