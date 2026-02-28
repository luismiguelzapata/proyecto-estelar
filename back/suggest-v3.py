"""
GUÍA DE MODIFICACIONES PARA INCORPORAR CARACTERÍSTICAS DE PERSONAJES SECUNDARIOS

Este archivo explica cómo modificar:
1. La estructura del JSON (inputs.opt2.json)
2. El código Python para capturar y usar esas características
"""

# ==========================================
# 1. NUEVA ESTRUCTURA DEL JSON
# ==========================================
"""
Cambiar "personajesSecundarios" de un array simple a un array de objetos:

JSON ACTUAL (INVÁLIDO):
"personajesSecundarios": [
  "conejito blanco",
  "ardilla mensajera",
  ...
]

JSON NUEVO (CORRECTO):
"personajesSecundarios": [
  {
    "nombre": "conejito blanco",
    "species": "conejo",
    "height_ratio": "0.6x altura de Kira",
    "body_shape": "cuerpo redondo y compacto",
    "head_ratio": "1.4x el cuerpo",
    "fur_color": "#FFFFFF",
    "inner_ear_color": "#FFDDE1",
    "eye_color": "#5C4033",
    "accessory": "pañuelo azul claro #A8D8EA",
    "forbidden_changes": "no manchas, no cambio de proporciones, no variación de color"
  },
  {
    "nombre": "ardilla mensajera",
    "species": "ardilla",
    "height_ratio": "0.55x altura de Kira",
    "body_shape": "pequeña con cola muy esponjosa en espiral fija",
    "head_ratio": "1.3x el cuerpo",
    "fur_color": "#C68642",
    "belly_color": "#F3D7B6",
    "eye_color": "#2F1B0C",
    "accessory": "mochila roja #E63946",
    "forbidden_changes": "no alterar tamaño de cola ni tonalidad"
  },
  {
    "nombre": "búho sabio",
    "species": "búho",
    "height_ratio": "0.8x altura de Kira",
    "body_shape": "ovalado robusto",
    "head_ratio": "proporcional grande",
    "feather_color": "#8C6A4A",
    "eye_color": "#F4A261",
    "accessory": "gafas redondas doradas #C9A227",
    "forbidden_changes": "no quitar gafas, no cambiar tamaño"
  }
  ... más personajes
]
"""


# ==========================================
# 2. MODIFICACIONES EN EL CÓDIGO PYTHON
# ==========================================

"""
A. FUNCIÓN: generar_elementos_historia()

CAMBIO NECESARIO:
- Cambiar de: random.choice(DATOS_HISTORIAS['personajesSecundarios'])
- Cambiar a: random.choice(DATOS_HISTORIAS['personajesSecundarios'])
  (automáticamente devolverá el dict completo en lugar de string)

La función se mantiene igual porque ya manejará el nuevo formato.
Sin embargo, necesitas adaptar cómo se usa.
"""

# VERSIÓN MEJORADA DE generar_elementos_historia():
def generar_elementos_historia_v3():
    """
    Genera una combinación aleatoria de elementos incluyendo datos del personaje secundario.
    
    Returns:
        dict: Diccionario con elementos seleccionados (ahora con personaje_secundario como objeto)
    """
    
    # Ahora personaje_secundario es un dict con todas las características
    personaje_secundario = random.choice(DATOS_HISTORIAS['personajesSecundarios'])
    
    elementos = {
        "lugar": random.choice(DATOS_HISTORIAS['lugares']),
        "objeto_principal": random.choice(DATOS_HISTORIAS['objetosCotidianos']),
        "color_objeto": random.choice(DATOS_HISTORIAS['colores']),
        "objeto_magico": random.choice(DATOS_HISTORIAS['objetosMagicos']),
        "personaje_secundario": personaje_secundario,  # Ahora es un dict completo
        "sentimiento_kira": random.choice(DATOS_HISTORIAS['sentimientos']),
        "sentimiento_toby": random.choice(DATOS_HISTORIAS['sentimientos']),
        "fenomeno": random.choice(DATOS_HISTORIAS['fenomenosNaturales']),
        "desafio": random.choice(DATOS_HISTORIAS['desafios']),
        "accion_kira": random.choice(DATOS_HISTORIAS['accionesClaves']),
        "accion_toby": random.choice(DATOS_HISTORIAS['accionesClaves']),
        "moraleja": random.choice(DATOS_HISTORIAS['moralejas'])
    }
    
    return elementos


"""
B. FUNCIÓN: generar_prompt_imagen_escena()

CAMBIO NECESARIO:
- Extraer características del personaje_secundario dict
- Incluir esas características en el prompt
"""

