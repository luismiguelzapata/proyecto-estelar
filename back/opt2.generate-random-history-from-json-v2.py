import random
import json
import re
from pathlib import Path
from datetime import datetime
from openai import OpenAI

client = OpenAI()

# ========================================
# CARGAR TEXTOS EXTERNOS
# ========================================

def cargar_texto_externo(nombre_archivo):
    ruta = Path(__file__).parent / nombre_archivo
    with open(ruta, 'r', encoding='utf-8') as f:
        return f.read()
    

SYSTEM_PROMPT = cargar_texto_externo("./componentes/history-teller.md")
PROMPT_TEMPLATE = cargar_texto_externo("./componentes/prompt_template.md")



def obtener_identidad_visual(personaje):
    identidad = DATOS_HISTORIAS.get("identidadVisualPersonajes", {}).get(personaje)
    
    if not identidad:
        return ""
    
    prompt_identidad = f"""
PERSONAJE FIJO (NO MODIFICAR DISEÑO):
- Especie: {identidad['species']}
- Tamaño relativo: {identidad['height_ratio']}
- Forma cuerpo: {identidad['body_shape']}
- Proporción cabeza: {identidad['head_ratio']}
- Color pelaje: {identidad['fur_color']}
- Interior orejas: {identidad['inner_ear_color']}
- Color ojos: {identidad['eye_color']}
- Nariz: {identidad['nose_color']}
- Orejas: {identidad['ears']}
- Cola: {identidad['tail']}
- Accesorio permanente: {identidad['accessory']}

REGLAS ESTRICTAS:
{identidad['forbidden_changes']}
"""
    return prompt_identidad



# ========================================
# CARGAR DATOS DEL JSON EXTERNO
# ========================================

def cargar_datos_historias(ruta_json="inputs.opt2.json"):
    """
    Carga los elementos de construcción de historias desde un archivo JSON externo.
    
    Args:
        ruta_json (str): Ruta al archivo JSON (relativa o absoluta)
        
    Returns:
        dict: Diccionario con todos los elementos cargados
        
    Raises:
        FileNotFoundError: Si el archivo JSON no existe
        json.JSONDecodeError: Si el JSON es inválido
    """
    
    # Convertir a Path para mejor manejo de rutas
    archivo_json = Path(ruta_json)
    
    # Si es ruta relativa, buscar en el mismo directorio que el script
    if not archivo_json.is_absolute():
        archivo_json = Path(__file__).parent / archivo_json
    
    if not archivo_json.exists():
        raise FileNotFoundError(f"❌ No se encontró el archivo: {archivo_json}")
    
    try:
        with open(archivo_json, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        
        # Extraer datos del contenedor 'construccionHistorias'
        contenedor = datos.get('construccionHistorias', {})
        
        # Validar que existan todos los elementos necesarios
        elementos_requeridos = [
            'sentimientos', 'moralejas', 'objetosCotidianos', 'objetosMagicos',
            'colores', 'lugares', 'personajesSecundarios', 'fenomenosNaturales',
            'desafios', 'accionesClaves'
        ]
        
        faltantes = [elem for elem in elementos_requeridos if elem not in contenedor]
        if faltantes:
            raise ValueError(f"❌ Faltan elementos en el JSON: {faltantes}")
        
        print("✅ Datos cargados correctamente desde:", archivo_json)
        return contenedor
        
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"❌ JSON inválido en {archivo_json}: {e.msg}", e.doc, e.pos)


# Cargar datos globales al iniciar
try:
    DATOS_HISTORIAS = cargar_datos_historias()
except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
    print(f"\n{e}\n")
    exit(1)


# ========================================
# GENERADOR DE ELEMENTOS ALEATORIOS
# ========================================

