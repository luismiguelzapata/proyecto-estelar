"""
CONFIG.PY - Configuración centralizada del proyecto Estelar

Define rutas, constantes y configuración global.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# ── Rutas base ────────────────────────────────────────────────────────────────

SCRIPT_DIR   = Path(__file__).parent.parent   # codebase/
PROJECT_ROOT = SCRIPT_DIR.parent              # proyecto-estelar/

# Cargar .env desde codebase/
env_path = SCRIPT_DIR / ".env"
load_dotenv(dotenv_path=env_path)

# ── Directorios del proyecto ──────────────────────────────────────────────────

CODEBASE_DIR          = SCRIPT_DIR
CONFIG_DIR            = CODEBASE_DIR / "config"
MODULES_DIR           = CODEBASE_DIR / "modules"
COMPONENTES_DIR       = CODEBASE_DIR / "componentes"

ASSETS_DIR            = PROJECT_ROOT / "assets"
ASSETS_PERSONAJES_DIR = ASSETS_DIR / "personajes"

OUTPUTS_DIR           = PROJECT_ROOT / "outputs"
OUTPUTS_HISTORIAS_DIR = OUTPUTS_DIR / "historias" / "revision"

LOGS_DIR              = PROJECT_ROOT / "logs"

# ── Archivos de datos ─────────────────────────────────────────────────────────

JSON_INPUT_FILE      = CODEBASE_DIR / "inputs.opt2.json"
JSON_INPUT_FILE_2D   = CODEBASE_DIR / "inputs.opt2-2D.json"
JSON_INPUT_FILE_3D   = CODEBASE_DIR / "inputs.opt2-3D.json"
HISTORY_TELLER_FILE  = COMPONENTES_DIR / "history-teller.md"
PROMPT_TEMPLATE_FILE = COMPONENTES_DIR / "prompt_template.md"

# ── APIs ──────────────────────────────────────────────────────────────────────

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
RUNWAY_API_KEY = os.getenv("kayroscreativeApiKey")

# Modelos
OPENAI_MODEL  = "gpt-4o"                          # Más barato y rápido que gpt-4
GEMINI_MODEL  = "gen4_image"
IMAGE_MODEL   = "gen4_image"

# Parámetros de generación de texto
OPENAI_TEMPERATURE = 0.9
OPENAI_MAX_TOKENS  = 1500

# ── Elementos requeridos en el JSON ──────────────────────────────────────────

ELEMENTOS_REQUERIDOS_JSON = [
    'sentimientos', 'moralejas', 'objetosCotidianos',
    'objetosMagicos', 'colores', 'lugares',
    'personajesSecundarios', 'fenomenosNaturales',
    'desafios', 'accionesClaves',
]

# ── Formatos ──────────────────────────────────────────────────────────────────

TIMESTAMP_FORMAT = "%Y%m%d-%H%M%S"
DATETIME_FORMAT  = "%Y-%m-%d %H:%M:%S"

# ── Helpers de rutas para personajes ─────────────────────────────────────────

def get_personaje_dir(nombre_personaje: str) -> Path:
    """Obtiene (y crea si no existe) el directorio para un personaje."""
    nombre = nombre_personaje.lower().replace(" ", "-")
    path   = ASSETS_PERSONAJES_DIR / nombre
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_personaje_image_path(nombre_personaje: str) -> Path:
    """Ruta completa de la imagen de un personaje."""
    nombre = nombre_personaje.lower().replace(" ", "-")
    return get_personaje_dir(nombre_personaje) / f"{nombre}.jpg"


# ── Crear directorios al importar ────────────────────────────────────────────

def ensure_directories_exist():
    for d in [
        CODEBASE_DIR, CONFIG_DIR, MODULES_DIR, COMPONENTES_DIR,
        ASSETS_DIR, ASSETS_PERSONAJES_DIR,
        OUTPUTS_DIR, OUTPUTS_HISTORIAS_DIR,
        LOGS_DIR,
    ]:
        d.mkdir(parents=True, exist_ok=True)


ensure_directories_exist()