def generar_prompt_imagen_escena_v3(num_escena, descripcion_escena, historia_dict):
    """
    Genera un prompt en español para generar imagen con características del personaje.
    
    Args:
        num_escena (int): Número de la escena
        descripcion_escena (str): Descripción de la escena
        historia_dict (dict): Diccionario con información de la historia
        
    Returns:
        str: Prompt enriquecido con características del personaje
    """
    lugar = historia_dict.get("elementos", {}).get("lugar", "escena mágica")
    color_obj = historia_dict.get("elementos", {}).get("color_objeto", "mágico")
    objeto = historia_dict.get("elementos", {}).get("objeto_principal", "objeto")
    
    # NUEVA: Extraer características del personaje secundario
    personaje_sec = historia_dict.get("elementos", {}).get("personaje_secundario", {})
    nombre_personaje = personaje_sec.get("nombre", "personaje secundario")
    species_personaje = personaje_sec.get("species", "")
    body_shape = personaje_sec.get("body_shape", "")
    height_ratio = personaje_sec.get("height_ratio", "")
    fur_color = personaje_sec.get("fur_color", "")
    eye_color = personaje_sec.get("eye_color", "")
    accessory = personaje_sec.get("accessory", "")
    forbidden = personaje_sec.get("forbidden_changes", "")
    
    # Construir descripción física del personaje secundario
    caracteristicas_personaje = f"""
PERSONAJE SECUNDARIO - {nombre_personaje.upper()}:
- Especie: {species_personaje}
- Forma del cuerpo: {body_shape}
- Altura: {height_ratio}
- Color de pelaje/plumas: {fur_color}
- Color de ojos: {eye_color}
- Accesorios: {accessory}
- PROHIBIDO: {forbidden}
"""
    
    prompt = f"""Escena cinematográfica de película animada.

Estilo: Similar a una película de animación 3D de alta calidad, mágica y acogedora.

Escena {num_escena}: {descripcion_escena}

Lugar: {lugar} con iluminación cálida de hora dorada, luz suave y soñadora.

PERSONAJES PRINCIPALES:
- Kira (perrita): Energética y expresiva, con postura confiada y movimientos animados.
- Toby (perrito): Ligeramente más pequeño, pensativo, con ojos curiosos y gestos observadores.

{caracteristicas_personaje}

ELEMENTO DESTACADO: {objeto} de color {color_obj}

ATMÓSFERA: Calorosa, mágica y envolvente. Música orquestal suave.

CALIDAD: Cinemática, animación altamente detallada, 4K, atmósfera emotiva y edificante.

Perfecto para audiencia infantil."""
    
    return prompt


"""
C. FUNCIÓN: generar_prompt_video_escena()

CAMBIO NECESARIO:
- Similar a la función anterior, extraer y incluir características del personaje
"""

def generar_prompt_video_escena_v3(num_escena, descripcion_escena, historia_dict):
    """
    Genera un prompt en español para generar video con características del personaje.
    """
    lugar = historia_dict.get("elementos", {}).get("lugar", "escena mágica")
    
    # NUEVA: Extraer características del personaje secundario
    personaje_sec = historia_dict.get("elementos", {}).get("personaje_secundario", {})
    nombre_personaje = personaje_sec.get("nombre", "personaje secundario")
    accessory = personaje_sec.get("accessory", "")
    
    prompt = f"""VIDEO ANIMADO - Escena {num_escena}

Descripción: {descripcion_escena}

Duración: 15-30 segundos

Locación: {lugar}

PERSONAJES EN PANTALLA:
- Kira y Toby con sus características consistentes
- {nombre_personaje} (con {accessory}) interactuando de forma expresiva

ELEMENTOS DE CÁMARA:
- Transiciones suaves
- Movimiento de cámara envolvente

SONIDO:
- Música: orquestal, suave y aventurera
- Efectos: subtiles y mágicos

Iluminación: Cálida, dorada, mágica.

Qualidad: 4K, animación suave, atmósfera emotiva."""
    
    return prompt


"""
D. FUNCIÓN AUXILIAR: Obtener nombre del personaje (para textos)

Nueva función para convertir el dict en string cuando se necesite:
"""

def obtener_nombre_personaje(personaje_dict):
    """
    Extrae el nombre del personaje desde el dict.
    Si recibe un string (compatibilidad), lo devuelve directamente.
    
    Args:
        personaje_dict: dict o str con datos del personaje
        
    Returns:
        str: Nombre del personaje
    """
    if isinstance(personaje_dict, dict):
        return personaje_dict.get("nombre", "personaje desconocido")
    else:
        return str(personaje_dict)


"""
E. MODIFICAR generar_elementos_historia() EN EL PROMPT TEMPLATE

En la sección donde se usa PROMPT_TEMPLATE.format(**elementos),
ahora necesitas adaptar cómo aparece el personaje_secundario en el template.

ANTES:
PERSONAJE SECUNDARIO: {personaje_secundario}

DESPUÉS (opción 1 - solo nombre):
PERSONAJE SECUNDARIO: {personaje_secundario_nombre}

O (opción 2 - descripción completa):
{personaje_secundario_descrip}

Para esto, debes modificar generar_elementos_historia() así:
"""

