"""
SCENE_GENERATOR.PY - Generador de prompts de escenas para video IA

Toma el texto de una historia ya guardada y genera prompts detallados
para generadores de video IA (Sora, Runway, Pika, Kling).

Integra el sistema de coherencia multi-agente:
  → Agente 1: Director Creativo CGI  (genera cada escena)
  → Agente 2: Editor Narrativo       (valida coherencia global)
  → Corrección automática iterativa  (hasta MAX_FIX_ITERATIONS rondas)

Los archivos se guardan en:
  outputs/historias/revision/{TITULO}/prompts-scenas/
    ├── escena1.md          ← Prompt enriquecido para video IA
    ├── escenaN.md
    ├── RESUMEN_FINAL.md    ← Puntuación y problemas detectados
    └── coherence_report_v{N}.json
"""

import json
import re
import time
from pathlib import Path
from typing import Optional

from openai import OpenAI

from config.config import OPENAI_MODEL, LOGS_DIR, IMAGE_MODEL
from .token_tracker import tracker

# ── Constantes configurables ─────────────────────────────────────────────────

COHERENCE_THRESHOLD = 85   # % mínimo para aprobar la coherencia
MAX_FIX_ITERATIONS  = 3    # Intentos máximos de corrección automática
SCENE_MAX_TOKENS    = 1500
EDITOR_MAX_TOKENS   = 3000
SCENE_TEMPERATURE   = 0.7
EDITOR_TEMPERATURE  = 0.3


# ── Prompts de los agentes ────────────────────────────────────────────────────

_SCENE_SYSTEM = """\
Eres un experto director creativo especializado en animación CGI estilo Pixar/Disney.
Tu trabajo es convertir párrafos de una historia infantil en prompts altamente detallados
para generadores de video IA (Sora, Runway ML, Pika, Kling).

REGLAS CRÍTICAS:
1. El prompt DEBE estar en INGLÉS (los generadores de video responden mejor en inglés).
2. Mantén ABSOLUTA coherencia visual con los personajes descritos (hex exactos, proporciones).
3. Cada escena incluye: ambiente, iluminación, cámara, acción, emoción y continuidad.
4. Incluye al final "CONTINUITY NOTES" con los elementos que DEBEN aparecer en la siguiente escena.
5. Estilo visual: 3D CGI animation, Pixar/Disney quality, soft studio lighting, vibrant colors, 8K render.
6. NO inventes características físicas nuevas. Úsalas exactamente como se describen.
7. Duración estimada de cada clip: 5-8 segundos.

ESTRUCTURA DEL PROMPT DE ESCENA (usa EXACTAMENTE estas secciones en este orden):

SCENE [N] — [TÍTULO CORTO DE LA ESCENA]

CHARACTERS DESCRIPTION:
[BLOQUE DE PERSONAJES — será inyectado automáticamente, no lo reescribas]

ENVIRONMENT:
[Ambiente, hora del día, clima, paleta de colores dominante]

CHARACTERS PRESENT:
[Personajes en escena con estado emocional actual]

ACTION & MOVEMENT:
[Secuencia de acciones exacta, movimiento de cámara]

CAMERA:
[Tipo de plano, ángulo, movimiento]

LIGHTING & MOOD:
[Iluminación específica, atmósfera emocional]

TECHNICAL:
[Estilo 3D, calidad render, duración estimada del clip]

CONTINUITY NOTES (for next scene):
[Elementos visuales, posición de personajes y objetos que deben continuar]
"""

_EDITOR_SYSTEM = """\
Eres un editor experto en narrativa visual, especializado en animación CGI y storyboarding.
Revisas secuencias de prompts de escenas para video animado y evalúas:

1. COHERENCIA VISUAL: ¿Los personajes mantienen sus características físicas?
2. COHERENCIA NARRATIVA: ¿La historia fluye lógicamente de escena en escena?
3. CONTINUIDAD DE AMBIENTE: ¿Luz, objetos y clima son consistentes entre escenas?
4. CONTINUIDAD DE ACCIONES: ¿Las acciones conectan fluidamente?
5. CLARIDAD PARA IA VIDEO: ¿Cada prompt es suficientemente detallado?

RESPONDE ÚNICAMENTE CON ESTE JSON EXACTO (sin markdown, sin bloques de código):
{
  "overall_score": <0-100>,
  "scene_scores": {"1": <0-100>, "2": <0-100>, ...},
  "issues": [
    {
      "scene": <número>,
      "type": "visual|narrative|continuity|clarity",
      "description": "<descripción>",
      "severity": "low|medium|high"
    }
  ],
  "corrections_needed": [
    {
      "scene": <número>,
      "original_section": "<texto exacto a reemplazar>",
      "corrected_section": "<texto corregido>",
      "reason": "<razón>"
    }
  ],
  "summary": "<resumen ejecutivo en máximo 3 oraciones>",
  "passed": <true|false>
}
"""

_ILLUSTRATION_SYSTEM = """\
Eres un ilustrador experto especializado en libros de cuentos infantiles estilo Pixar/Disney CGI.
Tu trabajo es convertir párrafos de una historia en prompts detallados para generadores de imagen IA
(Midjourney, DALL-E 3, Adobe Firefly, Stable Diffusion XL).

DIFERENCIAS CLAVE con los prompts de video:
- Las ilustraciones son ESTÁTICAS: no hay movimiento, ni instrucciones de cámara, ni duración.
- El ENVIRONMENT debe ser MUCHO más rico y detallado: texturas, luz ambiental, elementos decorativos,
  profundidad de campo visual, paleta cromática específica con HEX, detalles del fondo que enriquecen
  la narrativa. Piensa como un director de arte de Pixar describiendo un cuadro.
- CHARACTERS PRESENT indica quiénes aparecen, su posición en el encuadre y expresión emocional.
  No describas acciones dinámicas sino poses narrativas (posturas que cuentan la historia).
- CONTINUITY NOTES es más corta: solo posición de personajes y elementos de entorno a mantener.

REGLAS CRÍTICAS:
1. El prompt DEBE estar en INGLÉS.
2. Respeta ABSOLUTAMENTE los colores HEX y proporciones de los personajes dados.
3. NO inventes rasgos físicos nuevos en los personajes.
4. El ENVIRONMENT debe tener al menos 5-7 líneas de descripción visual detallada.
   Incluye: ubicación, hora del día, tipo de luz, sombras, colores dominantes con HEX aproximados,
   texturas del suelo/paredes/vegetación, elementos decorativos, profundidad (primer plano / fondo).
5. Estilo visual: 3D CGI illustration, Pixar/Disney quality, children's storybook, 8K render.
6. NO incluyas secciones de ACTION & MOVEMENT ni CAMERA.

ESTRUCTURA DEL PROMPT DE ILUSTRACIÓN (usa EXACTAMENTE estas secciones en este orden):

ILLUSTRATION [N] — [TÍTULO CORTO EVOCADOR]

CHARACTERS DESCRIPTION:
[BLOQUE DE PERSONAJES — será inyectado automáticamente, no lo reescribas]

ENVIRONMENT:
[Descripción visual MUY DETALLADA del entorno: mínimo 6 líneas.
Incluye: escenario completo, hora del día, tipo de cielo/luz, fuentes de luz,
colores dominantes con HEX, texturas (suelo, vegetación, objetos),
elementos en primer plano / plano medio / fondo,
detalles decorativos que enriquecen la atmósfera del cuento.]

CHARACTERS PRESENT:
[Personajes en escena, su posición en el encuadre y expresión/postura narrativa]

LIGHTING & MOOD:
[Tipo de luz, dirección, temperatura de color, atmósfera emocional, estilo de sombreado]

COMPOSITION & STYLE:
[Composición de la ilustración: regla de tercios, encuadre, profundidad.
Estilo artístico: 3D CGI storybook, Pixar quality, paleta de colores específica.]

CONTINUITY NOTES (for next illustration):
[Elementos de posición y entorno que deben mantenerse en la siguiente ilustración]
"""

