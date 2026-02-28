"""
Módulo generador de historias
Maneja la generación de historias usando OpenAI
"""

import random
from typing import Dict, Any
from openai import OpenAI

from config.config import (
    OPENAI_MODEL,
    OPENAI_TEMPERATURE,
    OPENAI_MAX_TOKENS,
    HISTORY_TELLER_FILE,
    PROMPT_TEMPLATE_FILE
)
from .data_loader import cargar_datos_historias, cargar_prompts
from .utils import obtener_nombre_personaje

# Cliente OpenAI (se inicializa cuando sea necesario)
client = None

# Cargar datos globales
DATOS_HISTORIAS = None
SYSTEM_PROMPT = None
PROMPT_TEMPLATE = None


def _get_client():
    """Obtiene o inicializa el cliente OpenAI"""
    global client
    if client is None:
        client = OpenAI()
    return client


def inicializar_generador():
    """
    Inicializa el generador cargando los datos necesarios.
    Debe llamarse antes de generar historias.
    """
    global DATOS_HISTORIAS, SYSTEM_PROMPT, PROMPT_TEMPLATE
    
    try:
        DATOS_HISTORIAS = cargar_datos_historias()
        SYSTEM_PROMPT, PROMPT_TEMPLATE = cargar_prompts(
            HISTORY_TELLER_FILE,
            PROMPT_TEMPLATE_FILE
        )
        print("✅ Generador de historias inicializado correctamente\n")
    except Exception as e:
        print(f"❌ Error al inicializar generador: {str(e)}")
        raise


def generar_elementos_historia() -> Dict[str, Any]:
    """
    Genera una combinación aleatoria de elementos para una historia.
    Ahora maneja personajesSecundarios como dict con características.
    
    Returns:
        dict: Diccionario con elementos seleccionados
        
    Raises:
        RuntimeError: Si el generador no ha sido inicializado
    """
    
    if DATOS_HISTORIAS is None:
        raise RuntimeError("❌ Generador no inicializado. Llama a inicializar_generador()")
    
    personaje_secundario = random.choice(DATOS_HISTORIAS['personajesSecundarios'])
    personaje_nombre = obtener_nombre_personaje(personaje_secundario)
    
    elementos = {
        "lugar": random.choice(DATOS_HISTORIAS['lugares']),
        "objeto_principal": random.choice(DATOS_HISTORIAS['objetosCotidianos']),
        "color_objeto": random.choice(DATOS_HISTORIAS['colores']),
        "objeto_magico": random.choice(DATOS_HISTORIAS['objetosMagicos']),
        "personaje_secundario": personaje_secundario,  # Dict completo con características
        "personaje_secundario_nombre": personaje_nombre,  # Solo el nombre para template
        "sentimiento_kira": random.choice(DATOS_HISTORIAS['sentimientos']),
        "sentimiento_toby": random.choice(DATOS_HISTORIAS['sentimientos']),
        "fenomeno": random.choice(DATOS_HISTORIAS['fenomenosNaturales']),
        "desafio": random.choice(DATOS_HISTORIAS['desafios']),
        "accion_kira": random.choice(DATOS_HISTORIAS['accionesClaves']),
        "accion_toby": random.choice(DATOS_HISTORIAS['accionesClaves']),
        "moraleja": random.choice(DATOS_HISTORIAS['moralejas'])
    }
    
    return elementos


def generar_historia_aleatoria() -> Dict[str, Any]:
    """
    Genera una historia completamente aleatoria combinando elementos del JSON.
    
    Returns:
        dict: Historia generada + elementos usados + tokens utilizados
        
    Raises:
        RuntimeError: Si el generador no ha sido inicializado
    """
    
    if PROMPT_TEMPLATE is None or SYSTEM_PROMPT is None:
        raise RuntimeError("❌ Generador no inicializado. Llama a inicializar_generador()")
    
    # Generar elementos aleatorios
    elementos = generar_elementos_historia()
    
    # Mostrar elementos seleccionados
    print("🎲 ELEMENTOS SELECCIONADOS:")
    print("=" * 60)
    for key, value in elementos.items():
        if key == "personaje_secundario" and isinstance(value, dict):
            print(f"  {key}: {value.get('nombre', 'desconocido')}")
        else:
            print(f"  {key}: {value}")
    print("=" * 60)
    print("\n⏳ Generando historia con GPT-4...\n")
    
    try:
        openai_client = _get_client()
        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": PROMPT_TEMPLATE.format(**elementos)}
            ],
            temperature=OPENAI_TEMPERATURE,
            max_tokens=OPENAI_MAX_TOKENS
        )
        
        historia = response.choices[0].message.content
        
        return {
            "historia": historia,
            "elementos": elementos,
            "tokens": response.usage.total_tokens
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "elementos": elementos
        }


# def generar_multiples_historias(cantidad: int = 5) -> list:
#     """
#     Genera múltiples historias aleatorias.
    
#     Args:
#         cantidad (int): Número de historias a generar (1-10)
        
#     Returns:
#         list: Lista de historias generadas
#     """
    
#     if cantidad < 1 or cantidad > 10:
#         raise ValueError("❌ La cantidad debe estar entre 1 y 10")
    
#     historias = []
    
#     for i in range(1, cantidad + 1):
#         print(f"\n{'='*60}")
#         print(f"📖 GENERANDO HISTORIA {i}/{cantidad}")
#         print(f"{'='*60}\n")
        
#         resultado = generar_historia_aleatoria()
#         historias.append(resultado)
        
#         if "historia" in resultado:
#             print("\n" + resultado["historia"])
#             print(f"\n📊 Tokens usados: {resultado['tokens']}")
#         else:
#             print(f"\n❌ Error: {resultado['error']}")
        
#         print("\n" + "="*60)
    
#     return historias
