"""
╔══════════════════════════════════════════════════════════════════════════════╗
║           GENERADOR DE ESCENAS PARA HISTORIAS ANIMADAS                       ║
║           Con IA OpenAI + Sistema de Coherencia Multi-Agente                 ║
╚══════════════════════════════════════════════════════════════════════════════╝

USO:
    python scene_generator.py --story historia.md --characters characters.json
    python scene_generator.py --story historia.md --characters characters.json --only-validate
    python scene_generator.py --story historia.md --characters characters.json --threshold 90

REQUISITOS:
    pip install openai python-dotenv

ARCHIVOS NECESARIOS:
    - historia.md         → La historia a procesar
    - characters.json     → Descripción física de los personajes
    - .env                → OPENAI_API_KEY=sk-...
"""

import os
import json
import re
import time
import argparse
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from openai import OpenAI

# ─── Configuración ────────────────────────────────────────────────────────────

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL_SCENE    = "gpt-4o"          # Modelo para generar escenas individuales
MODEL_EDITOR   = "gpt-4o"          # Modelo para el agente editor/validador
COHERENCE_THRESHOLD = 85           # % mínimo para dar la historia como buena
MAX_FIX_ITERATIONS  = 3            # Máximo de intentos de corrección automática


# ─── Lectura de personajes ─────────────────────────────────────────────────────

