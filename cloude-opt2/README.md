# 🎬 Generador de Escenas para Historias Animadas

Sistema automático que convierte una historia en texto en **prompts detallados para generadores de video IA** (Sora, Runway ML, Pika, Kling), manteniendo coherencia visual y narrativa entre escenas.

---

## 📁 Estructura de Archivos

```
proyecto/
│
├── scene_generator.py      ← Script principal
├── historia.md             ← Tu historia (un párrafo = una escena)
├── characters.json         ← Descripción física de personajes
├── .env                    ← Tu API key de OpenAI
├── .env.example            ← Plantilla del .env
│
└── [generados automáticamente]
    ├── escena1.md          ← Prompt de la escena 1
    ├── escena2.md          ← Prompt de la escena 2
    ├── escena3.md          ← ...
    ├── escena4.md
    ├── escena5.md
    ├── escena6.md
    ├── RESUMEN_FINAL.md    ← Reporte legible final
    └── coherence_report_v1.json  ← Reporte técnico JSON
```

---

## 🚀 Instalación

```bash
# 1. Instalar dependencias
pip install openai python-dotenv

# 2. Configurar API key
cp .env.example .env
# Editar .env y añadir tu OPENAI_API_KEY

# 3. Preparar tus archivos
# → historia.md con la historia (párrafos separados por línea en blanco)
# → characters.json con los personajes
```

---

## ▶️ Uso

### Flujo completo (generar + validar)
```bash
python scene_generator.py --story historia.md --characters characters.json
```

### Con directorio de salida específico
```bash
python scene_generator.py --story historia.md --characters characters.json --output ./mi_proyecto
```

### Con umbral de coherencia personalizado
```bash
python scene_generator.py --story historia.md --characters characters.json --threshold 90
```

### Solo validar escenas ya existentes (sin regenerar)
```bash
python scene_generator.py --story historia.md --characters characters.json --only-validate
```

---

## ⚙️ Cómo funciona

### Fase 1 — Análisis de la historia
- Lee `historia.md` y divide por párrafos (líneas en blanco como separador)
- Cuenta automáticamente el número de escenas

### Fase 2 — Generación de escenas
Para cada párrafo, un agente **Director Creativo CGI** genera un prompt que incluye:
- `ENVIRONMENT` — Ambiente, hora del día, paleta de colores
- `CHARACTERS PRESENT` — Personajes en escena y estado emocional
- `ACTION & MOVEMENT` — Secuencia de acciones y movimiento de cámara
- `CAMERA` — Tipo de plano y ángulo
- `LIGHTING & MOOD` — Iluminación y atmósfera
- `TECHNICAL` — Estilo 3D, calidad render, duración estimada
- `CONTINUITY NOTES` — Elementos que DEBEN continuar en la siguiente escena

### Fase 3 — Validación de coherencia (Agente Editor)
Un segundo agente **Editor Experto en Narrativa Visual** evalúa:

| Criterio | Descripción |
|----------|-------------|
| Coherencia visual | ¿Los personajes mantienen sus características? |
| Coherencia narrativa | ¿La historia fluye lógicamente? |
| Continuidad de ambiente | ¿Luz, objetos y clima son consistentes? |
| Continuidad de acciones | ¿Las escenas conectan fluidamente? |
| Claridad para IA | ¿Cada prompt es suficientemente detallado? |

**Si la puntuación < umbral (default 85%):**
- El editor identifica los problemas específicos
- Genera correcciones automáticas
- Aplica los cambios y re-evalúa
- Hasta 3 iteraciones de corrección automática

### Fase 4 — Archivos de salida
- `escenaN.md` — Prompt listo para enviar a generadores de video IA
- `RESUMEN_FINAL.md` — Reporte visual con puntuaciones y problemas
- `coherence_report_vN.json` — Datos técnicos del análisis

---

## 📝 Formato de historia.md

Cada párrafo separado por **una línea en blanco** = una escena:

```markdown
Primera escena aquí. Puede ocupar varias oraciones
dentro del mismo párrafo sin problema.

Segunda escena aquí. Todo lo que está entre
dos líneas en blanco forma una sola escena.

Tercera escena...
```

---

## 🎨 Formato de characters.json

```json
{
  "personajesPrincipales": [
    {
      "nombre": "Kira",
      "species": "perro",
      "fur_color": "#F5C542",
      "eye_color": "#1E90FF",
      "accessory": "lazo rojo en la oreja",
      "forbidden_changes": "no cambiar color dorado ni ojos azules"
    }
  ],
  "personajesSecundarios": [...],
  "objectosImportantes": [...]
}
```

> 💡 Usa **hex exactos** para los colores. El sistema los pasa directamente al prompt
> para que la IA de video mantenga consistencia entre escenas.

---

## 🎯 Objetivo final

Los prompts generados están optimizados para:

| Generador de Video IA | Compatible |
|-----------------------|-----------|
| OpenAI Sora           | ✅ |
| Runway ML Gen-3       | ✅ |
| Pika 1.5              | ✅ |
| Kling AI              | ✅ |
| Luma Dream Machine    | ✅ |

Flujo de producción de video:
```
historia.md → escenaN.md → [IA Video Generator] → clip_N.mp4 → [Edición manual] → video_completo.mp4
```

---

## 🔧 Configuración avanzada

Edita estas constantes al inicio de `scene_generator.py`:

```python
MODEL_SCENE    = "gpt-4o"   # Modelo para generar escenas
MODEL_EDITOR   = "gpt-4o"   # Modelo para validar coherencia
COHERENCE_THRESHOLD = 85    # % mínimo para aprobar
MAX_FIX_ITERATIONS  = 3     # Intentos máximos de corrección automática
```
