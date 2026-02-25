
import random
from openai import OpenAI

client = OpenAI()

# ========================================
# BASE DE DATOS DE ELEMENTOS
# ========================================

SENTIMIENTOS = [
    "curioso", "emocionado", "sorprendido", "preocupado", "alegre", 
    "confundido", "valiente", "nervioso", "orgulloso", "asombrado",
    "determinado", "pensativo", "feliz", "intrigado", "esperanzado",
    "cansado", "entusiasmado", "frustrado", "tranquilo", "maravillado"
]

MORALEJAS = [
    "juntos somos más fuertes",
    "cada uno tiene algo especial que aportar",
    "observar con atención antes de actuar",
    "la paciencia trae grandes recompensas",
    "las diferencias nos hacen mejores amigos",
    "pensar diferente resuelve problemas difíciles",
    "ayudar a otros nos hace felices",
    "escuchar es tan importante como hablar",
    "los pequeños detalles importan mucho",
    "el coraje crece cuando tienes buenos amigos",
    "compartir multiplica la alegría",
    "ser valiente es seguir adelante aunque tengas miedo",
    "las mejores ideas vienen del trabajo en equipo",
    "confiar en tus amigos te hace más fuerte",
    "cuidar la naturaleza es cuidar nuestro hogar"
]

OBJETOS_COTIDIANOS = [
    "pelota", "cuerda", "campana", "espejo", "libro", "mapa", "linterna",
    "caja", "llave", "brújula", "bufanda", "sombrero", "cesta", "red",
    "pala", "cubo", "silbato", "bandera", "reloj", "carta", "piedra",
    "concha", "pluma", "botella", "collar"
]

OBJETOS_MAGICOS = [
    "semillas brillantes", "polvo de estrellas", "piedra que cambia de color",
    "flor que canta", "cristal luminoso", "espejo que muestra recuerdos",
    "campana dorada que suena sola", "pluma iridiscente", "caracola que susurra",
    "llave de luz", "cuerda infinita", "mapa que se dibuja solo",
    "piedras que flotan", "flores que brillan en la oscuridad",
    "agua que cambia de color", "hoja que nunca cae", "corona de nubes",
    "brújula que señala lo importante", "lágrimas de cristal", "puente de arcoíris"
]

COLORES = [
    "rojo", "azul", "amarillo", "verde", "morado", "naranja", "rosa",
    "dorado", "plateado", "turquesa", "violeta", "blanco brillante",
    "negro profundo", "coral", "lavanda"
]

LUGARES = [
    "parque junto al río", "bosque de árboles altos", "jardín secreto",
    "colina con flores", "cueva luminosa", "claro del bosque",
    "orilla del lago", "puente de piedra", "pradera dorada",
    "montaña pequeña", "valle escondido", "arroyo cristalino",
    "campo de amapolas", "bosque de bambú", "cascada plateada",
    "playa tranquila", "roca gigante", "túnel de árboles",
    "isla en el río", "sendero del arcoíris"
]

PERSONAJES_SECUNDARIOS = [
    "conejito blanco", "ardilla mensajera", "búho sabio",
    "mariposa brillante", "pájaro cantor", "tortuga anciana",
    "zorro amigable", "ratoncito tímido", "gato elegante",
    "pato gracioso", "erizo curioso", "libélula veloz",
    "rana saltarina", "castor constructor", "luciérnaga luminosa"
]

FENOMENOS_NATURALES = [
    "arcoíris después de la lluvia", "niebla misteriosa", "viento suave",
    "rayos de sol entre nubes", "rocío brillante en la mañana",
    "hojas cayendo", "nieve ligera", "reflejos en el agua",
    "sombras danzantes", "eco en el valle", "aurora en el cielo",
    "estrellas fugaces", "luna llena brillante", "nubes con formas",
    "cascada de luz"
]

DESAFIOS = [
    "algo desapareció misteriosamente", "alguien necesita ayuda urgente",
    "un camino está bloqueado", "algo dejó de funcionar",
    "un sonido extraño se escucha", "alguien perdió algo importante",
    "algo cambió de lugar solo", "un mensaje cifrado aparece",
    "una puerta está cerrada", "algo brillante está atrapado",
    "un puente está roto", "alguien está perdido",
    "algo está al revés", "un patrón se rompió", "algo no encaja",
    "una señal es confusa", "algo está escondido",
    "un camino tiene múltiples opciones", "algo creció de repente",
    "un reflejo muestra algo diferente"
]

ACCIONES_CLAVE = [
    "descubren", "encuentran", "escuchan", "siguen", "observan",
    "tocan", "huelen", "saltan sobre", "excavan cerca de",
    "atraviesan", "rodean", "se acercan a", "miran dentro de",
    "recogen", "organizan", "conectan", "desenredan", "reparan",
    "construyen", "transforman"
]


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
        "lugar": random.choice(LUGARES),
        "objeto_principal": random.choice(OBJETOS_COTIDIANOS),
        "color_objeto": random.choice(COLORES),
        "objeto_magico": random.choice(OBJETOS_MAGICOS),
        "personaje_secundario": random.choice(PERSONAJES_SECUNDARIOS),
        "sentimiento_kira": random.choice(SENTIMIENTOS),
        "sentimiento_toby": random.choice(SENTIMIENTOS),
        "fenomeno": random.choice(FENOMENOS_NATURALES),
        "desafio": random.choice(DESAFIOS),
        "accion_kira": random.choice(ACCIONES_CLAVE),
        "accion_toby": random.choice(ACCIONES_CLAVE),
        "moraleja": random.choice(MORALEJAS)
    }
    
    return elementos