def load_characters(characters_path: str) -> str:
    """
    Lee el JSON de personajes y devuelve una descripción compacta
    lista para ser incluida en los prompts del generador de escenas.
    """
    with open(characters_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    lines = ["=== PERSONAJES Y SUS CARACTERÍSTICAS FÍSICAS FIJAS ===\n"]

    # Personajes principales (si el JSON los tiene separados)
    if "personajesPrincipales" in data:
        lines.append("── PERSONAJES PRINCIPALES ──")
        for p in data["personajesPrincipales"]:
            lines.append(_format_character(p))

    # Personajes secundarios
    if "personajesSecundarios" in data:
        lines.append("\n── PERSONAJES SECUNDARIOS (usar solo los presentes en la escena) ──")
        for p in data["personajesSecundarios"]:
            lines.append(_format_character(p))

    return "\n".join(lines)


def _format_character(p: dict) -> str:
    """Formatea un personaje para el contexto del prompt."""
    parts = [f"\n• {p.get('nombre','?').upper()} ({p.get('species','?')})"]
    skip = {"nombre", "species", "prompt-3D", "forbidden_changes"}
    for k, v in p.items():
        if k not in skip:
            parts.append(f"  - {k}: {v}")
    if "forbidden_changes" in p:
        parts.append(f"  ⚠️ NO CAMBIAR: {p['forbidden_changes']}")
    return "\n".join(parts)


# ─── Lectura de la historia ────────────────────────────────────────────────────

def load_story(story_path: str) -> list[str]:
    """
    Lee historia.md y devuelve una lista de párrafos no vacíos.
    """
    text = Path(story_path).read_text(encoding="utf-8")
    # Dividir por líneas en blanco
    raw_paragraphs = re.split(r"\n\s*\n", text.strip())
    paragraphs = [p.strip() for p in raw_paragraphs if p.strip()]
    print(f"📖 Historia cargada: {len(paragraphs)} párrafos encontrados.")
    return paragraphs


# ─── Generador de escenas individuales ────────────────────────────────────────

SCENE_SYSTEM_PROMPT = """Eres un experto director creativo especializado en animación CGI estilo Pixar/Disney.
Tu trabajo es convertir párrafos de una historia infantil en prompts altamente detallados 
para generadores de video IA (como Sora, Runway ML, Pika, Kling).

REGLAS CRÍTICAS:
1. El prompt debe ser en INGLÉS (los generadores de video IA responden mejor en inglés).
2. Mantén ABSOLUTA coherencia visual con los personajes descritos (colores hex exactos, proporciones, accesorios).
3. Cada escena debe incluir: ambiente, iluminación, cámara, acción, emoción y continuidad.
4. Incluye al final una sección "CONTINUITY NOTES" con elementos visuales que DEBEN aparecer en la siguiente escena.
5. El estilo visual es: 3D CGI animation, Pixar/Disney quality, soft studio lighting, vibrant colors, 8K render.
6. NO inventes características físicas nuevas para los personajes. Úsalas exactamente como se describe.
7. La duración estimada de cada clip debe ser de 5-8 segundos de video.

ESTRUCTURA DEL PROMPT DE ESCENA:
```
SCENE [N] — [TÍTULO CORTO DE LA ESCENA]

ENVIRONMENT:
[Descripción del ambiente, hora del día, clima, paleta de colores]

CHARACTERS PRESENT:
[Lista de personajes en escena con su estado emocional]

ACTION & MOVEMENT:
[Qué ocurre exactamente, movimientos de cámara, secuencia de acción]

CAMERA:
[Tipo de plano, ángulo, movimiento de cámara]

LIGHTING & MOOD:
[Iluminación específica, atmósfera emocional]

TECHNICAL:
[Estilo 3D, calidad render, duración estimada]

CONTINUITY NOTES (for next scene):
[Elementos visuales, posición de personajes, objetos, clima que deben continuar]
```
"""

def generate_scene_prompt(
    paragraph: str,
    scene_number: int,
    total_scenes: int,
    characters_description: str,
    previous_continuity: Optional[str],
    next_paragraph: Optional[str],
) -> str:
    """
    Genera el prompt de una escena individual usando GPT-4o.
    """
    context_parts = []

    if previous_continuity:
        context_parts.append(f"CONTINUITY FROM PREVIOUS SCENE:\n{previous_continuity}")

    if next_paragraph:
        context_parts.append(
            f"NEXT PARAGRAPH (for visual continuity planning):\n{next_paragraph}"
        )

    user_message = f"""
{characters_description}

══════════════════════════════════════════
CURRENT PARAGRAPH (Scene {scene_number} of {total_scenes}):
══════════════════════════════════════════
{paragraph}

{chr(10).join(context_parts)}

══════════════════════════════════════════
Generate the complete scene prompt for Scene {scene_number}.
Make it detailed enough for an AI video generator.
End with CONTINUITY NOTES for the next scene.
══════════════════════════════════════════
"""

    response = client.chat.completions.create(
        model=MODEL_SCENE,
        messages=[
            {"role": "system", "content": SCENE_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.7,
        max_tokens=1500,
    )
    return response.choices[0].message.content.strip()


def extract_continuity_notes(scene_prompt: str) -> str:
    """Extrae las CONTINUITY NOTES de un prompt de escena generado."""
    match = re.search(
        r"CONTINUITY NOTES.*?:(.*?)(?=\n[A-Z]{2,}|\Z)",
        scene_prompt,
        re.DOTALL | re.IGNORECASE,
    )
    return match.group(1).strip() if match else ""


# ─── Agente Editor / Validador de coherencia ──────────────────────────────────

EDITOR_SYSTEM_PROMPT = """Eres un editor experto en narrativa visual, especializado en animación CGI y storyboarding.
Tu trabajo es revisar una secuencia de prompts de escenas para un video animado y evaluar:

1. COHERENCIA VISUAL: ¿Los personajes mantienen sus características físicas consistentes?
2. COHERENCIA NARRATIVA: ¿La historia fluye lógicamente de escena en escena?
3. CONTINUIDAD DE AMBIENTE: ¿El ambiente, luz y objetos se mantienen consistentes entre escenas?
4. CONTINUIDAD DE ACCIONES: ¿Las acciones conectan fluidamente entre escenas?
5. CLARIDAD PARA IA VIDEO: ¿Cada prompt es lo suficientemente claro y detallado para un generador de video IA?

RESPONDE EN ESTE FORMATO JSON EXACTO (sin markdown, sin bloques de código):
{
  "overall_score": <número 0-100>,
  "scene_scores": {
    "1": <número 0-100>,
    "2": <número 0-100>,
    ...
  },
  "issues": [
    {
      "scene": <número>,
      "type": "visual|narrative|continuity|clarity",
      "description": "<descripción del problema>",
      "severity": "low|medium|high"
    }
  ],
  "corrections_needed": [
    {
      "scene": <número>,
      "original_section": "<texto exacto a reemplazar>",
      "corrected_section": "<texto corregido>",
      "reason": "<razón del cambio>"
    }
  ],
  "summary": "<resumen ejecutivo de máximo 3 oraciones>",
  "passed": <true si overall_score >= umbral, false en caso contrario>
}
"""

def validate_and_correct(
    scenes: dict[int, str],
    characters_description: str,
    story_paragraphs: list[str],
    threshold: int,
) -> dict:
    """
    El agente editor lee todos los prompts y devuelve un análisis JSON
    con puntuación de coherencia y correcciones necesarias.
    """
    scenes_text = "\n\n" + "=" * 60 + "\n\n"
    scenes_text = scenes_text.join(
        [f"SCENE {n}:\n{text}" for n, text in sorted(scenes.items())]
    )

    user_message = f"""
{characters_description}

══════════════════════════════════════════
ORIGINAL STORY (for reference):
══════════════════════════════════════════
{chr(10).join([f'Paragraph {i+1}: {p}' for i, p in enumerate(story_paragraphs)])}

══════════════════════════════════════════
GENERATED SCENE PROMPTS TO EVALUATE:
══════════════════════════════════════════
{scenes_text}

══════════════════════════════════════════
COHERENCE THRESHOLD: {threshold}%
Evaluate all scenes and provide corrections if overall_score < {threshold}.
Respond ONLY with the JSON format specified. No markdown, no code blocks.
══════════════════════════════════════════
"""

    response = client.chat.completions.create(
        model=MODEL_EDITOR,
        messages=[
            {"role": "system", "content": EDITOR_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.3,
        max_tokens=3000,
    )

    raw = response.choices[0].message.content.strip()
    # Limpiar posibles bloques de código markdown
    raw = re.sub(r"```(?:json)?", "", raw).strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        print("⚠️  El editor devolvió JSON inválido. Intentando extracción parcial...")
        # Intento de extracción básica
        score_match = re.search(r'"overall_score"\s*:\s*(\d+)', raw)
        score = int(score_match.group(1)) if score_match else 50
        return {
            "overall_score": score,
            "scene_scores": {},
            "issues": [],
            "corrections_needed": [],
            "summary": raw[:300],
            "passed": score >= threshold,
        }


def apply_corrections(scenes: dict[int, str], corrections: list[dict]) -> dict[int, str]:
    """
    Aplica las correcciones sugeridas por el agente editor a las escenas.
    """
    corrected = {k: v for k, v in scenes.items()}
    applied = 0

    for fix in corrections:
        scene_num = fix.get("scene")
        original  = fix.get("original_section", "")
        corrected_text = fix.get("corrected_section", "")

        if scene_num and original and corrected_text and scene_num in corrected:
            if original in corrected[scene_num]:
                corrected[scene_num] = corrected[scene_num].replace(
                    original, corrected_text, 1
                )
                applied += 1
                print(f"   ✏️  Corrección aplicada en escena {scene_num}: {fix.get('reason','')[:80]}")

    print(f"   → {applied}/{len(corrections)} correcciones aplicadas.")
    return corrected


# ─── Gestión de archivos ──────────────────────────────────────────────────────

def save_scene(scene_prompt: str, scene_number: int, output_dir: Path) -> Path:
    path = output_dir / f"escena{scene_number}.md"
    path.write_text(scene_prompt, encoding="utf-8")
    return path


def load_scene(scene_number: int, output_dir: Path) -> Optional[str]:
    path = output_dir / f"escena{scene_number}.md"
    return path.read_text(encoding="utf-8") if path.exists() else None


def save_report(report: dict, iteration: int, output_dir: Path) -> Path:
    path = output_dir / f"coherence_report_v{iteration}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    return path


def save_summary(scenes: dict, final_report: dict, output_dir: Path):
    """Genera un resumen final legible en Markdown."""
    path = output_dir / "RESUMEN_FINAL.md"
    score = final_report.get("overall_score", 0)
    passed = final_report.get("passed", False)

    lines = [
        "# 🎬 RESUMEN FINAL — GENERADOR DE ESCENAS",
        "",
        f"## Puntuación de Coherencia: **{score}%** {'✅ APROBADO' if passed else '❌ REQUIERE REVISIÓN MANUAL'}",
        "",
        f"### Resumen del Editor:",
        final_report.get("summary", "N/A"),
        "",
        "---",
        "",
        "## Puntuaciones por Escena:",
        "",
    ]

    scene_scores = final_report.get("scene_scores", {})
    for n in sorted(scenes.keys()):
        sc = scene_scores.get(str(n), scene_scores.get(n, "N/A"))
        emoji = "✅" if isinstance(sc, int) and sc >= 80 else "⚠️"
        lines.append(f"- **Escena {n}**: {sc}% {emoji}")

    issues = final_report.get("issues", [])
    if issues:
        lines += ["", "---", "", "## Problemas Detectados:", ""]
        for issue in issues:
            severity_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
                issue.get("severity", "low"), "⚪"
            )
            lines.append(
                f"- {severity_emoji} **Escena {issue.get('scene')}** [{issue.get('type','?')}]: {issue.get('description','')}"
            )

    lines += [
        "",
        "---",
        "",
        "## Archivos Generados:",
        "",
    ]
    for n in sorted(scenes.keys()):
        lines.append(f"- `escena{n}.md` — Prompt para generador de video IA")

    lines += [
        "",
        "---",
        "_Generado automáticamente por scene_generator.py_",
    ]

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


# ─── Pipeline principal ────────────────────────────────────────────────────────

def run_pipeline(
    story_path: str,
    characters_path: str,
    output_dir: str = ".",
    threshold: int = COHERENCE_THRESHOLD,
    only_validate: bool = False,
):
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    print("\n" + "═" * 60)
    print("   🎬  GENERADOR DE ESCENAS ANIMADAS — INICIANDO")
    print("═" * 60 + "\n")

    # 1. Cargar datos
    print("📂 Cargando personajes...")
    characters_desc = load_characters(characters_path)

    print("📖 Cargando historia...")
    paragraphs = load_story(story_path)
    total = len(paragraphs)

    # 2. Generar o cargar escenas
    scenes: dict[int, str] = {}

    if only_validate:
        print("\n🔍 Modo solo-validación: cargando escenas existentes...")
        for i in range(1, total + 1):
            content = load_scene(i, output)
            if content:
                scenes[i] = content
                print(f"   ✅ escena{i}.md cargada")
            else:
                print(f"   ❌ escena{i}.md no encontrada — salteando")
    else:
        print(f"\n🖊️  Generando {total} prompts de escenas...\n")
        continuity = None

        for i, paragraph in enumerate(paragraphs, start=1):
            print(f"  🎨 Generando escena {i}/{total}...")

            next_para = paragraphs[i] if i < total else None

            prompt = generate_scene_prompt(
                paragraph=paragraph,
                scene_number=i,
                total_scenes=total,
                characters_description=characters_desc,
                previous_continuity=continuity,
                next_paragraph=next_para,
            )

            scenes[i] = prompt
            path = save_scene(prompt, i, output)
            continuity = extract_continuity_notes(prompt)

            print(f"     ✅ escena{i}.md guardada → {path}")
            time.sleep(0.5)  # Pequeña pausa entre llamadas

    if not scenes:
        print("❌ No hay escenas para validar. Abortando.")
        return

    # 3. Bucle de validación y corrección
    print(f"\n{'═'*60}")
    print(f"   🔬  AGENTE EDITOR — VALIDANDO COHERENCIA (umbral: {threshold}%)")
    print(f"{'═'*60}\n")

    final_report = None
    for iteration in range(1, MAX_FIX_ITERATIONS + 1):
        print(f"  Iteración {iteration}/{MAX_FIX_ITERATIONS}...")

        report = validate_and_correct(scenes, characters_desc, paragraphs, threshold)
        final_report = report

        score   = report.get("overall_score", 0)
        passed  = report.get("passed", False)
        issues  = report.get("issues", [])
        fixes   = report.get("corrections_needed", [])

        report_path = save_report(report, iteration, output)
        print(f"   📊 Puntuación: {score}% | Problemas: {len(issues)} | Correcciones: {len(fixes)}")
        print(f"   📄 Reporte guardado: {report_path}")

        if passed:
            print(f"\n   ✅ COHERENCIA APROBADA ({score}% ≥ {threshold}%)")
            break

        if fixes and iteration < MAX_FIX_ITERATIONS:
            print(f"\n   ⚙️  Aplicando correcciones automáticas...")
            scenes = apply_corrections(scenes, fixes)
            # Re-guardar escenas corregidas
            for n, text in scenes.items():
                save_scene(text, n, output)
            print()
        elif iteration == MAX_FIX_ITERATIONS:
            print(
                f"\n   ⚠️  Se alcanzó el máximo de iteraciones. "
                f"Puntuación final: {score}%. Revisión manual recomendada."
            )

    # 4. Resumen final
    summary_path = save_summary(scenes, final_report or {}, output)

    print(f"\n{'═'*60}")
    print(f"   🏁  PROCESO COMPLETADO")
    print(f"{'═'*60}")
    print(f"\n   📁 Archivos generados en: {output.resolve()}")
    for n in sorted(scenes.keys()):
        print(f"      • escena{n}.md")
    print(f"      • RESUMEN_FINAL.md")
    print(f"      • coherence_report_v*.json\n")


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generador de prompts de escenas animadas para IA de video"
    )
    parser.add_argument(
        "--story",
        default="historia.md",
        help="Ruta al archivo historia.md (default: historia.md)",
    )
    parser.add_argument(
        "--characters",
        default="characters.json",
        help="Ruta al JSON de personajes (default: characters.json)",
    )
    parser.add_argument(
        "--output",
        default=".",
        help="Directorio de salida (default: directorio actual)",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=COHERENCE_THRESHOLD,
        help=f"Porcentaje mínimo de coherencia (default: {COHERENCE_THRESHOLD})",
    )
    parser.add_argument(
        "--only-validate",
        action="store_true",
        help="Solo valida escenas existentes sin regenerarlas",
    )

    args = parser.parse_args()

    run_pipeline(
        story_path=args.story,
        characters_path=args.characters,
        output_dir=args.output,
        threshold=args.threshold,
        only_validate=args.only_validate,
    )


if __name__ == "__main__":
    main()