def generar_elementos_historia():
    """
    Genera una combinación aleatoria de elementos para la historia.
    
    Returns:
        dict: Diccionario con elementos seleccionados
    """
    
    elementos = {
        "lugar": random.choice(DATOS_HISTORIAS['lugares']),
        "objeto_principal": random.choice(DATOS_HISTORIAS['objetosCotidianos']),
        "color_objeto": random.choice(DATOS_HISTORIAS['colores']),
        "objeto_magico": random.choice(DATOS_HISTORIAS['objetosMagicos']),
        "personaje_secundario": random.choice(DATOS_HISTORIAS['personajesSecundarios']),
        "sentimiento_kira": random.choice(DATOS_HISTORIAS['sentimientos']),
        "sentimiento_toby": random.choice(DATOS_HISTORIAS['sentimientos']),
        "fenomeno": random.choice(DATOS_HISTORIAS['fenomenosNaturales']),
        "desafio": random.choice(DATOS_HISTORIAS['desafios']),
        "accion_kira": random.choice(DATOS_HISTORIAS['accionesClaves']),
        "accion_toby": random.choice(DATOS_HISTORIAS['accionesClaves']),
        "moraleja": random.choice(DATOS_HISTORIAS['moralejas'])
    }
    
    return elementos


# ========================================
# FUNCIONES DE ALMACENAMIENTO
# ========================================

def extraer_titulo_historia(contenido_historia):
    """
    Extrae el título de la historia desde el contenido generado.
    Busca el patrón: **TÍTULO:** [Nombre]
    
    Args:
        contenido_historia (str): Contenido completo de la historia
        
    Returns:
        str: Título limpio y formateado para usar en nombre de archivo
    """
    # Buscar el patrón **TÍTULO:** seguido del nombre
    match = re.search(r'\*\*TÍTULO:\*\*\s*(.+?)(?:\n|\*\*)', contenido_historia)
    if match:
        titulo = match.group(1).strip()
        # Reemplazar espacios y caracteres especiales por guiones bajos
        titulo = re.sub(r'[^a-záéíóúñA-ZÁÉÍÓÚÑ0-9]', '_', titulo)
        return titulo
    return "Historia_Sin_Titulo"


def extraer_escenas_historia(contenido_historia):
    """
    Extrae las descripciones de escenas del contenido generado.
    Busca la sección **ESCENAS:** y extrae cada línea numerada.
    
    Args:
        contenido_historia (str): Contenido completo de la historia
        
    Returns:
        list: Lista de descripciones de escenas
    """
    escenas = []
    # Buscar la sección ESCENAS: y extraer cada línea
    match = re.search(r'\*\*ESCENAS:\*\*(.+?)(?:\n\n|$)', contenido_historia, re.DOTALL)
    if match:
        texto_escenas = match.group(1)
        # Extraer líneas numeradas
        lineas = re.findall(r'\d+\.\s*(.+?)(?=\n\d+\.|$)', texto_escenas, re.DOTALL)
        escenas = [linea.strip() for linea in lineas if linea.strip()]
    return escenas


