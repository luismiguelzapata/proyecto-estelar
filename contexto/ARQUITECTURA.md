# 🏗️ Arquitectura del Proyecto

## Diagrama de Flujo Principal

```
┌─────────────────────────────────────────────────────────────────┐
│                          USUARIO                               │
│                   (python main.py --modo X)                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   main.py       │
                    │  (orquestador)  │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
   ┌─────────┐       ┌──────────────┐      ┌──────────┐
   │ Historia│       │  Historias   │      │  Imagen  │
   │ Única   │   +   │ Múltiples    │  +   │ Personaje│
   └────┬────┘       └──────┬───────┘      └────┬─────┘
        │                   │                    │
        └───────────────────┼────────────────────┘
                            │
                   ┌────────┴────────┐
                   │                 │
        ┌──────────▼──────────┐  ┌───▼──────────────────┐
        │ story_generator.py  │  │ image_generator.py   │
        ├─────────────────────┤  ├──────────────────────┤
        │ • generar_elementos │  │ • generar_imagen()   │
        │ • generar_historia()│  │ • llamar_gemini()    │
        │ • inicializar()     │  │ • guardar_imagen()   │
        └──────┬──────────────┘  └──────────┬───────────┘
               │                            │
        ┌──────▼────────┐           ┌──────▼──────┐
        │  OpenAI API   │           │ Gemini API  │
        │  (GPT-4)      │           │(Flash 2.0)  │
        └───────────────┘           └─────────────┘
               │                            │
        ┌──────▼────────┐           ┌──────▼──────────┐
        │text (historia)│           │bytes(imagen)    │
        └──────┬────────┘           └────────┬────────┘
               │                            │
        ┌──────▼──────────────────────────┬─┘
        │ story_storage.py                │
        ├─────────────────────────────────┤
        │ • guardar_historia()            │
        │ • guardar_escenas_markdown()    │
        │ • extraer_escenas()             │
        └──────┬──────────────────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
    ▼                     ▼
outputs/historias/   assets/personajes/
revision/            └─ conejito-blanco/
└─ Titulo_Historia/     └─ conejito-blanco.jpg
   ├─ Titulo_Historia-
   │  20260226-120000.txt
   └─ prompts-scenas/
      ├─ escena1.md
      ├─ escena2.md
      └─ ...
```

## Estructura de Módulos

```
┌─── CAPA DE CONFIGURACIÓN ──────────────────┐
│  config/                                   │
│  ├─ config.py (rutas, constantes, APIs)   │
│  └─ __init__.py                            │
└────────────────────────────────────────────┘
                      ▲
                      │ importa
                      │
┌─── CAPA DE DATOS ──────────────────────────┐
│  modules/data_loader.py                    │
│  • cargar_datos_historias()                │
│  • cargar_archivo_externo()                │
│  • cargar_prompts()                        │
└────────────────────────────────────────────┘
                      ▲
                      │ importa
              ┌───────┴───────────┐
              │                   │
┌─────────────▼──────────┐ ┌──────▼──────────────────┐
│ GENERACIÓN DE HISTORIAS│ │ GENERACIÓN DE IMÁGENES │
├────────────────────────┤ ├───────────────────────┤
│ story_generator.py     │ │ image_generator.py    │
│ • generar_elementos()  │ │ • generar_imagen()    │
│ • generar_historia()   │ │ • crear_placeholder() │
│ • inicializar_gen()    │ │ • generar_imagenes_  │
│                        │ │   escena()            │
└────────┬───────────────┘ └─────────┬─────────────┘
         │                           │
         └───────────┬───────────────┘
                     │
         ┌───────────▼────────────┐
         │   FUNCIONES AUXILIARES │
         ├────────────────────────┤
         │ utils.py               │
         │ • obtener_nombre()     │
         │ • extraer_titulo()     │
         │ • extraer_escenas()    │
         │ • normalizar_nombre()  │
         │ • generar_prompts()    │
         └────────────────────────┘
                     ▲
                     │ importa
                     │
         ┌───────────▼────────────┐
         │  ALMACENAMIENTO        │
         ├────────────────────────┤
         │ story_storage.py       │
         │ • guardar_historia()   │
         │ • guardar_escenas()    │
         └────────────────────────┘
```

## Flujo de Datos

```
1. CARGA DE DATOS
   ├─ config.py → rutas y variables
   ├─ inputs.opt2.json → elementos de historias
   ├─ history-teller.md → prompt del sistema
   └─ prompt_template.md → plantilla de prompts

2. GENERACIÓN
   ├─ generar_elementos_historia()
   │  └─ random.choice() sobre cada categoría
   ├─ generar_historia_aleatoria()
   │  ├─ OpenAI GPT-4 (+ elementos)
   │  └─ retorna texto de historia
   └─ generar_imagen_personaje()
      ├─ Gemini Flash 2.0 (+ prompt-3D)
      └─ retorna bytes de imagen

3. ALMACENAMIENTO
   ├─ guardar_historia()
   │  ├─ extract_titulo()
   │  ├─ create_directory()
   │  └─ write(historia.txt)
   ├─ guardar_escenas_markdown()
   │  ├─ extract_escenas()
   │  ├─ generate_prompts()
   │  └─ write(escenaN.md)
   └─ generar_imagen_personaje()
      ├─ normalize_nombre()
      ├─ create_directory(assets/personajes/nombre/)
      └─ write(nombre.jpg)

4. SALIDA FINAL
   outputs/historias/revision/
   └─ Titulo_Historia/
      ├─ Titulo_Historia-20260226-120000.txt
      └─ prompts-scenas/
         ├─ escena1.md
         ├─ escena2.md
         └─ ...

   assets/personajes/
   ├─ conejito-blanco/
   │  └─ conejito-blanco.jpg
   ├─ ardilla-energetica/
   │  └─ ardilla-energetica.jpg
   └─ ...
```

## Seguridad y Validación

```
INPUT VALIDATION
├─ config.py
│  ├─ ensure_directories_exist()
│  └─ validate API keys
├─ data_loader.py
│  ├─ file_exists()?
│  ├─ valid JSON?
│  └─ required_elements?
└─ utils.py
   ├─ normalize_filename()
   └─ clean_special_chars()

ERROR HANDLING
├─ try-except en todas las funciones
├─ error_messages informativos
├─ fallback a valores por defecto
└─ logging de operaciones
```

## Escalabilidad

```
ACTUAL (v1)
├─ 1 generador de historias (OpenAI)
├─ 1 generador de imágenes (Gemini)
└─ Archivos locales

PRÓXIMAS MEJORAS (v2+)
├─ Múltiples modelos intercambiables
├─ API REST para acceso remoto
├─ Base de datos (historias + imágenes)
├─ Caché de resultados
├─ Generación asíncrona
├─ Dashboard web
└─ Sistema de plugins
```

---

🏗️ **Arquitectura Modular** = Fácil de mantener, escalar y extender
