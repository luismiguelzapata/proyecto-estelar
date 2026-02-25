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


def guardar_historia(historia_dict, carpeta_salida="outputs/historias/revision"):
    """
    Guarda la historia generada en un archivo con nombre basado en el título y timestamp.
    Formato: TITULO-YYYYMMDD-HHMMSS.txt
    
    Args:
        historia_dict (dict): Diccionario con la historia generada
        carpeta_salida (str): Ruta de salida (relativa o absoluta)
        
    Returns:
        Path: Ruta del archivo guardado, o None si hubo error
    """
    try:
        # Crear ruta absoluta
        ruta_salida = Path(__file__).parent.parent / carpeta_salida
        ruta_salida.mkdir(parents=True, exist_ok=True)
        
        # Extraer el contenido
        contenido = historia_dict.get("historia", "")
        
        # Extraer título y generar timestamp
        titulo = extraer_titulo_historia(contenido)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        
        # Crear nombre de archivo
        nombre_archivo = f"{titulo}-{timestamp}.txt"
        ruta_archivo = ruta_salida / nombre_archivo
        
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
        
        # Guardar archivo
        with open(ruta_archivo, 'w', encoding='utf-8') as f:
            f.write(contenido_final)
        
        print(f"\n✅ Historia guardada en: {ruta_archivo}")
        return ruta_archivo
        
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


def generar_multiples_historias(cantidad=5):
    """
    Genera múltiples historias aleatorias.
    
    Args:
        cantidad (int): Número de historias a generar
        
    Returns:
        list: Lista de historias generadas
    """
    
    historias = []
    
    for i in range(1, cantidad + 1):
        print(f"\n{'='*60}")
        print(f"📖 GENERANDO HISTORIA {i}/{cantidad}")
        print(f"{'='*60}\n")
        
        resultado = generar_historia_aleatoria()
        historias.append(resultado)
        
        if "historia" in resultado:
            print("\n" + resultado["historia"])
            print(f"\n📊 Tokens usados: {resultado['tokens']}")
        else:
            print(f"\n❌ Error: {resultado['error']}")
        
        print("\n" + "="*60)
    
    return historias


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
        
        # Guardar la historia en archivo
        guardar_historia(resultado)
    
    # Opción 2: Múltiples historias (descomentar para usar)
    """
    print("\n\n🎲 ¿Generar múltiples historias aleatorias?")
    cantidad = int(input("¿Cuántas historias? (1-10): "))
    
    historias = generar_multiples_historias(cantidad)
    
    print(f"\n✅ {len(historias)} historias generadas exitosamente")
    """