def _format_character(p: dict) -> str:
    """Formatea un personaje para el contexto del prompt del agente (formato compacto)."""
    parts = [f"\n• {p.get('nombre', '?').upper()} ({p.get('species', '?')})"]
    skip = {"nombre", "species", "prompt-3D", "forbidden_changes"}
    for k, v in p.items():
        if k not in skip:
            parts.append(f"  - {k}: {v}")
    if "forbidden_changes" in p:
        parts.append(f"  ⚠️ NO CAMBIAR: {p['forbidden_changes']}")
    return "\n".join(parts)


# Frases a eliminar del prompt-3D del secundario cuando se incrusta en la escena.
# Son instrucciones de fondo blanco / pose que solo aplican a generación de imagen suelta.
_FRASES_A_LIMPIAR_PROMPT3D = [
    "clean white studio background,",
    "clean white studio background.",
    "clean white studio background",
    "full body visible,",
    "full body visible.",
    "full body visible",
    "centered composition,",
    "centered composition.",
    "centered composition",
]


def _limpiar_prompt_3d(prompt: str) -> str:
    """
    Elimina del prompt-3D del secundario las instrucciones de fondo/pose
    que solo aplican cuando se genera la imagen suelta del personaje.
    Limpia también comas/espacios residuales.
    """
    resultado = prompt
    for frase in _FRASES_A_LIMPIAR_PROMPT3D:
        resultado = resultado.replace(frase, "")
    # Limpiar múltiples espacios y comas dobles residuales
    resultado = re.sub(r",\s*,", ",", resultado)
    resultado = re.sub(r"\s{2,}", " ", resultado)
    resultado = resultado.strip().strip(",").strip()
    return resultado


# ── Helpers exclusivos de ilustraciones ──────────────────────────────────────

def _build_secondary_block_for_md(characters_data: dict) -> str:
    """
    Construye el bloque del personaje secundario para el .md de ilustración.
    Solo incluye el secundario — Kira y Toby se omiten del .md porque sus
    prompts completos se inyectan directamente en el prompt de Google Imagen.
    """
    lines = []
    for p in characters_data.get("personajesSecundarios", []):
        nombre   = p.get("nombre", "personaje secundario")
        prompt3d = p.get("prompt-3D", "")
        if prompt3d:
            lines.append(f'"{nombre}": """{_limpiar_prompt_3d(prompt3d)}"""')
        else:
            skip   = {"nombre", "species", "prompt-3D", "forbidden_changes"}
            campos = [f"{k}: {v}" for k, v in p.items() if k not in skip]
            desc   = f"{p.get('species', 'character')}, {nombre}. " + ". ".join(campos)
            if "forbidden_changes" in p:
                desc += f". *** NEVER CHANGE: {p['forbidden_changes']}"
            lines.append(f'"{nombre}": """{desc}"""')

    if not lines:
        return ""
    return "PERSONAJE SECUNDARIO\n" + "\n".join(lines)


def _extract_illustration_section(text: str, section_name: str) -> str:
    """
    Extrae el contenido de una sección nombrada del texto generado por OpenAI.
    Funciona con: ENVIRONMENT, CHARACTERS PRESENT, LIGHTING & MOOD,
                  COMPOSITION & STYLE, CONTINUITY NOTES.
    """
    pattern = re.compile(
        rf"{re.escape(section_name)}[^:]*:\s*\n(.*?)(?=\n[A-Z]{{2,}}[^:\n]*:|\Z)",
        re.DOTALL | re.IGNORECASE,
    )
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def _build_imagen_prompt_from_illustration(
    illustration_text: str,
    characters_data: dict,
) -> str:
    """
    Construye el prompt completo para Google Imagen combinando:
      - Prompts de Kira y Toby desde config/personajes.py  (referencia visual exacta)
      - Personaje secundario desde characters_data
      - Contexto de escena generado por OpenAI: ENVIRONMENT, CHARACTERS PRESENT,
        LIGHTING & MOOD, COMPOSITION & STYLE

    El .md guarda el contexto limpio; este prompt va directo a la API de imagen.
    """
    from config.personajes import PERSONAJES

    kira_prompt = _limpiar_prompt_3d(PERSONAJES.get("kira", ""))
    toby_prompt = _limpiar_prompt_3d(PERSONAJES.get("toby", ""))

    # Personaje(s) secundario(s)
    secondary_lines = []
    for p in characters_data.get("personajesSecundarios", []):
        nombre   = p.get("nombre", "personaje secundario")
        prompt3d = p.get("prompt-3D", "")
        if prompt3d:
            secondary_lines.append(f'"{nombre}": """{_limpiar_prompt_3d(prompt3d)}"""')

    # Secciones de contexto generadas por OpenAI
    env         = _extract_illustration_section(illustration_text, "ENVIRONMENT")
    chars       = _extract_illustration_section(illustration_text, "CHARACTERS PRESENT")
    lighting    = _extract_illustration_section(illustration_text, "LIGHTING & MOOD")
    composition = _extract_illustration_section(illustration_text, "COMPOSITION & STYLE")

    parts = [
        "CHARACTER REFERENCES (STRICT — use EXACT hex colors and proportions, never invent new traits):",
        "",
        f'kira: """{kira_prompt}"""',
        "",
        f'toby: """{toby_prompt}"""',
    ]
    if secondary_lines:
        parts += [""] + secondary_lines

    if env:
        parts += ["", "ENVIRONMENT:", env]
    if chars:
        parts += ["", "CHARACTERS PRESENT:", chars]
    if lighting:
        parts += ["", "LIGHTING & MOOD:", lighting]
    if composition:
        parts += ["", "COMPOSITION & STYLE:", composition]

    parts += [
        "",
        "ILLUSTRATION STYLE (MANDATORY):",
        "- 3D CGI children's storybook illustration, Pixar/Disney quality",
        "- Big expressive eyes, rounded cute proportions, soft fur textures",
        "- Richly detailed background with storytelling depth",
        "- Warm, harmonious color palette — no harsh or cold contrasts",
        "- 8K resolution, ultra-detailed, crisp clean edges",
        "- Strictly NO text, NO speech bubbles, NO watermarks, NO UI elements",
        "- Single complete illustration, NOT a comic strip or panel sequence",
    ]
    return "\n".join(parts)