# ========================================
# PROMPT DINÁMICO
# ========================================

PROMPT_TEMPLATE = """
Eres un narrador profesional especializado en crear historias para niños de 3-6 años. 
Tu tarea es escribir una historia protagonizada por dos perritos con personalidades 
complementarias, narrada con voz cálida y cercana, como si estuvieras contándola 
oralmente a niños reunidos en un círculo.

PROTAGONISTAS:

KIRA (La Perrita):
- Personalidad: Acción, liderazgo, energía, promotora de aventuras, optimista, valiente, decidida, entusiasta, dinámica, enérgica,  resiliente, proactiva, inspiradora, motivadora, audaz, segura de sí misma.
- Respuestas: "¡Vamos!" / "¡Podemos hacerlo!" / "¡Yo sé qué hacer!" / "¡Tengo una idea!" / "¡Sigamos adelante!" / "¡No hay tiempo que perder!" / "¡Esto es emocionante!" / "¡Lo intentemos!" / "¡Estoy lista para la aventura!" / "¡Juntos podemos lograrlo!"
- Rol: Motor de acción que impulsa la historia con su energía y entusiasmo

TOBY (El Perrito):
- Personalidad: Imaginación, creatividad, observación, curiosidad, reflexión, soñador, analítico, perceptivo, ingenioso, estratégico, intuitivo, detallista, pensativo, reflexivo, observador, imaginativo.
- Respuestas: "Espera... ¿y si...?" / "Mira esto..." / "Se me ocurre algo..." / "que podríamos..." / "¿y si intentamos...?" / "Noté algo interesante..." / "Tengo una idea diferente..." / "¿y si lo hacemos así?" / "Creo que podríamos..." / "Observa esto..." / "¿y si combinamos nuestras ideas?" / "Tengo una teoría..." / "¿y si pensamos en esto de otra manera?" / "Noté algo que podría ayudar..." / "¿y si usamos esto de una forma diferente?" 
- Rol: Estratega creativo que aporta ideas y soluciones a los desafíos

---

ELEMENTOS OBLIGATORIOS PARA ESTA HISTORIA:

ESCENARIO: {lugar}
OBJETO PRINCIPAL: {objeto_principal} de color {color_objeto}
ELEMENTO MÁGICO: {objeto_magico}
PERSONAJE SECUNDARIO: {personaje_secundario}
FENÓMENO NATURAL: {fenomeno}
DESAFÍO: {desafio}

EMOCIONES:
- Kira se siente: {sentimiento_kira}
- Toby se siente: {sentimiento_toby}

ACCIONES CLAVE:
- Kira debe: {accion_kira}
- Toby debe: {accion_toby}

MORALEJA OBJETIVO: {moraleja}

---

REQUISITOS:

1. Duración: 450-600 palabras (3-4 minutos lectura)
2. Tono: Activo, dinámico, enganchante, con lenguaje sencillo y directo, ideal para niños pequeños, con diálogos cortos y escenas visuales claras.
3. Estructura: Inicio rápido → Desafío → Colaboración → Éxito → Moraleja
4. Incorporar TODOS los elementos listados de manera natural
5. Diálogos cortos (máximo 8 palabras)
6. Máximo 8 escenas visuales diferenciadas

---

FORMATO DE ENTREGA:

**TÍTULO:** [Nombre atractivo]

**HISTORIA:**
[Texto completo]

**MORALEJA:**
[La lección: {moraleja}]

**ESCENAS:**
1. [Descripción escena 1]
2. [Descripción escena 2]
[...hasta 8]

---

GENERA LA HISTORIA AHORA.
"""


# ========================================
# FUNCIONES PRINCIPALES
# ========================================

def generar_historia_aleatoria():
    """
    Genera una historia completamente aleatoria combinando elementos.
    
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
                {"role": "system", "content": "Eres un narrador experto."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.9,  # Alta creatividad
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
    print("🐶 GENERADOR ALEATORIO DE HISTORIAS - KIRA Y TOBY\n")
    
    # Opción 1: Historia única aleatoria
    print("Generando historia con elementos aleatorios...\n")
    
    resultado = generar_historia_aleatoria()
    
    if "historia" in resultado:
        print("\n" + "="*60)
        print(resultado["historia"])
        print("="*60)
        print(f"\n📊 Tokens: {resultado['tokens']}")
    
    # Opción 2: Múltiples historias (descomentar para usar)
    """
    print("\n\n🎲 ¿Generar múltiples historias aleatorias?")
    cantidad = int(input("¿Cuántas historias? (1-10): "))
    
    historias = generar_multiples_historias(cantidad)
    
    print(f"\n✅ {len(historias)} historias generadas exitosamente")
    """

