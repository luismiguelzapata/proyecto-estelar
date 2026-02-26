# 🐶 Sistema Modular - Kira y Toby

Documentación del nuevo sistema modular y arquitectura mejorada del proyecto Estelar.

## 📁 Estructura de Carpetas

```
proyecto-estelar/
├── codebase/
│   ├── main.py                              ⭐ Punto de entrada principal
│   ├── inputs.opt2.json                     📊 Datos de historias y personajes
│   ├── config/
│   │   ├── __init__.py
│   │   └── config.py                        ⚙️ Configuración centralizada
│   ├── modules/                             🧩 Módulos principales
│   │   ├── __init__.py
│   │   ├── utils.py                         🛠️ Funciones auxiliares
│   │   ├── data_loader.py                   📂 Carga de datos y archivos externos
│   │   ├── story_generator.py               📖 Generación de historias (OpenAI)
│   │   ├── story_storage.py                 💾 Almacenamiento de historias
│   │   └── image_generator.py               🎨 Generación de imágenes (Gemini)
│   ├── componentes/
│   │   ├── history-teller.md                📝 Prompt del sistema
│   │   └── prompt_template.md               📝 Plantilla de prompts
│   └── opt2.generate-random... (legacy)     ⚠️ Archivo antiguo (mantener para compatibilidad)
│
├── assets/                                  🎨 Recursos generados
│   └── personajes/                          👥 Imágenes de personajes
│       ├── conejito-blanco/
│       │   └── conejito-blanco.jpg
│       ├── ardilla-energetica/
│       │   └── ardilla-energetica.jpg
│       └── ...
│
└── outputs/                                 📤 Historias generadas
    └── historias/
        └── revision/
            ├── Titulo_Historia_1/
            │   ├── Titulo_Historia_1-20260226-120000.txt
            │   └── prompts-scenas/
            │       ├── escena1.md
            │       ├── escena2.md
            │       └── ...
            └── ...
```

## 🚀 Cómo Usar

### 1. Instalación de Dependencias

```bash
pip install openai google-generativeai pillow python-dotenv
```

### 2. Configuración de Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto:

```env
OPENAI_API_KEY=tu_clave_aqui
GOOGLE_API_KEY=tu_clave_aqui
```

### 3. Ejecución desde Terminal

```powershell
cd codebase

# Generar una historia única
python main.py --modo historia

# Generar múltiples historias (5)
python main.py --modo historias --cantidad 5

# Generar imágenes de personajes (con API)
python main.py --modo imagen

# Generar imágenes placeholder (para testing sin API)
python main.py --modo imagen --placeholder

# Modo completo: historia + escenas + imágenes
python main.py --modo completo
```

### 4. Uso desde Python

```python
from modules import (
    generar_historia_aleatoria,
    guardar_historia,
    generar_imagen_personaje
)
from modules.story_generator import inicializar_generador

# Inicializar
inicializar_generador()

# Generar historia
resultado = generar_historia_aleatoria()

# Guardar
guardado = guardar_historia(resultado)

# Generar imagen de personaje
imagen_path = generar_imagen_personaje(resultado['elementos']['personaje_secundario'])
```

## 📚 Módulos Disponibles

### `config/config.py`
- Define rutas absolutas del proyecto
- Configuración de APIs (OpenAI, Google)
- Constantes globales
- Funciones de utilidad para rutas

### `modules/data_loader.py`
- `cargar_datos_historias()` - Carga JSON de historias
- `cargar_archivo_externo()` - Carga archivos externos
- `cargar_prompts()` - Carga prompts del sistema

### `modules/story_generator.py`
- `inicializar_generador()` - Inicializa el generador
- `generar_elementos_historia()` - Genera elementos aleatorios
- `generar_historia_aleatoria()` - Genera historia con GPT-4
- `generar_multiples_historias(cantidad)` - Genera N historias

### `modules/story_storage.py`
- `guardar_historia()` - Guarda historia en archivo
- `guardar_escenas_markdown()` - Crea markdown de escenas