def generar_prompt_imagen_escena(num_escena, descripcion_escena, historia_dict):
    """
    Genera un prompt en español para generar una imagen de la escena.
    Sigue el estilo de película animada cinématica para audiencia infantil.
    
    Args:
        num_escena (int): Número de la escena
        descripcion_escena (str): Descripción de la escena
        historia_dict (dict): Diccionario con información de la historia
        
    Returns:
        str: Prompt para generar imagen
    """
    lugar = historia_dict.get("elementos", {}).get("lugar", "escena mágica")
    color_obj = historia_dict.get("elementos", {}).get("color_objeto", "mágico")
    objeto = historia_dict.get("elementos", {}).get("objeto_principal", "objeto")
    personaje_sec = historia_dict.get("elementos", {}).get("personaje_secundario")
    bloque_identidad = obtener_identidad_visual(personaje_sec)

    
    prompt = f"""Escena cinematográfica de película animada.

Estilo: Similar a una película de animación 3D de alta calidad, mágica y acogedora.

Escena {num_escena}: {descripcion_escena}

Lugar: {lugar} con iluminación cálida de hora dorada, luz suave y soñadora. El viento mueve suavemente el pasto y las flores.

Personaje secundario:
{personaje_sec}

{bloque_identidad}

Personajes: 
- Kira (perrita): Energética y expresiva, con postura confiada y movimientos animados.

Carácterísticas visuales de Kira:
- Body color: uniform pastel light yellow fur, hex code #FFF9D4, matte finish, no gradients
- Head shape: perfectly round, 1.5 times larger than body
- Eyes: extremely oversized dark brown eyes (hex #5C4033), occupying 40% of face width, three white circular highlights per eye positioned at 10 o'clock, perfectly symmetrical
- Nose: small black triangular nose (hex #2C2C2C), centered below eyes, glossy finish
- Mouth: simple curved line forming "w" shape, subtle friendly smile
- Ears: medium-sized rounded floppy ears, slightly drooping forward, same yellow as body
- Distinctive mark: small heart-shaped spot on RIGHT CHEEK ONLY, peach orange color (hex #FFB380), 15% size of head
- Tail: fluffy curled tail pointing upward, same yellow as body, 0.8x body length
- Body: compact rounded torso, no visible muscle definition, simplified smooth shapes
- Legs: four short stubby legs, rounded paws, no visible toes, each leg 0.3x body height
- Proportions: head to body ratio exactly 1:1.5

- Toby (perrito): Ligeramente más pequeño, pensativo, con ojos curiosos y gestos observadores.

Carácterísticas visuales de Toby:
PHYSICAL DESCRIPTION:
- Color distribution: 
  * Main body (back, sides, head top): soft lavender-gray fur, hex code #E8E3F0, matte finish
  * Face mask (muzzle, chin): white/cream colored, hex #FDFBF7
  * Chest and belly: light lavender-white fur, hex #F5F3F8
  * Neck mane: slightly darker lavender, hex #D4C9E0
  * All color transitions soft and natural, no hard edges
- Head shape: perfectly round, 1.5 times larger than body
- Eyes: HETEROCHROMIA - left eye bright blue (hex #6BB6D6), right eye warm brown (hex #8B6F47), both extremely oversized occupying 40% of face width, three white circular highlights per eye at 10 o'clock, perfectly symmetrical in size and shape
- Nose: small black triangular nose (hex #2C2C2C), centered below eyes, glossy finish
- Mouth: simple curved line forming "w" shape, subtle friendly smile
- Ears: medium-sized rounded triangular ears, standing upright with slight forward tilt
- Distinctive marks: 
  * Primary: White facial mask (hex #FDFBF7) covering lower muzzle, chin, and extending to upper chest in natural Husky pattern
  * Secondary: Lightning bolt shape on LEFT SIDE of body (visible on left flank), baby blue color (hex #A8D8EA), zigzag pattern with 3 points, 25% length of body height
- Neck mane: fluffy collar-like fur around neck, slightly darker lavender (hex #D4C9E0), 1.5x thickness of body fur, covers upper chest area, highly visible volume
- Tail: fluffy straight tail with slight upward curve, same lavender-gray as main body, 0.9x body length
- Body: compact rounded torso, no visible muscle definition, simplified smooth shapes
- Legs: four short stubby legs, rounded paws, no visible toes, each leg 0.3x body height
- Proportions: head to body ratio exactly 1:1.5


NEGATIVE PROMPTS (DO NOT INCLUDE):
- Multiple spots or patterns beyond the single heart on right cheek
- Sharp teeth, claws, or aggressive features
- Adult proportions, long legs, thin body
- Saturated bright colors, neon, rainbow
- Multiple characters, humans, other animals
- Complex backgrounds, grass, sky, objects
- Anime style, 2D flat art





- Objeto destacado: {objeto} de color {color_obj}

Atmósfera: Calorosa, mágica y envolvente. Música orquestal suave, tono caprichoso y aventurero.

Calidad técnica: Cinemática, animación altamente detallada, movimientos suaves y dinámicos, iluminación cinematográfica, profundidad de campo, 4K, atmósfera emotiva y edificante.

Perfecto para una audiencia infantil.


IMPORTANT:
MANTENER EXACTAMENTE EL MISMO DISEÑO DEL PERSONAJE EN TODAS LAS ESCENAS.
NO reinterpretar.
NO rediseñar.
NO cambiar proporciones."""
    
    return prompt


