# 🐶 Proyecto Estelar — Generador de Historias Kira & Toby

Sistema modular para generar historias infantiles animadas con IA,
crear prompts de escenas para generadores de imagen/video,
y llevar un **control detallado del consumo de tokens y costos**.

---

## 📁 Estructura del Proyecto

```
proyecto-estelar/
│
├── codebase/                    ← Todo el código fuente
│   ├── main.py                  ← ▶️  Punto de entrada principal
│   ├── inputs.opt2.json         ← Base de datos de elementos narrativos
│   ├── .env                     ← 🔑 Tus API keys (no subir a git)
│   ├── .env.example             ← Plantilla del .env
│   │
│   ├── componentes/             ← Prompts del narrador IA
│   │   ├── history-teller.md   ← System prompt del narrador
│   │   └── prompt_template.md  ← Template con placeholders {lugar}, {objeto}...
│   │
│   ├── config/                  ← Configuración global
│   │   ├── config.py           ← Rutas, modelos, parámetros
│   │   ├── personajes.py       ← Prompts 3D de Kira y Toby
│   │   └── __init__.py
│   │
│   └── modules/                 ← Lógica del negocio
│       ├── token_tracker.py    ← 📊 Control de tokens y costos
│       ├── data_loader.py      ← Carga del JSON y archivos externos
│       ├── story_generator.py  ← Generación con GPT-4o
│       ├── story_storage.py    ← Guardado en disco
│       ├── image_generator.py  ← Generación con Google Imagen
│       ├── utils.py            ← Funciones auxiliares
│       └── __init__.py
│
├── assets/
│   └── personajes/             ← Imágenes generadas de personajes
│       └── {nombre}/
│           ├── front.png
│           ├── side.png
│           └── quarter.png
│
├── logs/
│   └── token_usage.json        ← 📊 Historial acumulado de tokens
│
└── outputs/
    └── historias/
        ├── revision/           ← Historias generadas (por revisar)
        │   └── {TITULO}/
        │       ├── {TITULO}-{timestamp}.txt   ← Historia + tokens
        │       └── prompts-scenas/
        │           ├── escena1.md
        │           └── escenaN.md
        └── aprobadas/          ← Mover aquí las historias aprobadas
```

---

## 🚀 Instalación

```bash
# 1. Instalar dependencias
pip install openai google-genai python-dotenv Pillow

# 2. Configurar API keys
cd codebase/
cp .env.example .env
# Editar .env y añadir tus claves reales

# 3. Verificar que inputs.opt2.json está en codebase/
ls codebase/inputs.opt2.json
```

---

Qué cambié y por qué
main.py — nuevo modo --modo escenas
El cambio clave. Ahora puedes tomar cualquier historia ya guardada y pasarle el scene_generator completo:


# Caso exacto que describes: historia ya guardada en disco
python main.py --modo escenas --historia "outputs\historias\revision\Aventuras_en_el_Parque_del_Río\Aventuras_en_el_Parque_del_Río-20260228-021434.txt"

# Con tu characters.json propio (Kira y Toby con lazo rojo y collar azul)
python main.py --modo escenas --historia "ruta.txt" --characters "characters.json"

# Solo re-validar escenas ya existentes sin regenerarlas
python main.py --modo escenas --historia "ruta.txt" --solo-validar

# Con umbral más estricto
python main.py --modo escenas --historia "ruta.txt" --threshold 90



Los escenaN.md se guardan automáticamente en la misma carpeta del .txt, dentro de prompts-scenas/, sin que tengas que especificar nada más.
Resolución automática del characters.json
El sistema busca los personajes en este orden, sin que tengas que indicarlo:

--characters si lo pasas explícitamente
characters.json en la misma carpeta del .txt
characters.json en codebase/ ← el que subiste está aquí ahora
inputs.opt2.json del proyecto como fallback

scene_generator.py — extractor mejorado
El extractor _extract_story_text() ahora es mucho más robusto: detecta el bloque **HISTORIA:** y extrae solo los párrafos narrativos, ignorando **TÍTULO:**, **MORALEJA:**, **ESCENAS:** y la metadata de tokens. Funciona tanto con .txt del proyecto como con .md planos.




## ▶️ Uso

Todos los comandos se ejecutan **desde dentro de `codebase/`**:

```bash
cd codebase/
```

### Generar una historia
```bash
python main.py
# o explícitamente:
python main.py --modo historia
```

### Generar imágenes de personajes secundarios
```bash
# Con Google Imagen (consume API):
python main.py --modo imagen

# Con placeholders para testing (sin consumir API):
python main.py --modo imagen --placeholder
```

### Modo completo (historia + imágenes del personaje)
```bash
python main.py --modo completo
```

### Ver historial de consumo de tokens
```bash
python main.py --tokens
```

---

## 📊 Control de Tokens

Cada vez que el sistema llama a OpenAI o Google, registra automáticamente:

- Tokens de entrada y salida
- Modelo utilizado
- Costo estimado en USD
- Metadata (personaje, lugar, moraleja)

### En consola (tiempo real):
```
  🔢 [generar_historia] gpt-4o → 1,823 tokens (~$0.0183 USD)
  🖼️  [generar_vista_personaje] imagen-4.0-fast-generate-001 → 1 imagen(es) (~$0.0400 USD)

  ───────────────────────────────────────────────────────
  📊 CONSUMO DE TOKENS — SESIÓN ACTUAL
  ───────────────────────────────────────────────────────
  Tokens de entrada  (prompt):          1,234
  Tokens de salida   (completion):        589
  ──────────────────────────────────────────────────────
  TOTAL TOKENS:                         1,823
  Imágenes generadas:                       3
  Costo estimado:                      $0.1382 USD
  ───────────────────────────────────────────────────────
```

### En el archivo .txt de la historia guardada:
```
══════════════════════════════════════════════════════
📊 CONSUMO DE TOKENS
══════════════════════════════════════════════════════
  Tokens de entrada   (prompt):         1,234
  Tokens de salida    (completion):       589
  ──────────────────────────────────────────────────
  TOTAL TOKENS:                         1,823
  Costo estimado:                      $0.0183 USD
══════════════════════════════════════════════════════
```

### Historial acumulado (`logs/token_usage.json`):
```json
{
  "cumulative": {
    "total_tokens": 15420,
    "images_generated": 12,
    "estimated_cost_usd": 1.2840,
    "total_sessions": 7
  }
}
```

---

## ⚙️ Configuración de Modelos

Edita `codebase/config/config.py` para cambiar modelos:

```python
OPENAI_MODEL = "gpt-4o"       # Más barato y rápido
# OPENAI_MODEL = "gpt-4"      # Más potente, más caro
# OPENAI_MODEL = "gpt-3.5-turbo"  # Mucho más barato

IMAGE_MODEL = "imagen-4.0-fast-generate-001"
```

Los precios en `modules/token_tracker.py` se actualizan ahí:

```python
PRICING = {
    "gpt-4o": {"input": 2.50, "output": 10.00},   # USD por 1M tokens
    ...
}
```

---

## 🔄 Flujo Completo de Producción de Video

```
inputs.opt2.json
      ↓
  main.py --modo completo
      ↓
outputs/historias/revision/TITULO/
      ├── TITULO.txt               ← Historia revisable
      └── prompts-scenas/
          ├── escena1.md           ← Prompt imagen + video
          └── escena15.md
      ↓ (copiar a aprobadas/ cuando esté lista)
      ↓
Generadores de Video IA
(Sora / Runway / Pika / Kling)
      ↓
clips de video individuales
      ↓
Edición manual → video_completo.mp4
```