def _build_runway_prompt_from_illustration(
    illustration_text: str,
    characters_data: dict,
) -> str:
    """
    Versión compacta del prompt de ilustración para Runway (límite: 1000 chars).
    Prioriza ENVIRONMENT y CHARACTERS PRESENT sobre las descripciones largas de personajes.
    Usa descripciones breves de Kira y Toby en lugar de los prompts completos de personajes.py.
    """
    # Descripciones breves de los protagonistas (caben en ~200 chars)
    kira_brief = "Kira: female Shiba Inu puppy, pale yellow fur #FFF9D4, brown eyes #5C4033, red heart bow on right ear, cute 3D Pixar style"
    toby_brief = "Toby: male Husky puppy, lavender fur #E8E3F0, heterochromatic eyes (left blue #6BB6D6, right brown #8B6F47), lightning bolt on left flank, cute 3D Pixar style"

    # Personaje secundario breve
    sec_brief = ""
    for p in characters_data.get("personajesSecundarios", []):
        nombre  = p.get("nombre", "")
        species = p.get("species", "")
        fur     = p.get("fur_color", "")
        acc     = p.get("accessory", "")
        sec_brief = f"{nombre}: {species}" + (f", {fur}" if fur else "") + (f", {acc}" if acc else "")
        break  # solo el primero

    env   = _extract_illustration_section(illustration_text, "ENVIRONMENT")
    chars = _extract_illustration_section(illustration_text, "CHARACTERS PRESENT")

    parts = [
        "3D CGI children's storybook illustration, Pixar/Disney quality.",
        f"CHARACTERS: {kira_brief}. {toby_brief}.",
    ]
    if sec_brief:
        parts.append(f"Secondary: {sec_brief}.")
    if env:
        # Tomar solo las 3 primeras líneas del environment
        env_short = " ".join(env.split("\n")[:3]).strip()
        parts.append(f"SCENE: {env_short}")
    if chars:
        chars_short = chars.split("\n")[0].strip()
        parts.append(f"CHARACTERS PRESENT: {chars_short}")
    parts.append("Warm magical atmosphere, big expressive eyes, no text, no watermarks.")

    prompt = " ".join(parts)
    return prompt[:1000]


def _save_illustration_slim(
    text: str,
    n: int,
    output_dir: Path,
    secondary_block: str = "",
) -> Path:
    """
    Guarda el prompt de ilustración en ilustracionN.md, versión limpia:
      - Sin el bloque largo de Kira y Toby (eso va en el prompt de imagen)
      - Con una referencia compacta a personajes.py + personaje secundario
      - Mantiene ENVIRONMENT, CHARACTERS PRESENT, LIGHTING & MOOD,
        COMPOSITION & STYLE y CONTINUITY NOTES generados por OpenAI
    """
    # Eliminar la sección CHARACTERS DESCRIPTION (Kira/Toby full block)
    text_clean = re.sub(
        r"\nCHARACTERS DESCRIPTION:.*?(?=\nENVIRONMENT:|\nCHARACTERS PRESENT:|\Z)",
        "",
        text,
        count=1,
        flags=re.DOTALL | re.IGNORECASE,
    ).strip()

    # Cabecera de referencia
    ref_lines = [
        "# PERSONAJES — REFERENCIA",
        "> **Kira** y **Toby**: descripción visual completa en `config/personajes.py`",
    ]
    if secondary_block:
        ref_lines += ["", secondary_block]

    contenido = "\n".join(ref_lines) + "\n\n---\n\n" + text_clean
    path      = output_dir / f"ilustracion{n}.md"
    path.write_text(contenido, encoding="utf-8")
    return path


def build_characters_description(characters_data: dict) -> str:
    """
    Construye la descripción compacta de personajes para el contexto
    del agente generador (user_msg). No se guarda en el .md.
    """
    lines = ["=== PERSONAJES Y SUS CARACTERÍSTICAS FÍSICAS FIJAS ===\n"]

    if "personajesPrincipales" in characters_data:
        lines.append("── PERSONAJES PRINCIPALES ──")
        for p in characters_data["personajesPrincipales"]:
            lines.append(_format_character(p))

    if "personajesSecundarios" in characters_data:
        lines.append("\n── PERSONAJES SECUNDARIOS (incluir solo los presentes en la escena) ──")
        for p in characters_data["personajesSecundarios"]:
            lines.append(_format_character(p))

    if "objectosImportantes" in characters_data:
        lines.append("\n── OBJETOS IMPORTANTES (mantener consistencia visual) ──")
        for obj in characters_data["objectosImportantes"]:
            parts = [f"\n• {obj.get('nombre', '?').upper()}"]
            for k, v in obj.items():
                if k not in {"nombre", "forbidden_changes"}:
                    parts.append(f"  - {k}: {v}")
            if "forbidden_changes" in obj:
                parts.append(f"  ⚠️ NO CAMBIAR: {obj['forbidden_changes']}")
            lines.append("\n".join(parts))

    return "\n".join(lines)