def generar_elementos_historia_v3_mejorada():
    """
    Versión con campos adicionales para el template.
    """
    personaje_secundario = random.choice(DATOS_HISTORIAS['personajesSecundarios'])
    
    # Crear versión para template
    if isinstance(personaje_secundario, dict):
        personaje_nombre = personaje_secundario.get("nombre", "personaje")
        personaje_descrip = f"""
Personaje: {personaje_nombre} ({personaje_secundario.get('species', '')})
Características: {personaje_secundario.get('body_shape', '')}
Accesorio: {personaje_secundario.get('accessory', '')}
"""
    else:
        personaje_nombre = personaje_secundario
        personaje_descrip = personaje_secundario
    
    elementos = {
        "lugar": random.choice(DATOS_HISTORIAS['lugares']),
        "objeto_principal": random.choice(DATOS_HISTORIAS['objetosCotidianos']),
        "color_objeto": random.choice(DATOS_HISTORIAS['colores']),
        "objeto_magico": random.choice(DATOS_HISTORIAS['objetosMagicos']),
        # Versiones del personaje secundario para diferentes usos
        "personaje_secundario": personaje_secundario,
        "personaje_secundario_nombre": personaje_nombre,
        "personaje_secundario_descrip": personaje_descrip,
        "sentimiento_kira": random.choice(DATOS_HISTORIAS['sentimientos']),
        "sentimiento_toby": random.choice(DATOS_HISTORIAS['sentimientos']),
        "fenomeno": random.choice(DATOS_HISTORIAS['fenomenosNaturales']),
        "desafio": random.choice(DATOS_HISTORIAS['desafios']),
        "accion_kira": random.choice(DATOS_HISTORIAS['accionesClaves']),
        "accion_toby": random.choice(DATOS_HISTORIAS['accionesClaves']),
        "moraleja": random.choice(DATOS_HISTORIAS['moralejas'])
    }
    
    return elementos


# ==========================================
# 3. RESUMEN DE CAMBIOS NECESARIOS
# ==========================================

"""
PASO 1: Actualizar JSON (inputs.opt2.json)
└─ Cambiar personajesSecundarios de array de strings a array de objetos
└─ Cada objeto debe tener: nombre, especies, dimensiones, colores, accesorios, etc.

PASO 2: Actualizar generar_elementos_historia()
└─ Ahora devolverá personaje_secundario como dict completo
└─ Agregar campos adicionales: personaje_secundario_nombre, personaje_secundario_descrip

PASO 3: Actualizar generar_prompt_imagen_escena()
└─ Extraer características del dict del personaje
└─ Incluirlas en el prompt: especie, colores, accesorios, restricciones

PASO 4: Actualizar generar_prompt_video_escena()
└─ Similar al paso 3, adaptado para prompts de video

PASO 5: Actualizar PROMPT_TEMPLATE (en el archivo txt/md)
└─ Cambiar {personaje_secundario} por {personaje_secundario_nombre}
└─ O usar {personaje_secundario_descrip} para más detalles

PASO 6: Adaptaciones menores
└─ Cualquier lugar donde se use personaje_secundario como string
└─ Envolver con obtener_nombre_personaje() si es necesario
"""

# ==========================================
# 4. EJEMPLO COMPLETO DE CÓMO QUEDA
# ==========================================

"""
Con estas modificaciones, cuando generas una historia:

1. Se elige un personaje secundario: {"nombre": "conejito blanco", ...}

2. Se generan elementos que incluyen todo el dict

3. En generar_prompt_imagen_escena() extrae y formatea:
   - Nombre: "conejito blanco"
   - Especie: "conejo"
   - Color: "#FFFFFF"
   - Accesorio: "pañuelo azul claro #A8D8EA"
   - Restricciones: "no manchas, no cambio de proporciones"

4. El prompt resultante es específico y consistente:
   "PERSONAJE SECUNDARIO - CONEJITO BLANCO:
    - Especie: conejo
    - Forma del cuerpo: cuerpo redondo y compacto
    - Altura: 0.6x altura de Kira
    - Color de pelaje: #FFFFFF
    - Color de ojos: #5C4033
    - Accesorios: pañuelo azul claro #A8D8EA
    - PROHIBIDO: no manchas, no cambio de proporciones, no variación de color"

5. Esto se mantiene CONSISTENTE en todas las escenas de esa historia
"""

print("✅ Archivo de sugerencias generado con éxito")
print("📖 Lee los cambios necesarios en los comentarios de este archivo")