def generar_prompt_video_escena(num_escena, descripcion_escena, historia_dict):
    """
    Genera un prompt en español para generar un video de la escena.
    
    Args:
        num_escena (int): Número de la escena
        descripcion_escena (str): Descripción de la escena
        historia_dict (dict): Diccionario con información de la historia
        
    Returns:
        str: Prompt para generar video
    """
    lugar = historia_dict.get("elementos", {}).get("lugar", "escena mágica")
    
    prompt = f"""VIDEO ANIMADO - Escena {num_escena}

Descripción: {descripcion_escena}

Duración: 15-30 segundos

Estilo: Película animada 3D de alta calidad, dirigida a audiencia infantil.

Locación: {lugar}

Personajes en movimiento:
- Kira y Toby interactuando de forma dinámica y expresiva
- Movimientos fluidos y naturales
- Expresiones faciales emotivas

Elementos de cámara:
- Transiciones suaves
- Zoom progresivo cuando es necesario
- Movimiento de cámara envolvente
- Enfoque sobre momentos clave

Sonido:
- Música de fondo: orquestal, suave y aventurera
- Efectos de sonido: subtiles y mágicos
- Diálogos: cortos y claros (si aplica)

Iluminación: Cálida, dorada, mágica. Profundidad y realismo.

Qualidad: 4K, animación suave, atmósfera emotiva y edificante."""
    
    return prompt


def guardar_escenas_markdown(titulo, escenas, historia_dict):
    """
    Crea archivos markdown para cada escena con prompts de imagen y video.
    
    Args:
        titulo (str): Título formateado de la historia
        escenas (list): Lista de descripciones de escenas
        historia_dict (dict): Diccionario con información de la historia
        
    Returns:
        list: Lista de rutas de archivos creados
    """
    rutas_creadas = []
    
    try:
        # Crear carpeta prompts-scenas
        ruta_prompts = historia_dict["ruta_historia_dir"] / "prompts-scenas"
        ruta_prompts.mkdir(parents=True, exist_ok=True)
        
        # Crear archivo para cada escena
        for num_escena, descripcion_escena in enumerate(escenas, 1):
            nombre_archivo = f"escena{num_escena}.md"
            ruta_archivo = ruta_prompts / nombre_archivo
            
            # Generar prompts
            prompt_imagen = generar_prompt_imagen_escena(num_escena, descripcion_escena, historia_dict)
            prompt_video = generar_prompt_video_escena(num_escena, descripcion_escena, historia_dict)
            
            # Contenido del archivo markdown
            contenido_md = f"""# Escena {num_escena}

## Descripción de la Escena
{descripcion_escena}

---

## 🎬 Prompt para Generar Imagen

{prompt_imagen}

---

## 🎥 Prompt para Generar Video

{prompt_video}

---

"""
            
            # Guardar archivo
            with open(ruta_archivo, 'w', encoding='utf-8') as f:
                f.write(contenido_md)
            
            rutas_creadas.append(ruta_archivo)
            print(f"  ✅ {nombre_archivo} creado")
        
        return rutas_creadas
        
    except Exception as e:
        print(f"❌ Error al guardar escenas markdown: {e}")
        return []


def guardar_historia(historia_dict, carpeta_salida="outputs/historias/revision"):
    """
    Guarda la historia generada en una estructura de carpetas organizada.
    Crea: TITULO/TITULO-YYYYMMDD-HHMMSS.txt y TITULO/prompts-scenas/escenaN.md
    
    Args:
        historia_dict (dict): Diccionario con la historia generada
        carpeta_salida (str): Ruta de salida base (relativa o absoluta)
        
    Returns:
        dict: Información sobre archivos guardados
    """
    try:
        # Extraer el contenido
        contenido = historia_dict.get("historia", "")
        
        # Extraer título y generar timestamp
        titulo = extraer_titulo_historia(contenido)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        
        # Crear ruta de carpeta por título
        ruta_base = Path(__file__).parent.parent / carpeta_salida
        ruta_historia_dir = ruta_base / titulo
        ruta_historia_dir.mkdir(parents=True, exist_ok=True)
        
        # Crear nombre de archivo
        nombre_archivo = f"{titulo}-{timestamp}.txt"
        ruta_archivo = ruta_historia_dir / nombre_archivo
        
        # Preparar contenido a guardar
        contenido_final = f"""{'='*80}
HISTORIA GENERADA - KIRA Y TOBY
{'='*80}
Fecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*80}

{contenido}

{'='*80}
ELEMENTOS UTILIZADOS:
{'='*80}
"""
        
        # Agregar elementos
        elementos = historia_dict.get("elementos", {})
        for key, value in elementos.items():
            contenido_final += f"  {key}: {value}\n"
        
        # Agregar tokens si está disponible
        if "tokens" in historia_dict:
            contenido_final += f"\n📊 Tokens utilizados: {historia_dict['tokens']}"
        
        # Guardar archivo principal
        with open(ruta_archivo, 'w', encoding='utf-8') as f:
            f.write(contenido_final)
        
        print(f"\n✅ Historia guardada en: {ruta_archivo}")
        
        # Extraer escenas y guardar archivos markdown
        escenas = extraer_escenas_historia(contenido)
        
        if escenas:
            print(f"\n📝 Generando {len(escenas)} archivos de escenas...")
            historia_dict["ruta_historia_dir"] = ruta_historia_dir
            rutas_escenas = guardar_escenas_markdown(titulo, escenas, historia_dict)
            print(f"\n✅ Carpeta de escenas creada en: {ruta_historia_dir}/prompts-scenas")
        else:
            print("⚠️ No se extrajeron escenas")
        
        return {
            "ruta_historia": str(ruta_archivo),
            "ruta_directorio": str(ruta_historia_dir),
            "titulo": titulo,
            "timestamp": timestamp
        }
        
    except Exception as e:
        print(f"\n❌ Error al guardar la historia: {e}")
        return None