def build_characters_block_for_scene(characters_data: dict) -> str:
    """
    Construye el bloque CHARACTERS DESCRIPTION que se incrusta en cada
    archivo escenaN.md guardado.

    Formato:
      CHARACTERS DESCRIPTION:
      kira: \"\"\"<prompt completo de personajes.py>\"\"\"
      toby: \"\"\"<prompt completo de personajes.py>\"\"\"
      <nombre secundario>: \"\"\"<prompt-3D limpio del secundario>\"\"\"

    Kira y Toby: se usan los prompts completos de config/personajes.py
    (descripción física exhaustiva con HEX, proporciones, negative prompts,
    consistencia visual obligatoria).

    Personaje secundario: se usa el campo prompt-3D del characters_data,
    limpiando las frases de fondo/pose que no aplican en el contexto de escena.

    Si characters_data no tiene los prompts de Kira/Toby (cuando se construye
    el dict mínimo en story_storage), usa los de personajes.py directamente.
    """
    from config.personajes import PERSONAJES

    bloques = ["CHARACTERS DESCRIPTION:"]

    # ── Kira ──────────────────────────────────────────────────────────────
    kira_prompt = PERSONAJES.get("kira", "")
    # Limpiar frases de pose/fondo que no aplican en escena
    kira_prompt = _limpiar_prompt_3d(kira_prompt)
    bloques.append(f'kira: """{kira_prompt}"""')

    # ── Toby ──────────────────────────────────────────────────────────────
    toby_prompt = PERSONAJES.get("toby", "")
    toby_prompt = _limpiar_prompt_3d(toby_prompt)
    bloques.append(f'toby: """{toby_prompt}"""')

    # ── Personaje(s) secundario(s) ─────────────────────────────────────────
    for p in characters_data.get("personajesSecundarios", []):
        nombre   = p.get("nombre", "personaje secundario")
        prompt3d = p.get("prompt-3D", "")
        if prompt3d:
            prompt3d_limpio = _limpiar_prompt_3d(prompt3d)
            bloques.append(f'"{nombre}": """{prompt3d_limpio}"""')
        else:
            # Sin prompt-3D: construir descripción compacta desde los campos disponibles
            campos = []
            skip   = {"nombre", "species", "prompt-3D", "forbidden_changes"}
            for k, v in p.items():
                if k not in skip:
                    campos.append(f"  - {k}: {v}")
            if "forbidden_changes" in p:
                campos.append(f"  *** NEVER CHANGE: {p['forbidden_changes']}")
            desc = f"{p.get('species', 'character')}, {p.get('nombre', '?')}.\n" + "\n".join(campos)
            bloques.append(f'"{nombre}": """{desc}"""')

    return "\n\n".join(bloques)


# ── Generación de escenas ─────────────────────────────────────────────────────

def _extract_continuity_notes(scene_text: str) -> str:
    """Extrae la sección CONTINUITY NOTES de un prompt generado."""
    match = re.search(
        r"CONTINUITY NOTES.*?:(.*?)(?=\n[A-Z]{2,}|\Z)",
        scene_text,
        re.DOTALL | re.IGNORECASE,
    )
    return match.group(1).strip() if match else ""


def _generate_single_scene(
    openai_client: OpenAI,
    paragraph: str,
    scene_number: int,
    total_scenes: int,
    characters_desc: str,
    previous_continuity: Optional[str],
    next_paragraph: Optional[str],
) -> tuple[str, dict]:
    """
    Genera el prompt de una escena individual.

    Returns:
        (prompt_text, usage_dict)
    """
    context_parts = []
    if previous_continuity:
        context_parts.append(f"CONTINUITY FROM PREVIOUS SCENE:\n{previous_continuity}")
    if next_paragraph:
        context_parts.append(
            f"NEXT PARAGRAPH (for visual continuity planning):\n{next_paragraph}"
        )

    user_msg = (
        f"{characters_desc}\n\n"
        f"{'═'*50}\n"
        f"CURRENT PARAGRAPH (Scene {scene_number} of {total_scenes}):\n"
        f"{'═'*50}\n"
        f"{paragraph}\n\n"
        f"{chr(10).join(context_parts)}\n\n"
        f"{'═'*50}\n"
        f"Generate the complete scene prompt for Scene {scene_number}.\n"
        f"Make it detailed enough for an AI video generator.\n"
        f"End with CONTINUITY NOTES for the next scene.\n"
        f"{'═'*50}"
    )

    response = openai_client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": _SCENE_SYSTEM},
            {"role": "user",   "content": user_msg},
        ],
        temperature=SCENE_TEMPERATURE,
        max_tokens=SCENE_MAX_TOKENS,
    )

    return (
        response.choices[0].message.content.strip(),
        {
            "prompt":     response.usage.prompt_tokens,
            "completion": response.usage.completion_tokens,
            "total":      response.usage.total_tokens,
        },
    )


# ── Validación y corrección ───────────────────────────────────────────────────

def _validate_and_correct(
    openai_client: OpenAI,
    scenes: dict[int, str],
    characters_desc: str,
    story_paragraphs: list[str],
    threshold: int,
) -> tuple[dict, dict]:
    """
    Llama al agente editor para evaluar coherencia.

    Returns:
        (report_dict, usage_dict)
    """
    scenes_text = ("\n\n" + "=" * 60 + "\n\n").join(
        f"SCENE {n}:\n{text}" for n, text in sorted(scenes.items())
    )
    story_ref = "\n".join(
        f"Paragraph {i+1}: {p}" for i, p in enumerate(story_paragraphs)
    )

    user_msg = (
        f"{characters_desc}\n\n"
        f"{'═'*50}\nORIGINAL STORY (reference):\n{'═'*50}\n{story_ref}\n\n"
        f"{'═'*50}\nGENERATED SCENE PROMPTS TO EVALUATE:\n{'═'*50}\n{scenes_text}\n\n"
        f"{'═'*50}\n"
        f"COHERENCE THRESHOLD: {threshold}%\n"
        f"Evaluate all scenes. Provide corrections if overall_score < {threshold}.\n"
        f"Respond ONLY with the JSON format. No markdown, no code blocks.\n"
        f"{'═'*50}"
    )

    response = openai_client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": _EDITOR_SYSTEM},
            {"role": "user",   "content": user_msg},
        ],
        temperature=EDITOR_TEMPERATURE,
        max_tokens=EDITOR_MAX_TOKENS,
    )

    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"```(?:json)?", "", raw).strip()

    usage = {
        "prompt":     response.usage.prompt_tokens,
        "completion": response.usage.completion_tokens,
        "total":      response.usage.total_tokens,
    }

    try:
        report = json.loads(raw)
    except json.JSONDecodeError:
        print("  ⚠️  El editor devolvió JSON inválido. Extracción parcial...")
        score_match = re.search(r'"overall_score"\s*:\s*(\d+)', raw)
        score = int(score_match.group(1)) if score_match else 50
        report = {
            "overall_score": score,
            "scene_scores": {},
            "issues": [],
            "corrections_needed": [],
            "summary": raw[:300],
            "passed": score >= threshold,
        }

    return report, usage


def _apply_corrections(
    scenes: dict[int, str],
    corrections: list[dict],
) -> tuple[dict[int, str], int]:
    """
    Aplica correcciones del editor. Devuelve (scenes_corregidas, n_aplicadas).
    """
    corrected = dict(scenes)
    applied = 0

    for fix in corrections:
        n     = fix.get("scene")
        orig  = fix.get("original_section", "")
        new   = fix.get("corrected_section", "")
        reason = fix.get("reason", "")

        if n and orig and new and n in corrected and orig in corrected[n]:
            corrected[n] = corrected[n].replace(orig, new, 1)
            applied += 1
            print(f"    ✏️  Escena {n}: {reason[:80]}")

    return corrected, applied


