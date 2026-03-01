"""
MAIN.PY - Punto de entrada principal del proyecto Estelar

Orquesta la generación de historias, escenas e imágenes.

ESTRUCTURA DE SALIDA:
    outputs/historias/revision/[TITULO]/
    ├── [TITULO]-TIMESTAMP.txt                 ← historia completa
    ├── escenas/                               ← prompts de video para IA
    │   ├── escena1.md … escenaN.md
    │   ├── RESUMEN_FINAL.md
    │   └── coherence_report_v*.json
    └── ilustraciones/
        └── prompts-ilustraciones/             ← prompts para imagen estática
            ├── ilustracion1.md … ilustracionN.md
            └── ilustracion_N.png  (solo con --con-imagenes)

USO:
    # Flujo normal (historia nueva + escenas de video automáticamente):
    python main.py
    python main.py --modo historia

    # Flujo completo (historia + escenas video + ilustraciones + imágenes personaje):
    python main.py --modo completo

    # Procesar una historia ya guardada:
    python main.py --modo escenas     --historia "outputs/.../TITULO-xxx.txt"
    python main.py --modo ilustracion --historia "outputs/.../TITULO-xxx.txt"
    python main.py --modo ilustracion --historia "outputs/.../TITULO-xxx.txt" --con-imagenes

    # Solo imágenes de personajes del JSON:
    python main.py --modo imagen
    python main.py --modo imagen --placeholder   # sin consumir API

    # Control de tokens:
    python main.py --tokens
"""

import argparse
import json
import sys
from pathlib import Path

from modules import (
    cargar_datos_historias,
    generar_historia_aleatoria,
    guardar_historia,
    generar_imagen_personaje,
    generar_imagenes_escena,
    inicializar_generador,
    crear_imagen_placeholder,
    tracker,
)
from modules.scene_generator import (
    generar_escenas_desde_historia,
    generar_ilustraciones_desde_historia,
    COHERENCE_THRESHOLD,
)
from config.config import ASSETS_PERSONAJES_DIR, LOGS_DIR


# ═════════════════════════════════════════════════════════════════════════════
# CLI
# ═════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="🐶 Generador de Historias Animadas — Kira y Toby",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  Flujo completo (historia + escenas video + ilustraciones + imágenes personaje):
    python main.py --modo completo

  Solo historia nueva (incluye escenas de video automáticamente):
    python main.py

  Escenas de VIDEO para una historia ya guardada:
    python main.py --modo escenas --historia "outputs/historias/revision/TITULO/TITULO-xxx.txt"
    python main.py --modo escenas --historia "ruta.txt" --characters "characters.json" --threshold 90
    python main.py --modo escenas --historia "ruta.txt" --solo-validar

  Ilustraciones de cuento (.md + PNG automático con Google Imagen):
    python main.py --modo ilustracion --historia "outputs/historias/revision/TITULO/TITULO-xxx.txt"

  Solo imágenes de personajes del JSON:
    python main.py --modo imagen
    python main.py --modo imagen --placeholder   # sin API (testing)

  Ver historial de consumo de tokens:
    python main.py --tokens

