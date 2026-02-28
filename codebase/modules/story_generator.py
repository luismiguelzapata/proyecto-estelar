"""
STORY_GENERATOR.PY - Generador de historias con OpenAI

Genera historias infantiles usando GPT-4o.
Registra cada llamada en el TokenTracker para control de consumo.
"""

import random
from typing import Dict, Any
from openai import OpenAI

from config.config import (
    OPENAI_MODEL,
    OPENAI_TEMPERATURE,
    OPENAI_MAX_TOKENS,
    HISTORY_TELLER_FILE,
    PROMPT_TEMPLATE_FILE,
    LOGS_DIR,
)
from .data_loader import cargar_datos_historias, cargar_prompts
from .utils import obtener_nombre_personaje
from .token_tracker import tracker

# ── Estado global del módulo ─────────────────────────────────────────────────

_client:          OpenAI | None = None
DATOS_HISTORIAS:  dict  | None  = None
SYSTEM_PROMPT:    str   | None  = None
PROMPT_TEMPLATE:  str   | None  = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI()
    return _client


def inicializar_generador():
    """
    Inicializa el generador: carga JSON + prompts + configura el token tracker.
    Debe llamarse UNA vez antes de generar historias.
    """
    global DATOS_HISTORIAS, SYSTEM_PROMPT, PROMPT_TEMPLATE

    # Configurar tracker con directorio de logs
    tracker.set_log_path(LOGS_DIR)

    DATOS_HISTORIAS = cargar_datos_historias()
    SYSTEM_PROMPT, PROMPT_TEMPLATE = cargar_prompts(
        HISTORY_TELLER_FILE,
        PROMPT_TEMPLATE_FILE,
    )
    print("✅ Generador de historias listo\n")


def generar_elementos_historia() -> Dict[str, Any]:
    """
    Selecciona una combinación aleatoria de elementos del JSON.

    Returns:
        dict con todos los elementos seleccionados

    Raises:
        RuntimeError: si el generador no fue inicializado
    """
    if DATOS_HISTORIAS is None:
        raise RuntimeError("❌ Llama primero a inicializar_generador()")

    personaje_secundario = random.choice(DATOS_HISTORIAS["personajesSecundarios"])
    personaje_nombre     = obtener_nombre_personaje(personaje_secundario)

    return {
        "lugar":                    random.choice(DATOS_HISTORIAS["lugares"]),
        "objeto_principal":         random.choice(DATOS_HISTORIAS["objetosCotidianos"]),
        "color_objeto":             random.choice(DATOS_HISTORIAS["colores"]),
        "objeto_magico":            random.choice(DATOS_HISTORIAS["objetosMagicos"]),
        "personaje_secundario":     personaje_secundario,   # dict completo
        "personaje_secundario_nombre": personaje_nombre,   # solo nombre para el template
        "sentimiento_kira":         random.choice(DATOS_HISTORIAS["sentimientos"]),
        "sentimiento_toby":         random.choice(DATOS_HISTORIAS["sentimientos"]),
        "fenomeno":                 random.choice(DATOS_HISTORIAS["fenomenosNaturales"]),
        "desafio":                  random.choice(DATOS_HISTORIAS["desafios"]),
        "accion_kira":              random.choice(DATOS_HISTORIAS["accionesClaves"]),
        "accion_toby":              random.choice(DATOS_HISTORIAS["accionesClaves"]),
        "moraleja":                 random.choice(DATOS_HISTORIAS["moralejas"]),
    }


def generar_historia_aleatoria() -> Dict[str, Any]:
    """
    Genera una historia completa con GPT-4o usando elementos aleatorios.

    Returns:
        dict con:
          - historia (str): texto completo
          - elementos (dict): elementos usados
          - tokens (dict): desglose de tokens consumidos
          - costo_estimado_usd (float): costo estimado de la llamada

    Raises:
        RuntimeError: si el generador no fue inicializado
    """
    if PROMPT_TEMPLATE is None or SYSTEM_PROMPT is None:
        raise RuntimeError("❌ Llama primero a inicializar_generador()")

    elementos = generar_elementos_historia()

    # Mostrar elementos seleccionados
    print("🎲 ELEMENTOS SELECCIONADOS:")
    print("─" * 50)
    for k, v in elementos.items():
        if k == "personaje_secundario" and isinstance(v, dict):
            print(f"  {k}: {v.get('nombre', '?')}")
        else:
            print(f"  {k}: {v}")
    print("─" * 50)
    print(f"\n⏳ Generando historia con {OPENAI_MODEL}...\n")

    try:
        openai_client = _get_client()
        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": PROMPT_TEMPLATE.format(**elementos)},
            ],
            temperature=OPENAI_TEMPERATURE,
            max_tokens=OPENAI_MAX_TOKENS,
        )

        historia = response.choices[0].message.content
        uso      = response.usage

        # ── Registrar tokens ──────────────────────────────────────────────
        entry = tracker.register_openai(
            operation="generar_historia",
            model=OPENAI_MODEL,
            prompt_tokens=uso.prompt_tokens,
            completion_tokens=uso.completion_tokens,
            total_tokens=uso.total_tokens,
            metadata={
                "personaje": elementos["personaje_secundario_nombre"],
                "lugar":     elementos["lugar"],
                "moraleja":  elementos["moraleja"],
            },
        )
        tracker.print_entry(entry)
        # ─────────────────────────────────────────────────────────────────

        return {
            "historia": historia,
            "elementos": elementos,
            "tokens": {
                "prompt":     uso.prompt_tokens,
                "completion": uso.completion_tokens,
                "total":      uso.total_tokens,
            },
            "costo_estimado_usd": entry["estimated_cost_usd"],
        }

    except Exception as e:
        return {
            "error":    str(e),
            "elementos": elementos,
        }