# ── Guardado de archivos ──────────────────────────────────────────────────────

def _inject_characters_block(scene_text: str, characters_block: str) -> str:
    """
    Inyecta el bloque CHARACTERS DESCRIPTION en el archivo de escena.

    El bloque canónico que se pasa ya empieza con "CHARACTERS DESCRIPTION:\n"
    (viene de build_characters_block_for_scene). La inyección lo escribe una
    sola vez, sin duplicar la etiqueta.

    Estrategia:
      1. Si el agente ya incluyó "CHARACTERS DESCRIPTION:" → reemplaza todo ese
         bloque (etiqueta + contenido anterior) por el bloque canónico.
      2. Si no lo incluyó → lo inserta antes de "ENVIRONMENT:".
      3. Fallback → lo inserta tras la primera línea de título "SCENE N —".
    """
    # Caso 1: el agente incluyó la etiqueta → reemplazar COMPLETO (etiqueta + contenido)
    # Capturamos desde la etiqueta hasta la siguiente sección en mayúsculas o fin
    pattern_existing = re.compile(
        r"CHARACTERS DESCRIPTION:.*?(?=\n[A-Z][A-Z &]+:|\Z)",
        re.DOTALL | re.IGNORECASE,
    )
    if pattern_existing.search(scene_text):
        return pattern_existing.sub(characters_block, scene_text, count=1)

    # Caso 2: insertar entre título y ENVIRONMENT:
    pattern_env = re.compile(r"(\nENVIRONMENT:)", re.IGNORECASE)
    if pattern_env.search(scene_text):
        return pattern_env.sub(f"\n\n{characters_block}\n\\1", scene_text, count=1)

    # Caso 3: fallback — insertar tras la primera línea "SCENE N —..."
    lines = scene_text.split("\n")
    for i, line in enumerate(lines):
        if line.strip().upper().startswith("SCENE "):
            lines.insert(i + 1, f"\n{characters_block}\n")
            return "\n".join(lines)

    # Último recurso
    return f"{characters_block}\n\n{scene_text}"


def _save_scene(
    text: str,
    n: int,
    output_dir: Path,
    characters_block: str = "",
) -> Path:
    """
    Guarda el prompt de una escena en escenaN.md.

    Si se pasa characters_block, lo inyecta en el archivo de forma determinista
    (siempre aparece, independientemente de lo que haya generado el agente).
    """
    contenido = _inject_characters_block(text, characters_block) if characters_block else text
    path = output_dir / f"escena{n}.md"
    path.write_text(contenido, encoding="utf-8")
    return path


def _save_report(report: dict, iteration: int, output_dir: Path) -> Path:
    path = output_dir / f"coherence_report_v{iteration}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    return path


def _save_summary(
    scenes: dict[int, str],
    report: dict,
    output_dir: Path,
    token_summary: dict,
) -> Path:
    """Genera RESUMEN_FINAL.md con puntuaciones, problemas y resumen de tokens."""
    score  = report.get("overall_score", 0)
    passed = report.get("passed", False)

    lines = [
        "# 🎬 RESUMEN FINAL — GENERADOR DE ESCENAS",
        "",
        f"## Puntuación de Coherencia: **{score}%** "
        f"{'✅ APROBADO' if passed else '❌ REQUIERE REVISIÓN MANUAL'}",
        "",
        "### Resumen del Editor:",
        report.get("summary", "N/A"),
        "",
        "---",
        "",
        "## Puntuaciones por Escena:",
        "",
    ]

    scene_scores = report.get("scene_scores", {})
    for n in sorted(scenes.keys()):
        sc    = scene_scores.get(str(n), scene_scores.get(n, "N/A"))
        emoji = "✅" if isinstance(sc, int) and sc >= 80 else "⚠️"
        lines.append(f"- **Escena {n}**: {sc}% {emoji}")

    issues = report.get("issues", [])
    if issues:
        lines += ["", "---", "", "## Problemas Detectados:", ""]
        for issue in issues:
            sev = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
                issue.get("severity", "low"), "⚪"
            )
            lines.append(
                f"- {sev} **Escena {issue.get('scene')}** "
                f"[{issue.get('type', '?')}]: {issue.get('description', '')}"
            )

    # ── Resumen de tokens ──────────────────────────────────────────────────
    ts = token_summary
    lines += [
        "",
        "---",
        "",
        "## 📊 Consumo de Tokens (este proceso)",
        "",
        f"| Concepto | Tokens | Costo estimado |",
        f"|----------|--------|----------------|",
        f"| Generación de escenas | {ts.get('scene_tokens', 0):,} | ${ts.get('scene_cost', 0):.4f} USD |",
        f"| Validación / Editor   | {ts.get('editor_tokens', 0):,} | ${ts.get('editor_cost', 0):.4f} USD |",
        f"| **TOTAL**             | **{ts.get('total_tokens', 0):,}** | **${ts.get('total_cost', 0):.4f} USD** |",
        "",
        "> Los costos son estimaciones basadas en precios públicos de OpenAI.",
        "> Consulta `logs/token_usage.json` para el historial acumulado.",
    ]

    lines += [
        "",
        "---",
        "",
        "## Archivos Generados:",
        "",
    ]
    for n in sorted(scenes.keys()):
        lines.append(f"- `escena{n}.md` — Prompt enriquecido para generador de video IA")

    lines += [
        "",
        "---",
        "_Generado automáticamente por scene_generator.py (Proyecto Estelar)_",
    ]

    path = output_dir / "RESUMEN_FINAL.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


# ── Pipeline principal ────────────────────────────────────────────────────────

