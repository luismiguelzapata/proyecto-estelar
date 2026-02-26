# 🎨 Características de Generación de 3 Vistas

## Nueva Funcionalidad: Generación de Múltiples Poses

Se ha actualizado el módulo `image_generator.py` para generar **3 vistas diferentes** de cada personaje automáticamente.

---

## 📸 Vistas Disponibles

| Vista | Descripción | Archivo |
|-------|-------------|---------|
| **Front** | Vista frontal centrada | `front.jpg` |
| **Side** | Perfil derecho completo | `side.jpg` |
| **Quarter** | Vista 3/4 a 45° | `quarter.jpg` |

---

## 📁 Estructura de Carpetas Generada

Cuando generas imágenes para "conejito blanco", se crea:

```
assets/personajes/
└── conejito-blanco/
    ├── front.jpg    (vista frontal)
    ├── side.jpg     (vista de perfil)
    └── quarter.jpg  (vista 3/4)
```

---

## 🚀 Cómo Usar

### Opción 1: Automático (3 vistas)

```python
from modules.image_generator import generar_tres_vistas_personaje

# Generar 3 vistas automáticamente
vistas = generar_tres_vistas_personaje(
    nombre_personaje="conejito blanco",
    prompt_3d="A cute 3D cartoon baby rabbit..."
)

# Resultado:
# {
#     "front": Path(...front.jpg),
#     "side": Path(...side.jpg),
#     "quarter": Path(...quarter.jpg)
# }
```

### Opción 2: A través de generar_imagen_personaje()

```python
from modules import generar_imagen_personaje

personaje = {
    "nombre": "conejito blanco",
    "prompt-3D": "A cute 3D cartoon baby rabbit..."
}

# Generar 3 vistas (por defecto)
vistas = generar_imagen_personaje(personaje, generar_tres_vistas=True)

# O generar solo 1 imagen
imagen_unica = generar_imagen_personaje(personaje, generar_tres_vistas=False)
```

### Opción 3: En generar_imagenes_escena()

```python
from modules import generar_imagen_personaje

# Automáticamente incluye las 3 vistas
resultado = generar_imagenes_escena(
    historia_dict,
    generar_tres_vistas=True  # por defecto
)

# Retorna:
# {
#     "imagenes": {
#         "front": Path(...),
#         "side": Path(...),
#         "quarter": Path(...)
#     },
#     "generadas": 3,
#     "personaje": "conejito blanco"
# }
```

---

## 🔧 Modificaciones Internas

### Prompts Personalizados por Pose

Cada vista recibe un prompt específico:

```python
# Vista frontal
"IMPORTANT: The pose for this character MUST be: centered composition"

# Vista de perfil
"IMPORTANT: The pose for this character MUST be: right side profile view, 
full body visible from nose to tail tip"

# Vista 3/4
"IMPORTANT: The pose for this character MUST be: three-quarter view at 
45-degree angle, full body visible, looking slightly toward camera"
```

### Estructura de POSES_PERSONAJE

```python
POSES_PERSONAJE = {
    "front": {
        "nombre": "Vista Frontal",
        "descripcion": "centered composition",
        "archivo": "front.jpg"
    },
    "side": {
        "nombre": "Perfil Derecho",
        "descripcion": "right side profile view, full body visible from nose to tail tip",
        "archivo": "side.jpg"
    },
    "quarter": {
        "nombre": "Vista 3/4",
        "descripcion": "three-quarter view at 45-degree angle, full body visible, looking slightly toward camera",
        "archivo": "quarter.jpg"
    }
}
```

---

## 📊 Flujo de Generación

```
generar_imagen_personaje(personaje, generar_tres_vistas=True)
    ↓
generar_tres_vistas_personaje(nombre, prompt)
    ├─ Loop para cada pose en POSES_PERSONAJE
    │   ├─ Agregar descripción de pose al prompt
    │   ├─ Llamar a _llamar_gemini_imagen(prompt_con_pose)
    │   └─ Guardar en: assets/personajes/{nombre}/{archivo_pose}
    │
    └─ Retornar Dict con 3 rutas


RESULTADO:
assets/personajes/conejito-blanco/
├── front.jpg
├── side.jpg
└── quarter.jpg
```