Estructura de salida:
  outputs/historias/revision/[TITULO]/
  ├── [TITULO]-TIMESTAMP.txt
  ├── escenas/                              ← prompts de video
  └── ilustraciones/
      └── prompts-ilustraciones/            ← prompts de imagen estática
        """,
    )

    parser.add_argument(
        "--modo",
        choices=["historia", "imagen", "completo", "escenas", "ilustracion"],
        default="historia",
        help=(
            "historia:    genera historia nueva (incluye escenas automáticamente)\n"
            "escenas:     genera/re-genera escenas de video de una historia ya guardada\n"
            "ilustracion: genera prompts de ilustración de cuento (sin cámara, ENVIRONMENT rico)\n"
            "imagen:      genera imágenes de personajes secundarios\n"
            "completo:    historia + imágenes del personaje"
        ),
    )
    parser.add_argument(
        "--historia",
        type=str,
        default=None,
        metavar="RUTA",
        help="[modo escenas / ilustracion] Ruta al .txt de la historia ya guardada. "
             "Ejemplo: outputs/historias/revision/Mi_Historia/Mi_Historia-20260228.txt",
    )
    parser.add_argument(
        "--characters",
        type=str,
        default=None,
        metavar="RUTA",
        help="[modo escenas] Ruta al characters.json. "
             "Si no se especifica, usa los personajes del proyecto (inputs.opt2.json).",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=COHERENCE_THRESHOLD,
        metavar="N",
        help=f"[modo escenas] Umbral mínimo de coherencia en %% (default: {COHERENCE_THRESHOLD})",
    )
    parser.add_argument(
        "--solo-validar",
        action="store_true",
        help="[modo escenas] Solo valida escenas existentes sin regenerarlas",
    )
    parser.add_argument(
        "--placeholder",
        action="store_true",
        help="[modo imagen] Crear imágenes placeholder para testing (sin API)",
    )
    parser.add_argument(
        "--tokens",
        action="store_true",
        help="Mostrar historial acumulado de tokens y salir",
    )

    args = parser.parse_args()

    # ── Historial de tokens ────────────────────────────────────────────────
    if args.tokens:
        mostrar_historial_tokens()
        return

    # ── Header ────────────────────────────────────────────────────────────
    print("=" * 70)
    print("🐶 GENERADOR DE HISTORIAS ANIMADAS — KIRA Y TOBY")
    print("=" * 70)
    print()

    try:
        # El modo escenas no necesita inicializar el generador de historias
        if args.modo != "escenas":
            print("📚 Inicializando...\n")
            inicializar_generador()

        if args.modo == "historia":
            ejecutar_historia_unica()

        elif args.modo == "escenas":
            ejecutar_escenas_historia_existente(
                historia_path=args.historia,
                characters_path=args.characters,
                threshold=args.threshold,
                solo_validar=args.solo_validar,
            )

        elif args.modo == "ilustracion":
            ejecutar_ilustraciones_historia_existente(
                historia_path=args.historia,
                characters_path=args.characters,
            )

        elif args.modo == "imagen":
            ejecutar_generador_imagenes(args.placeholder)

        elif args.modo == "completo":
            ejecutar_modo_completo()

        # ── Resumen de tokens de la sesión ─────────────────────────────
        tracker.print_summary("SESIÓN ACTUAL")

        print("✅ Proceso completado exitosamente")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise


# ═════════════════════════════════════════════════════════════════════════════
# MODO ESCENAS — el nuevo modo principal de este flujo
# ═════════════════════════════════════════════════════════════════════════════

def ejecutar_escenas_historia_existente(
    historia_path: str | None,
    characters_path: str | None,
    threshold: int,
    solo_validar: bool,
):
    """
    Genera (o re-genera) los prompts de escenas de una historia ya guardada.

    El .txt de la historia puede estar:
      - En outputs/historias/revision/TITULO/TITULO-timestamp.txt  (ruta relativa o absoluta)
      - En cualquier otra ubicación accesible

    Los escenaN.md se guardan en: misma_carpeta_del_txt/escenas/
    """

    # ── 1. Resolver ruta de la historia ───────────────────────────────────
    if not historia_path:
        print("\n❌ Debes indicar la ruta a la historia con --historia")
        print("   Ejemplo:")
        print('   python main.py --modo escenas --historia "outputs/historias/revision/Mi_Historia/Mi_Historia-20260228.txt"')
        sys.exit(1)

    historia_file = _resolver_historia_path(historia_path)
    print(f"📄 Historia:   {historia_file.resolve()}")

    # ── 2. Resolver characters.json ───────────────────────────────────────
    characters_data = _resolver_characters(characters_path, historia_file)

    # ── 3. Definir carpeta de salida (escenas/ junto al .txt) ─────────────
    output_dir = historia_file.parent / "escenas"

    print(f"📁 Salida:     {output_dir.resolve()}")
    print(f"🎯 Umbral:     {threshold}%")
    if solo_validar:
        print("🔍 Modo:       solo validar escenas existentes\n")
    else:
        print("🖊️  Modo:       generar escenas nuevas\n")

    # ── 4. Lanzar el pipeline ──────────────────────────────────────────────
    tracker.set_log_path(LOGS_DIR)

    story_text = historia_file.read_text(encoding="utf-8")
    titulo     = historia_file.parent.name   # el nombre de la carpeta es el título

    resultado = generar_escenas_desde_historia(
        story_text=story_text,
        characters_data=characters_data,
        output_dir=output_dir,
        threshold=threshold,
        only_validate=solo_validar,
        historia_titulo=titulo,
    )

    # ── 5. Resumen final ───────────────────────────────────────────────────
    score  = resultado.get("coherence_score", 0)
    passed = resultado.get("passed", False)
    n_esc  = resultado.get("scenes_count", 0)

    print(f"\n{'─'*70}")
    print(f"  🎬 ESCENAS GENERADAS: {n_esc}")
    print(f"  📊 Coherencia:        {score}%  {'✅ APROBADO' if passed else '⚠️  REQUIERE REVISIÓN'}")
    print(f"  📁 Ubicación:         {output_dir.resolve()}")
    print(f"{'─'*70}\n")

    return resultado


# ═════════════════════════════════════════════════════════════════════════════
# MODO ILUSTRACIÓN
# ═════════════════════════════════════════════════════════════════════════════

def ejecutar_ilustraciones_historia_existente(
    historia_path: str | None,
    characters_path: str | None,
):
    """
    Genera prompts de ilustración de cuento (ilustracionN.md) para una
    historia ya guardada en disco.

    Los archivos se guardan en: misma_carpeta_del_txt/prompts-scenas/

    Diferencia con --modo escenas:
      - Prompts optimizados para imagen estática (sin ACTION, sin CAMERA)
      - ENVIRONMENT mucho más detallado (texturas, paleta HEX, profundidad)
      - Archivos: ilustracionN.md (no escenaN.md)
      - Sin agente editor de coherencia

    Si con_imagenes=True (flag --con-imagenes):
      - Además de los .md, llama a Google Imagen para generar los PNG

    USO:
      python main.py --modo ilustracion --historia "ruta/al/archivo.txt"
      python main.py --modo ilustracion --historia "ruta.txt" --characters "characters.json"
      python main.py --modo ilustracion --historia "ruta.txt" --con-imagenes
    """
    if not historia_path:
        print("\n❌ Debes indicar la ruta a la historia con --historia")
        print("   Ejemplo:")
        print('   python main.py --modo ilustracion --historia "outputs/historias/revision/TITULO/TITULO-xxx.txt"')
        sys.exit(1)

    historia_file = _resolver_historia_path(historia_path)
    print(f"📄 Historia:   {historia_file.resolve()}")

    characters_data = _resolver_characters(characters_path, historia_file)
    output_dir      = historia_file.parent / "ilustraciones" / "prompts-ilustraciones"
    titulo          = historia_file.parent.name

    print(f"📁 Salida:     {output_dir.resolve()}")
    print(f"🖼️  Modo:       ilustración de cuento (.md + PNG automático)\n")

    tracker.set_log_path(LOGS_DIR)
    story_text = historia_file.read_text(encoding="utf-8")

    # Pipeline integrado: genera ilustracionN.md (slim) + ilustracionN.png por cada párrafo
    resultado = generar_ilustraciones_desde_historia(
        story_text=story_text,
        characters_data=characters_data,
        output_dir=output_dir,
        historia_titulo=titulo,
    )

    n_ilus = resultado.get("scenes_count", 0)
    print(f"\n{'─'*70}")
    print(f"  🖼️  ILUSTRACIONES GENERADAS: {n_ilus}  (.md + PNG por cada una)")
    print(f"  📁 Ubicación: {output_dir.resolve()}")
    print(f"{'─'*70}\n")
    return resultado


def _resolver_historia_path(historia_path: str) -> Path:
    """
    Convierte una ruta (relativa o absoluta) al Path real del .txt de historia.
    Prueba en este orden: ruta absoluta, desde cwd, desde project_root, desde codebase/.
    Termina el proceso con error si no se encuentra.
    """
    historia_file = Path(historia_path)
    if not historia_file.is_absolute():
        candidatos = [
            Path.cwd() / historia_file,
            Path(__file__).parent.parent / historia_file,
            Path(__file__).parent / historia_file,
        ]
        for c in candidatos:
            if c.exists():
                return c

    if not historia_file.exists():
        print(f"\n❌ No se encontró el archivo: {historia_path}")
        print("   Verifica la ruta e inténtalo de nuevo.")
        sys.exit(1)

    return historia_file


def _resolver_characters(characters_path: str | None, historia_file: Path) -> dict:
    """
    Resuelve el dict de personajes en este orden de prioridad:

    1. --characters especificado por el usuario
    2. characters.json en la misma carpeta que el .txt
    3. characters.json en codebase/
    4. inputs.opt2.json del proyecto (extrae solo el personaje secundario relevante)
    5. Fallback mínimo con Kira y Toby
    """
    from config.config import JSON_INPUT_FILE

    # Opción 1: ruta explícita
    if characters_path:
        p = Path(characters_path)
        if not p.is_absolute():
            p = Path.cwd() / p
        if p.exists():
            print(f"👥 Personajes:  {p.resolve()}  (--characters)")
            with open(p, encoding="utf-8") as f:
                return json.load(f)
        print(f"⚠️  No se encontró {characters_path} — buscando alternativas...")

    # Opción 2: characters.json junto al .txt
    junto = historia_file.parent / "characters.json"
    if junto.exists():
        print(f"👥 Personajes:  {junto.resolve()}  (junto al .txt)")
        with open(junto, encoding="utf-8") as f:
            return json.load(f)

    # Opción 3: characters.json en codebase/
    codebase = Path(__file__).parent / "characters.json"
    if codebase.exists():
        print(f"👥 Personajes:  {codebase.resolve()}  (codebase/characters.json)")
        with open(codebase, encoding="utf-8") as f:
            return json.load(f)

    # Opción 4: extraer de inputs.opt2.json
    if JSON_INPUT_FILE.exists():
        print(f"👥 Personajes:  {JSON_INPUT_FILE.name}  (inputs.opt2.json del proyecto)")
        with open(JSON_INPUT_FILE, encoding="utf-8") as f:
            datos = json.load(f)
        secundarios = datos.get("construccionHistorias", {}).get("personajesSecundarios", [])
        # Filtrar solo los que tienen prompt-3D (los enriquecidos)
        secundarios_enriquecidos = [p for p in secundarios if isinstance(p, dict) and "prompt-3D" in p]
        return {
            "personajesPrincipales": _kira_y_toby_default(),
            "personajesSecundarios": secundarios_enriquecidos[:10],  # máx 10 para no saturar el prompt
        }

    # Opción 5: fallback mínimo
    print("👥 Personajes:  fallback mínimo (Kira y Toby)")
    return {"personajesPrincipales": _kira_y_toby_default(), "personajesSecundarios": []}


def _kira_y_toby_default() -> list:
    """Descripción base de los protagonistas cuando no hay characters.json."""
    return [
        {
            "nombre": "Kira",
            "species": "perro (Shiba Inu inspired)",
            "fur_color": "#FFF9D4",
            "eye_color": "#5C4033",
            "accessory": "heart-shaped spot on RIGHT cheek only, peach-orange #FFB380",
            "forbidden_changes": "no cambiar color amarillo pastel, no quitar marca de corazón en mejilla derecha",
        },
        {
            "nombre": "Toby",
            "species": "perro (Husky inspired)",
            "fur_color": "#E8E3F0",
            "eye_color": "HETEROCHROMIA: left #6BB6D6 blue, right #8B6F47 brown",
            "accessory": "lightning bolt on left flank #A8D8EA, neck mane #D4C9E0",
            "forbidden_changes": "no cambiar heterocromía, no quitar rayo del costado izquierdo",
        },
    ]


# ═════════════════════════════════════════════════════════════════════════════
# RESTO DE MODOS (sin cambios)
# ═════════════════════════════════════════════════════════════════════════════

def ejecutar_historia_unica() -> dict | None:
    """Genera y guarda una historia aleatoria (incluye escenas automáticamente)."""
    print("📖 Generando historia...\n")

    resultado = generar_historia_aleatoria()

    if "error" in resultado:
        print(f"\n❌ Error al generar historia: {resultado['error']}")
        return None

    print("\n" + "=" * 70)
    print(resultado["historia"])
    print("=" * 70)

    print("\n💾 Guardando historia y generando escenas...\n")
    guardado = guardar_historia(resultado)

    if guardado:
        print(f"\n🎉 Historia guardada exitosamente")
        print(f"   📂 {guardado['ruta_directorio']}")
        print(f"   📝 {guardado['ruta_historia']}")
        print(f"   🎬 Escenas: {guardado['ruta_escenas']}")
        return guardado

    return None


def ejecutar_generador_imagenes(usar_placeholder: bool = False):
    """Genera imágenes de todos los personajes secundarios del JSON."""
    print("🎨 Generador de Imágenes de Personajes\n")

    datos      = cargar_datos_historias()
    personajes = datos.get("personajesSecundarios", [])

    print(f"📊 Personajes en el JSON: {len(personajes)}\n")

    generadas = errores = 0

    for p in personajes:
        if not isinstance(p, dict):
            print(f"⚠️  {p} (formato antiguo — omitiendo)")
            continue

        nombre = p.get("nombre", "?")
        ok = crear_imagen_placeholder(nombre) if usar_placeholder else generar_imagen_personaje(p)

        if ok:
            generadas += 1
        else:
            errores += 1

    print(f"\n📊 Resultados:")
    print(f"   ✅ Generadas: {generadas}")
    print(f"   ❌ Errores:   {errores}")
    print(f"   📂 {ASSETS_PERSONAJES_DIR}")


def ejecutar_modo_completo():
    """
    Modo completo: historia + escenas de video + ilustraciones + imágenes del personaje.

    Pasos:
      1. Genera la historia y los prompts de escenas de video (escenas/)
      2. Genera los prompts de ilustración de cuento (ilustraciones/prompts-ilustraciones/)
      3. Genera las imágenes del personaje secundario en assets/personajes/
    """
    print("🚀 MODO COMPLETO: Historia + Escenas + Ilustraciones + Imágenes\n")

    # ── 1. Historia + Escenas de Video ────────────────────────────────────
    print("1️⃣  GENERANDO HISTORIA Y ESCENAS DE VIDEO...\n")
    guardado = ejecutar_historia_unica()

    if not guardado:
        print("❌ No se pudo generar la historia. Abortando.")
        return

    historia_file = Path(guardado["ruta_historia"])
    ruta_dir      = Path(guardado["ruta_directorio"])
    titulo        = guardado["titulo"]

    # ── 2. Prompts de Ilustración ─────────────────────────────────────────
    print("\n2️⃣  GENERANDO PROMPTS DE ILUSTRACIÓN DE CUENTO...\n")

    characters_data       = _resolver_characters(None, historia_file)
    story_text            = historia_file.read_text(encoding="utf-8")
    output_ilustraciones  = ruta_dir / "ilustraciones" / "prompts-ilustraciones"

    tracker.set_log_path(LOGS_DIR)
    resultado_ilus = generar_ilustraciones_desde_historia(
        story_text=story_text,
        characters_data=characters_data,
        output_dir=output_ilustraciones,
        historia_titulo=titulo,
    )

    # ── 3. Imágenes del Personaje Secundario ──────────────────────────────
    print("\n3️⃣  GENERANDO IMÁGENES DEL PERSONAJE SECUNDARIO...\n")

    historia_dict = {
        "historia":  guardado.get("historia", ""),
        "elementos": guardado.get("elementos", {}),
    }
    resultado_img = generar_imagenes_escena(historia_dict)

    # ── Resumen ───────────────────────────────────────────────────────────
    n_ilus = resultado_ilus.get("scenes_count", 0)
    print(f"\n{'═'*70}")
    print(f"  ✅ MODO COMPLETO FINALIZADO")
    print(f"{'═'*70}")
    print(f"  📝 Historia:          {guardado['ruta_historia']}")
    print(f"  🎬 Escenas video:     {guardado['ruta_escenas']}")
    print(f"  🖼️  Prompts ilus.:     {output_ilustraciones}  ({n_ilus} archivos)")
    if resultado_img:
        n_imgs = resultado_img.get("total_imagenes", 0)
        personaje = resultado_img.get("personaje", "N/A")
        print(f"  🎨 Personaje imag.:  {personaje}  ({n_imgs} imagen(es) → assets/personajes/)")
    else:
        print(f"  ⚠️  Sin imágenes de personaje (el personaje secundario no tiene prompt-3D en el JSON)")
    print(f"{'═'*70}\n")


# ═════════════════════════════════════════════════════════════════════════════
# HISTORIAL DE TOKENS
# ═════════════════════════════════════════════════════════════════════════════

def mostrar_historial_tokens():
    """Lee y muestra el historial acumulado de tokens desde el log JSON."""
    log_path = LOGS_DIR / "token_usage.json"

    if not log_path.exists():
        print("ℹ️  No hay historial de tokens aún. Genera algunas historias primero.")
        return

    with open(log_path, encoding="utf-8") as f:
        data = json.load(f)

    cumul    = data.get("cumulative", {})
    sessions = data.get("sessions", [])

    print("\n" + "═" * 60)
    print("  📊 HISTORIAL ACUMULADO DE TOKENS")
    print("═" * 60)
    print(f"  Total de sesiones:     {cumul.get('total_sessions', 0):>8}")
    print(f"  Total tokens:          {cumul.get('total_tokens', 0):>8,}")
    print(f"  Imágenes generadas:    {cumul.get('images_generated', 0):>8}")
    print(f"  Costo total estimado:  ${cumul.get('estimated_cost_usd', 0):>8.4f} USD")
    print("═" * 60)

    print(f"\n  Últimas {min(5, len(sessions))} sesiones:\n")
    for s in sessions[-5:]:
        t = s.get("totals", {})
        print(
            f"  • {s.get('session_start', '?')[:19]}  "
            f"{t.get('total_tokens', 0):>7,} tokens  "
            f"${t.get('estimated_cost_usd', 0):.4f} USD"
        )

    print(f"\n  📄 Log completo: {log_path}\n")


# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    main()