### `modules/image_generator.py`
- `generar_imagen_personaje()` - Genera imagen con Gemini
- `generar_imagen_personaje_con_prompt()` - Genera imagen con prompt específico
- `generar_imagenes_escena()` - Genera imágenes de una escena completa
- `crear_imagen_placeholder()` - Crea imagen de prueba (Pillow)

### `modules/utils.py`
- `obtener_nombre_personaje()` - Extrae nombre del personaje
- `extraer_titulo_historia()` - Extrae título de la historia
- `extraer_escenas_historia()` - Extrae escenas de la historia
- `generar_prompt_imagen_escena()` - Genera prompt para imagen
- `generar_prompt_video_escena()` - Genera prompt para video
- `normalizar_nombre_archivo()` - Normaliza strings para nombres

## 🎨 Generación de Imágenes

### Estructura Automática

Cuando se genera una imagen para "conejito blanco":

```
assets/personajes/
└── conejito-blanco/
    └── conejito-blanco.jpg
```

### Flujo de Generación

1. Se extrae el campo `prompt-3D` del personaje en `inputs.opt2.json`
2. Se normaliza el nombre: "conejito blanco" → "conejito-blanco"
3. Se crea directorio: `assets/personajes/conejito-blanco/`
4. Se genera imagen con Gemini Flash 2.0
5. Se guarda como: `conejito-blanco.jpg`

### Ejemplo de Uso

```python
from modules import generar_imagen_personaje

# Personaje del JSON
personaje = {
    "nombre": "conejito blanco",
    "species": "conejo",
    "prompt-3D": "A single cute 3D cartoon baby rabbit..."
}

# Generar imagen
ruta_imagen = generar_imagen_personaje(personaje)
# → assets/personajes/conejito-blanco/conejito-blanco.jpg
```

## 📊 Estructura de Datos

### JSON (inputs.opt2.json)

```json
{
  "construccionHistorias": {
    "personajesSecundarios": [
      {
        "nombre": "conejito blanco",
        "species": "conejo",
        "height_ratio": "0.6x altura de Kira",
        "body_shape": "round",
        "prompt-3D": "A single cute 3D cartoon baby rabbit..."
      }
    ]
  }
}
```

## 🔄 Flujo Completo

```
usuario → main.py → inicializar_generador()
                  ├─ cargar_datos_historias()
                  ├─ cargar_prompts()
                  └─ generar_historia_aleatoria()
                     ├─ generar_elementos_historia()
                     ├─ llamada OpenAI GPT-4
                     └─ guardar_historia()
                        ├─ guardar_escenas_markdown()
                        └─ generar_imagenes_escena()
                           └─ generar_imagen_personaje()
                              └─ llamada Gemini Flash 2.0
```

## ⚙️ Configuración Avanzada

Edita `config/config.py` para cambiar:

- Rutas de entrada/salida
- Modelos ML (GPT-4 → GPT-4-Turbo, etc.)
- Parámetros de generación (temperatura, max_tokens)
- URLs de APIs

## 📝 Notas

- El archivo `opt2.generate-random-history-from-json.py` se mantiene para compatibilidad
- Los nuevos desarrollos usan `main.py`
- Los módulos son independientes y pueden importarse por separado
- Las rutas se resuelven automáticamente desde cualquier ubicación

## 🐛 Solución de Problemas

### Error: "OPENAI_API_KEY no configurada"
→ Agrega tu clave en `.env` o en variable de entorno

### Error: "GOOGLE_API_KEY no configurada"
→ Agrega tu clave de Google para Gemini

### Error: "Módulo no encontrado"
→ Asegúrate de ejecutar desde el directorio `codebase/`

### Imagen placeholder sin content
→ Instala Pillow: `pip install Pillow`

## 🔮 Próximas Mejoras

- [ ] Soporte para múltiples modelos de IA
- [ ] Cache de historias generadas
- [ ] Generación asíncrona de imágenes
- [ ] API REST para acceso remoto
- [ ] Dashboard web de visualización
- [ ] Base de datos para almacenar historias

---

**¡Disfruta generando historias mágicas con Kira y Toby! 🐶✨**