---

## 💡 Casos de Uso

### Caso 1: Generar todas las vistas de un personaje

```python
from modules.data_loader import cargar_datos_historias
from modules.image_generator import generar_tres_vistas_personaje

datos = cargar_datos_historias()
personajes = datos['personajesSecundarios']

for personaje in personajes:
    if isinstance(personaje, dict) and 'prompt-3D' in personaje:
        nombre = personaje['nombre']
        prompt = personaje['prompt-3D']
        
        vistas = generar_tres_vistas_personaje(nombre, prompt)
        print(f"✅ {nombre}: {len(vistas)} vistas generadas")
```

### Caso 2: Generar solo vista frontal

```python
vistas = generar_imagen_personaje(personaje, generar_tres_vistas=False)
# Resultado: Una sola imagen (front.jpg por defecto)
```

### Caso 3: Usar en pipeline de historias + imágenes

```python
from modules import generar_historia_aleatoria, generar_imagenes_escena
from modules.story_generator import inicializar_generador

inicializar_generador()

# Generar historia
resultado = generar_historia_aleatoria()

# Generar 3 vistas del personaje
imagenes = generar_imagenes_escena(resultado, generar_tres_vistas=True)

# Resultado: 3 imágenes del personaje secundario
print(f"✅ Generadas {imagenes['generadas']} vistas")
```

---

## ⚙️ API de Referencia

### generar_tres_vistas_personaje()

```python
def generar_tres_vistas_personaje(
    nombre_personaje: str,
    prompt_3d: str
) -> Dict[str, Optional[Path]]:
    """
    Genera 3 vistas (front, side, quarter) de un personaje.
    
    Args:
        nombre_personaje: Nombre del personaje (ej: "conejito blanco")
        prompt_3d: Prompt detallado del personaje
    
    Returns:
        Dict con rutas: {"front": Path, "side": Path, "quarter": Path}
    """
```

### generar_imagen_personaje()

```python
def generar_imagen_personaje(
    personaje_dict: Dict[str, Any],
    generar_tres_vistas: bool = True  # NUEVO PARÁMETRO
) -> Optional[Dict[str, Optional[Path]]]:
    """
    Genera imagen(s) de un personaje.
    
    Args:
        personaje_dict: Diccionario del personaje con prompt-3D
        generar_tres_vistas: Si True genera 3 vistas, si False genera 1
    
    Returns:
        Dict con rutas o None si error
    """
```

### generar_imagenes_escena()

```python
def generar_imagenes_escena(
    historia_dict: Dict[str, Any],
    generar_tres_vistas: bool = True  # NUEVO PARÁMETRO
) -> Dict[str, Any]:
    """
    Genera imágenes del personaje de una escena.
    
    Args:
        historia_dict: Diccionario con elementos de la historia
        generar_tres_vistas: Si True genera 3 vistas
    
    Returns:
        Dict con información de imágenes generadas
    """
```

---

## 🔍 Validación

Para verificar que todo funciona:

```bash
python EJEMPLO_3_VISTAS.py
```

O importa directamente:

```python
from modules.image_generator import POSES_PERSONAJE
print(POSES_PERSONAJE.keys())  # ['front', 'side', 'quarter']
```

---

## 📝 Notas Importantes

1. ✅ **Poses personalizables**: Puedes editar `POSES_PERSONAJE` en `image_generator.py` para agregar más vistas
2. ✅ **Compatible con API**: Funciona con Gemini Flash 2.0
3. ✅ **Automático**: Por defecto genera 3 vistas en todos los métodos
4. ✅ **Reversible**: Usa `generar_tres_vistas=False` para generar solo 1 vista
5. ✅ **Descriptor de pose**: Cada pose incluye instrucción clara en el prompt

---

## 🎯 Próximas Mejoras

- [ ] Agregar más poses (vista trasera, superior, etc.)
- [ ] Generar variaciones de estilo (different lighting, colors)
- [ ] Caché de imágenes para no regenerar
- [ ] Optimización de llamadas a Gemini (batch processing)

---

**¡Las 3 vistas de personajes están listas para uso!** 🚀
