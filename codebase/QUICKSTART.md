# Quick Start - Guía Rápida

## 🚀 Inicio Rápido en 5 minutos

### Paso 1: Instalar Dependencias
```bash
pip install openai google-generativeai pillow python-dotenv
```

### Paso 2: Configurar API Keys
Crea `.env` en la raíz:
```
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AIza...
```

### Paso 3: Ejecutar Historias
```bash
cd codebase
python main.py --modo historia
```

**¡Listo!** Tu historia se guardará en `outputs/historias/revision/`

---

## 📋 Comandos Principales

```bash
# Una historia
python main.py --modo historia

# 5 historias
python main.py --modo historias --cantidad 5

# Imágenes de personajes (prueba sin API)
python main.py --modo imagen --placeholder

# Imágenes reales con Gemini
python main.py --modo imagen

# Todo: historia + escenas + imágenes
python main.py --modo completo
```

---

## 📂 Dónde Buscar Archivos Generados

```
outputs/historias/revision/
└── Nombre_Historia_12345/
    ├── Nombre_Historia_12345-20260226-120000.txt  (historia)
    └── prompts-scenas/
        ├── escena1.md  (con prompts para Midjourney)
        ├── escena2.md
        └── ...

assets/personajes/
├── conejito-blanco/conejito-blanco.jpg
├── ardilla-energetica/ardilla-energetica.jpg
└── ...
```

---

## 💡 Usos Comunes

### Generar una historia y guardar
```python
from modules.story_generator import inicializar_generador
from modules import generar_historia_aleatoria, guardar_historia

inicializar_generador()
resultado = generar_historia_aleatoria()
guardar_historia(resultado)
```

### Generar imagen de un personaje específico
```python
from modules import generar_imagen_personaje

personaje = {
    "nombre": "conejito blanco",
    "prompt-3D": "A cute 3D cartoon baby rabbit..."
}

generar_imagen_personaje(personaje)
```

---

## 🆘 Soporte

- **Error de imports**: Ejecuta desde `codebase/`
- **API timeout**: Revisa conexión internet
- **No genera imágenes**: Verifica claves Google API

¡Disfruta! 🎉
