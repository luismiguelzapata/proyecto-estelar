"""
Configuración centralizada del proyecto Estelar
Define rutas, constantes y configuración global
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# Cargar variables del archivo .env
# Buscar .env en codebase/ (directorio actual del config)
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# ========================================
# RUTAS BASE
# ========================================

# Directorio del script
SCRIPT_DIR = Path(__file__).parent.parent
PROJECT_ROOT = SCRIPT_DIR.parent

# Directorios principales
CODEBASE_DIR = SCRIPT_DIR
CONFIG_DIR = CODEBASE_DIR / "config"
MODULES_DIR = CODEBASE_DIR / "modules"
COMPONENTES_DIR = CODEBASE_DIR / "componentes"
ASSETS_DIR = PROJECT_ROOT / "assets"
ASSETS_PERSONAJES_DIR = ASSETS_DIR / "personajes"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
OUTPUTS_HISTORIAS_DIR = OUTPUTS_DIR / "historias" / "revision"

# Archivos de datos y configuración
JSON_INPUT_FILE = CODEBASE_DIR / "inputs.opt2.json"
HISTORY_TELLER_FILE = COMPONENTES_DIR / "history-teller.md"
PROMPT_TEMPLATE_FILE = COMPONENTES_DIR / "prompt_template.md"

# ========================================
# CONFIGURACIÓN DE APIs
# ========================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")  # Para Gemini

# Modelos
OPENAI_MODEL = "gpt-4"
GEMINI_MODEL = "gemini-2.5-flash-image"  # Gemini Flash 2.0/2.5

# Parámetros de generación
OPENAI_TEMPERATURE = 0.9
OPENAI_MAX_TOKENS = 1500

GEMINI_MAX_TOKENS = 1024
GEMINI_TEMPERATURE = 0.7

# ========================================
# VALIDACIÓN DE ELEMENTOS REQUERIDOS
# ========================================

ELEMENTOS_REQUERIDOS_JSON = [
    'sentimientos',
    'moralejas',
    'objetosCotidianos',
    'objetosMagicos',
    'colores',
    'lugares',
    'personajesSecundarios',
    'fenomenosNaturales',
    'desafios',
    'accionesClaves'
]

# ========================================
# FORMATOS Y CONSTANTES
# ========================================

TIMESTAMP_FORMAT = "%Y%m%d-%H%M%S"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

# Caracteres válidos para nombres de archivo
VALID_FILENAME_CHARS = r'[^a-záéíóúñA-ZÁÉÍÓÚÑ0-9]'

# ========================================
# CONFIGURACIÓN DE GENERACIÓN DE IMÁGENES
# ========================================

# Directorios para imágenes por personaje
def get_personaje_dir(nombre_personaje: str) -> Path:
    """Obtiene o crea el directorio para un personaje específico"""
    # Normalizar nombre
    nombre_normalizado = nombre_personaje.lower().replace(" ", "-")
    personaje_dir = ASSETS_PERSONAJES_DIR / nombre_normalizado
    personaje_dir.mkdir(parents=True, exist_ok=True)
    return personaje_dir


def get_personaje_image_path(nombre_personaje: str) -> Path:
    """Obtiene la ruta completa para guardar la imagen de un personaje"""
    nombre_normalizado = nombre_personaje.lower().replace(" ", "-")
    return get_personaje_dir(nombre_personaje) / f"{nombre_normalizado}.jpg"


# ========================================
# CONFIGURACIÓN DE PROMPTS
# ========================================

# Instrucciones especiales para generar imágenes de personajes
PROMPT_3D_SYSTEM = """Eres un especialista en crear descripciones detalladas para generar imágenes 3D 
de personajes animados usando Midjourney, DALL-E o herramientas similares.
Proporcionas especificaciones precisas con códigos hex de colores, proporciones exactas y características visuales."""

# ========================================
# CREAR DIRECTORIOS SI NO EXISTEN
# ========================================

def ensure_directories_exist():
    """Crea todos los directorios necesarios si no existen"""
    dirs = [
        CODEBASE_DIR,
        CONFIG_DIR,
        MODULES_DIR,
        COMPONENTES_DIR,
        ASSETS_DIR,
        ASSETS_PERSONAJES_DIR,
        OUTPUTS_DIR,
        OUTPUTS_HISTORIAS_DIR
    ]
    
    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)


# Ejecutar al importar
ensure_directories_exist()