def generar_escenas_desde_historia(
    story_text: str,
    characters_data: dict,
    output_dir: Path,
    threshold: int = COHERENCE_THRESHOLD,
    only_validate: bool = False,
    historia_titulo: str = "",
) -> dict:
    """
    Pipeline completo: texto de historia → prompts de escenas validados.

    Args:
        story_text:       Texto completo de la historia (extraído del .txt)
        characters_data:  Dict del characters.json (personajesPrincipales, etc.)
        output_dir:       Carpeta donde guardar los escenaN.md
                          (normalmente: outputs/historias/revision/TITULO/prompts-scenas/)
        threshold:        Porcentaje mínimo de coherencia (default: 85)
        only_validate:    Si True, solo valida escenas ya existentes
        historia_titulo:  Título para mostrar en los mensajes de consola

    Returns:
        dict con:
          - scenes_count     (int)
          - coherence_score  (int)
          - passed           (bool)
          - output_dir       (str)
          - tokens           (dict con desglose)
          - costo_estimado_usd (float)
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    tracker.set_log_path(LOGS_DIR)

    openai_client = OpenAI()

    label = f" — {historia_titulo}" if historia_titulo else ""
    print(f"\n{'═'*62}")
    print(f"   🎬  GENERADOR DE ESCENAS{label}")
    print(f"{'═'*62}\n")

    # 1. Preparar datos ────────────────────────────────────────────────────
    characters_desc  = build_characters_description(characters_data)
    characters_block = build_characters_block_for_scene(characters_data)

    # Extraer párrafos de la historia
    # El .txt tiene cabecera con ===, extraemos solo el bloque de texto narrativo
    story_clean = _extract_story_text(story_text)
    paragraphs  = [p.strip() for p in re.split(r"\n\s*\n", story_clean.strip()) if p.strip()]
    total       = len(paragraphs)
    print(f"📖 Párrafos detectados: {total}\n")

    token_summary = {
        "scene_tokens": 0, "scene_cost": 0.0,
        "editor_tokens": 0, "editor_cost": 0.0,
        "total_tokens": 0, "total_cost": 0.0,
    }

    # 2. Generar o cargar escenas ──────────────────────────────────────────
    scenes: dict[int, str] = {}

    if only_validate:
        print("🔍 Modo solo-validación: cargando escenas existentes...")
        for i in range(1, total + 1):
            path = output_dir / f"escena{i}.md"
            if path.exists():
                texto_existente = path.read_text(encoding="utf-8")
                # Re-inyectar el bloque de personajes aunque ya exista la escena
                # (actualiza con los personajes actuales del characters.json)
                scenes[i] = texto_existente
                _save_scene(texto_existente, i, output_dir, characters_block)
                print(f"  ✅ escena{i}.md cargada (bloque de personajes actualizado)")
            else:
                print(f"  ❌ escena{i}.md no encontrada — saltando")
    else:
        print(f"🖊️  Generando {total} prompts de escenas...\n")
        continuity = None

        for i, paragraph in enumerate(paragraphs, start=1):
            print(f"  🎨 Generando escena {i}/{total}...")

            next_para = paragraphs[i] if i < total else None

            prompt_text, usage = _generate_single_scene(
                openai_client=openai_client,
                paragraph=paragraph,
                scene_number=i,
                total_scenes=total,
                characters_desc=characters_desc,
                previous_continuity=continuity,
                next_paragraph=next_para,
            )

            scenes[i]  = prompt_text
            _save_scene(prompt_text, i, output_dir, characters_block)
            continuity = _extract_continuity_notes(prompt_text)

            # Registrar tokens
            entry = tracker.register_openai(
                operation=f"escena_{i}_de_{total}",
                model=OPENAI_MODEL,
                prompt_tokens=usage["prompt"],
                completion_tokens=usage["completion"],
                total_tokens=usage["total"],
                metadata={"historia": historia_titulo, "escena": i},
            )
            token_summary["scene_tokens"] += usage["total"]
            token_summary["scene_cost"]   += entry["estimated_cost_usd"]
            tracker.print_entry(entry)

            print(f"    ✅ escena{i}.md guardada")
            time.sleep(0.3)

    if not scenes:
        print("❌ No hay escenas para procesar.")
        return {"scenes_count": 0, "coherence_score": 0, "passed": False}

    # 3. Bucle de validación + corrección ─────────────────────────────────
    print(f"\n{'═'*62}")
    print(f"   🔬  AGENTE EDITOR — VALIDANDO (umbral: {threshold}%)")
    print(f"{'═'*62}\n")

    final_report = {}
    for iteration in range(1, MAX_FIX_ITERATIONS + 1):
        print(f"  Iteración {iteration}/{MAX_FIX_ITERATIONS}...")

        report, usage = _validate_and_correct(
            openai_client, scenes, characters_desc, paragraphs, threshold
        )
        final_report = report

        # Registrar tokens del editor
        entry = tracker.register_openai(
            operation=f"editor_iteracion_{iteration}",
            model=OPENAI_MODEL,
            prompt_tokens=usage["prompt"],
            completion_tokens=usage["completion"],
            total_tokens=usage["total"],
            metadata={"historia": historia_titulo, "iteracion": iteration},
        )
        token_summary["editor_tokens"] += usage["total"]
        token_summary["editor_cost"]   += entry["estimated_cost_usd"]
        tracker.print_entry(entry)

        score  = report.get("overall_score", 0)
        passed = report.get("passed", False)
        issues = report.get("issues", [])
        fixes  = report.get("corrections_needed", [])

        _save_report(report, iteration, output_dir)
        print(f"  📊 Score: {score}% | Problemas: {len(issues)} | Correcciones: {len(fixes)}")

        if passed:
            print(f"\n  ✅ COHERENCIA APROBADA ({score}% ≥ {threshold}%)")
            break

        if fixes and iteration < MAX_FIX_ITERATIONS:
            print(f"\n  ⚙️  Aplicando {len(fixes)} correcciones...")
            scenes, applied = _apply_corrections(scenes, fixes)
            print(f"  → {applied}/{len(fixes)} aplicadas")
            for n, text in scenes.items():
                _save_scene(text, n, output_dir, characters_block)
        elif iteration == MAX_FIX_ITERATIONS:
            print(
                f"\n  ⚠️  Máximo de iteraciones alcanzado. "
                f"Score final: {score}%. Revisión manual recomendada."
            )

    # 4. Totales y resumen final ───────────────────────────────────────────
    token_summary["total_tokens"] = token_summary["scene_tokens"] + token_summary["editor_tokens"]
    token_summary["total_cost"]   = round(token_summary["scene_cost"] + token_summary["editor_cost"], 6)

    summary_path = _save_summary(scenes, final_report, output_dir, token_summary)

    final_score = final_report.get("overall_score", 0)
    final_passed = final_report.get("passed", False)

    print(f"\n{'═'*62}")
    print(f"   🏁  PROCESO COMPLETADO")
    print(f"{'═'*62}")
    print(f"\n  📁 Salida: {output_dir.resolve()}")
    for n in sorted(scenes.keys()):
        print(f"     • escena{n}.md")
    print(f"     • RESUMEN_FINAL.md")
    print(f"     • coherence_report_v*.json")
    print(f"\n  📊 Tokens usados (este proceso): {token_summary['total_tokens']:,}")
    print(f"  💰 Costo estimado:               ${token_summary['total_cost']:.4f} USD\n")

    return {
        "scenes_count":       len(scenes),
        "coherence_score":    final_score,
        "passed":             final_passed,
        "output_dir":         str(output_dir),
        "tokens":             token_summary,
        "costo_estimado_usd": token_summary["total_cost"],
    }


# ── Helper: extraer solo el texto narrativo del .txt ─────────────────────────

def _extract_story_text(full_txt: str) -> str:
    """
    Extrae ÚNICAMENTE los párrafos narrativos de la historia.

    El .txt generado por story_storage tiene este formato:
        ===...===
        HISTORIA GENERADA — KIRA Y TOBY
        ===...===
        Fecha y hora: ...
        Modelo: ...
        ===...===

        **TÍTULO:** ...

        **HISTORIA:**
        <párrafo 1>

        <párrafo 2>
        ...

        **MORALEJA:**
        ...

        **ESCENAS:**
        ...

        ===...===
        ELEMENTOS UTILIZADOS:
        ...

    Solo queremos los párrafos entre **HISTORIA:** y la siguiente sección
    (**MORALEJA:**, **ESCENAS:** o la línea de ===).

    Funciona también con .md o .txt planos (sin cabecera).
    """

    # ── Intento 1: extraer bloque HISTORIA → siguiente sección ────────────
    # Soporta dos formatos que GPT puede generar:
    #   **HISTORIA:**   (negrita, formato pedido en el prompt)
    #   ### HISTORIA:   (heading markdown, formato alternativo)
    historia_match = re.search(
        r"(?:\*\*HISTORIA:\*\*|#{1,3}\s*HISTORIA:)\s*\n"
        r"(.*?)"
        r"(?=\n(?:\*\*(?:MORALEJA|ESCENAS):\*\*|#{1,3}\s*(?:MORALEJA|ESCENAS):)|={10,}|\Z)",
        full_txt,
        re.DOTALL,
    )
    if historia_match:
        texto = historia_match.group(1).strip()
        if texto:
            return texto

    # ── Intento 2: extraer el bloque del .txt con cabecera === ─────────────
    # Toma todo lo que está entre la cabecera y ELEMENTOS UTILIZADOS
    bloque_match = re.compile(
        r"={10,}\n"
        r"(?:Fecha.*?\n.*?\n)?"
        r"={10,}\n\n"
        r"(.*?)"
        r"\n\n={10,}",
        re.DOTALL,
    ).search(full_txt)

    if bloque_match:
        bloque = bloque_match.group(1).strip()
        # Del bloque, quedarnos solo con los párrafos que no son headers markdown
        # Filtramos líneas que empiezan con ** (secciones como **TÍTULO:**, etc.)
        paragraphs = []
        current = []
        for line in bloque.split("\n"):
            stripped = line.strip()
            # Detectar inicio de sección markdown tipo **SECCIÓN:**
            if re.match(r"^\*\*[A-ZÁÉÍÓÚÑ\s]+:\*\*", stripped):
                if current:
                    block_text = "\n".join(current).strip()
                    if block_text:
                        paragraphs.append(block_text)
                    current = []
                # Si es **HISTORIA:** empezamos a capturar
                if "HISTORIA" in stripped.upper():
                    current = []
                else:
                    current = None   # type: ignore  # parar captura
            elif current is not None:
                current.append(line)

        if current:
            block_text = "\n".join(current).strip()
            if block_text:
                paragraphs.append(block_text)

        if paragraphs:
            return "\n\n".join(paragraphs)

    # ── Fallback: texto plano (sin formato de proyecto) ────────────────────
    # Útil para .md puros o historia.md de prueba
    return full_txt.strip()


# ── Generador de ilustraciones de cuento ─────────────────────────────────────

def _generate_single_illustration(
    openai_client: OpenAI,
    paragraph: str,
    scene_number: int,
    total_scenes: int,
    characters_desc: str,
    previous_continuity: Optional[str],
    next_paragraph: Optional[str],
) -> tuple[str, dict]:
    """
    Genera el prompt de UNA ilustración de cuento infantil.
    Usa _ILLUSTRATION_SYSTEM en lugar de _SCENE_SYSTEM.

    Returns:
        (prompt_text, usage_dict)
    """
    context_parts = []
    if previous_continuity:
        context_parts.append(f"CONTINUITY FROM PREVIOUS ILLUSTRATION:\n{previous_continuity}")
    if next_paragraph:
        context_parts.append(
            f"NEXT PARAGRAPH (for visual continuity planning):\n{next_paragraph}"
        )

    user_msg = (
        f"{characters_desc}\n\n"
        f"{'═'*50}\n"
        f"STORY PARAGRAPH (Illustration {scene_number} of {total_scenes}):\n"
        f"{'═'*50}\n"
        f"{paragraph}\n\n"
        f"{chr(10).join(context_parts)}\n\n"
        f"{'═'*50}\n"
        f"Generate the complete illustration prompt for Illustration {scene_number}.\n"
        f"The ENVIRONMENT section must be VERY detailed (at least 6 lines):\n"
        f"  - Exact location, time of day, type of sky\n"
        f"  - Light sources, shadows, color temperature\n"
        f"  - Dominant color palette with HEX codes where possible\n"
        f"  - Surface textures (ground, walls, vegetation, water, etc.)\n"
        f"  - Foreground / midground / background elements\n"
        f"  - Decorative details that reinforce the story atmosphere\n"
        f"Do NOT include ACTION & MOVEMENT or CAMERA sections.\n"
        f"End with short CONTINUITY NOTES for the next illustration.\n"
        f"{'═'*50}"
    )

    response = openai_client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": _ILLUSTRATION_SYSTEM},
            {"role": "user",   "content": user_msg},
        ],
        temperature=SCENE_TEMPERATURE,
        max_tokens=SCENE_MAX_TOKENS + 500,   # más tokens para el ENVIRONMENT expandido
    )

    return (
        response.choices[0].message.content.strip(),
        {
            "prompt":     response.usage.prompt_tokens,
            "completion": response.usage.completion_tokens,
            "total":      response.usage.total_tokens,
        },
    )


def _save_illustration(
    text: str,
    n: int,
    output_dir: Path,
    characters_block: str = "",
) -> Path:
    """Guarda el prompt de ilustración en ilustracionN.md con el bloque de personajes inyectado."""
    contenido = _inject_characters_block(text, characters_block) if characters_block else text
    path = output_dir / f"ilustracion{n}.md"
    path.write_text(contenido, encoding="utf-8")
    return path


def generar_ilustraciones_desde_historia(
    story_text: str,
    characters_data: dict,
    output_dir: Path,
    historia_titulo: str = "",
    model: str = "gemini",
) -> dict:
    """
    Pipeline completo: texto de historia → prompts de ilustración de cuento.

    Genera un archivo ilustracionN.md por cada párrafo de la historia.
    Los prompts están optimizados para generadores de imagen estática
    (Midjourney, DALL-E 3, Adobe Firefly, Stable Diffusion XL).

    Diferencias respecto a generar_escenas_desde_historia:
      - Usa _ILLUSTRATION_SYSTEM (sin ACTION, sin CAMERA, ENVIRONMENT expandido)
      - Guarda en ilustracionN.md (no en escenaN.md)
      - No ejecuta el agente editor de coherencia (no aplica para imágenes estáticas)
      - El ENVIRONMENT se genera con mucho más detalle visual

    Args:
        story_text:       Texto completo de la historia (el .txt con cabecera)
        characters_data:  Dict del characters.json
        output_dir:       Carpeta de salida (normalmente prompts-scenas/)
        historia_titulo:  Título para los mensajes de consola

    Returns:
        dict con scenes_count, output_dir, tokens, costo_estimado_usd
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    tracker.set_log_path(LOGS_DIR)

    openai_client = OpenAI()

    label = f" — {historia_titulo}" if historia_titulo else ""
    print(f"\n{'═'*62}")
    print(f"   🖼️  GENERADOR DE ILUSTRACIONES{label}")
    print(f"{'═'*62}\n")

    # characters_desc → contexto compacto para que OpenAI genere buenos ENVIRONMENT etc.
    # secondary_block → bloque slim solo con el secundario, para el encabezado del .md
    characters_desc  = build_characters_description(characters_data)
    secondary_block  = _build_secondary_block_for_md(characters_data)

    story_clean = _extract_story_text(story_text)
    paragraphs  = [p.strip() for p in re.split(r"\n\s*\n", story_clean.strip()) if p.strip()]
    total       = len(paragraphs)
    print(f"📖 Párrafos detectados: {total}\n")

    token_summary = {
        "illus_tokens": 0, "illus_cost": 0.0,
        "img_count":    0, "img_cost":   0.0,
        "total_tokens": 0, "total_cost": 0.0,
    }

    illustrations: dict[int, str] = {}
    continuity = None

    print(f"🖊️  Generando {total} ilustraciones (prompt .md + imagen PNG)...\n")

    # Import lazy para no requerir google-genai si solo se generan .md
    try:
        from .image_generator import _llamar_imagen_api
        _imagen_disponible = True
    except Exception:
        _imagen_disponible = False
        print("  ⚠️  image_generator no disponible — solo se generarán los .md\n")

    for i, paragraph in enumerate(paragraphs, start=1):
        print(f"  🎨 Generando ilustración {i}/{total}...")

        next_para = paragraphs[i] if i < total else None

        prompt_text, usage = _generate_single_illustration(
            openai_client=openai_client,
            paragraph=paragraph,
            scene_number=i,
            total_scenes=total,
            characters_desc=characters_desc,
            previous_continuity=continuity,
            next_paragraph=next_para,
        )

        illustrations[i] = prompt_text

        # ── 1. Guardar .md limpio (sin Kira/Toby extendidos) ──────────────
        _save_illustration_slim(prompt_text, i, output_dir, secondary_block)
        continuity = _extract_continuity_notes(prompt_text)

        entry = tracker.register_openai(
            operation=f"ilustracion_{i}_de_{total}",
            model=OPENAI_MODEL,
            prompt_tokens=usage["prompt"],
            completion_tokens=usage["completion"],
            total_tokens=usage["total"],
            metadata={"historia": historia_titulo, "ilustracion": i},
        )
        token_summary["illus_tokens"] += usage["total"]
        token_summary["illus_cost"]   += entry["estimated_cost_usd"]
        tracker.print_entry(entry)
        print(f"    ✅ ilustracion{i}.md guardada")

        # ── 2. Generar PNG ────────────────────────────────────────────────
        if _imagen_disponible:
            if model == "runway":
                imagen_prompt = _build_runway_prompt_from_illustration(
                    prompt_text, characters_data
                )
            else:
                imagen_prompt = _build_imagen_prompt_from_illustration(
                    prompt_text, characters_data
                )
            imagen_bytes = _llamar_imagen_api(imagen_prompt, model=model)
            if imagen_bytes:
                ruta_png = output_dir / f"ilustracion{i}.png"
                ruta_png.write_bytes(imagen_bytes)
                img_entry = tracker.register_image(
                    operation=f"ilustracion_png_{i}_de_{total}",
                    model=IMAGE_MODEL,
                    images_count=1,
                    metadata={"historia": historia_titulo, "ilustracion": i, "backend": model},
                )
                token_summary["img_count"] += 1
                token_summary["img_cost"]  += img_entry.get("estimated_cost_usd", 0.0)
                tracker.print_entry(img_entry)
                print(f"    🖼️  ilustracion{i}.png generada")
            else:
                print(f"    ⚠️  PNG no generado para ilustración {i} (fallo de API)")

        time.sleep(0.3)

    token_summary["total_tokens"] = token_summary["illus_tokens"]
    token_summary["total_cost"]   = round(
        token_summary["illus_cost"] + token_summary["img_cost"], 6
    )

    imgs_ok = token_summary["img_count"]
    print(f"\n{'═'*62}")
    print(f"   🏁  ILUSTRACIONES COMPLETADAS")
    print(f"{'═'*62}")
    print(f"\n  📁 Salida: {output_dir.resolve()}")
    for n in sorted(illustrations.keys()):
        png_ok = (output_dir / f"ilustracion{n}.png").exists()
        print(f"     • ilustracion{n}.md {'+ ilustracion' + str(n) + '.png' if png_ok else '(solo .md)'}")
    print(f"\n  📊 Tokens texto:   {token_summary['illus_tokens']:,}")
    print(f"  🖼️  Imágenes PNG:   {imgs_ok}/{total}")
    print(f"  💰 Costo estimado: ${token_summary['total_cost']:.4f} USD\n")

    return {
        "scenes_count":       len(illustrations),
        "output_dir":         str(output_dir),
        "tokens":             token_summary,
        "costo_estimado_usd": token_summary["total_cost"],
    }


# ── Punto de entrada standalone (para uso directo) ────────────────────────────

def run_standalone(
    story_path: str,
    characters_path: str,
    output_dir: str = ".",
    threshold: int = COHERENCE_THRESHOLD,
    only_validate: bool = False,
):
    """
    Ejecución directa sin pasar por main.py del proyecto Estelar.
    Útil para procesar historias guardadas manualmente.

    Args:
        story_path:      Ruta al .txt o .md con la historia
        characters_path: Ruta al characters.json
        output_dir:      Directorio donde guardar los escenaN.md
        threshold:       Umbral de coherencia
        only_validate:   Solo validar escenas existentes
    """
    story_text = Path(story_path).read_text(encoding="utf-8")

    with open(characters_path, "r", encoding="utf-8") as f:
        characters_data = json.load(f)

    titulo = Path(story_path).stem

    generar_escenas_desde_historia(
        story_text=story_text,
        characters_data=characters_data,
        output_dir=Path(output_dir),
        threshold=threshold,
        only_validate=only_validate,
        historia_titulo=titulo,
    )