# ========================================
# FUNCIONES PRINCIPALES
# ========================================

def generar_historia_aleatoria():
    """
    Genera una historia completamente aleatoria combinando elementos del JSON.
    
    Returns:
        dict: Historia generada + elementos usados
    """
    
    # Generar elementos aleatorios
    elementos = generar_elementos_historia()
    
    # Crear prompt con elementos
    prompt = PROMPT_TEMPLATE.format(**elementos)
    
    print("🎲 ELEMENTOS SELECCIONADOS:")
    print("=" * 60)
    for key, value in elementos.items():
        print(f"  {key}: {value}")
    print("=" * 60)
    print("\n⏳ Generando historia...\n")
    
    try:
        response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": PROMPT_TEMPLATE.format(**elementos)}
        ],
        temperature=0.9,
        max_tokens=1500
        )
        
        historia = response.choices[0].message.content
        
        return {
            "historia": historia,
            "elementos": elementos,
            "tokens": response.usage.total_tokens
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "elementos": elementos
        }


# def generar_multiples_historias(cantidad=5):
#     """
#     Genera múltiples historias aleatorias.
    
#     Args:
#         cantidad (int): Número de historias a generar
        
#     Returns:
#         list: Lista de historias generadas
#     """
    
#     historias = []
    
#     for i in range(1, cantidad + 1):
#         print(f"\n{'='*60}")
#         print(f"📖 GENERANDO HISTORIA {i}/{cantidad}")
#         print(f"{'='*60}\n")
        
#         resultado = generar_historia_aleatoria()
#         historias.append(resultado)
        
#         if "historia" in resultado:
#             print("\n" + resultado["historia"])
#             print(f"\n📊 Tokens usados: {resultado['tokens']}")
#         else:
#             print(f"\n❌ Error: {resultado['error']}")
        
#         print("\n" + "="*60)
    
#     return historias


# ========================================
# EJECUCIÓN
# ========================================

if __name__ == "__main__":
    print("🐶 GENERADOR ALEATORIO DE HISTORIAS - KIRA Y TOBY")
    print("📂 Cargando datos desde: inputs.opt2.json\n")
    
    # Opción 1: Historia única aleatoria
    print("Generando historia con elementos aleatorios...\n")
    
    resultado = generar_historia_aleatoria()
    
    if "historia" in resultado:
        print("\n" + "="*60)
        print(resultado["historia"])
        print("="*60)
        print(f"\n📊 Tokens: {resultado['tokens']}")
        
        # Guardar la historia en archivo y generar escenas
        resultado_guardado = guardar_historia(resultado)
        if resultado_guardado:
            print(f"\n🎉 Proceso completado exitosamente")
            print(f"   📂 Directorio: {resultado_guardado['ruta_directorio']}")
    
    # Opción 2: Múltiples historias (descomentar para usar)
    """
    print("\n\n🎲 ¿Generar múltiples historias aleatorias?")
    cantidad = int(input("¿Cuántas historias? (1-10): "))
    
    historias = generar_multiples_historias(cantidad)
    
    print(f"\n✅ {len(historias)} historias generadas exitosamente")
    """
