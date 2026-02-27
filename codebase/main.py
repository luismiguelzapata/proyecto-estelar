# codebase/main.py

from pathlib import Path
import json
from modules.story_storage import guardar_historia, generar_imagenes_escenas

# ==========================
# CONFIGURACIÓN DE RUTAS
# ==========================
HISTORIA_JSON = Path("inputs/historia.json")   # tu fichero de historia
OUTPUT_MARKDOWN = Path("outputs/historia_completa.md")

# Crear carpeta de salida si no existe
OUTPUT_MARKDOWN.parent.mkdir(parents=True, exist_ok=True)

# ==========================
# CARGAR HISTORIA
# ==========================
if not HISTORIA_JSON.exists():
    print(f"❌ No se encontró el fichero de historia: {HISTORIA_JSON}")
    exit(1)

with open(HISTORIA_JSON, "r", encoding="utf-8") as f:
    historia = json.load(f)

# ==========================
# GUARDAR HISTORIA EN MARKDOWN
# ==========================
print("📄 Guardando historia en Markdown...")
guardar_historia(historia, OUTPUT_MARKDOWN)
print(f"✅ Markdown generado en: {OUTPUT_MARKDOWN}")

# ==========================
# GENERAR IMÁGENES DE ESCENAS
# ==========================
print("🎨 Generando imágenes de las escenas...")
resultados_imagenes = generar_imagenes_escenas(historia, generar_tres_vistas=True)

for idx, res in enumerate(resultados_imagenes, start=1):
    if res:
        print(f"  ✅ Escena {idx} procesada: {res.get('personaje')}")
    else:
        print(f"  ⚠️ Escena {idx} no generó imágenes")

print("🎬 Flujo completo finalizado")