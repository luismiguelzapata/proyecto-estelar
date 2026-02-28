from openai import OpenAI
import os

client = OpenAI()

# ========================================
# PROMPT MAESTRO - KIRA Y TOBY
# ========================================

PROMPT_MAESTRO = """
Eres un narrador profesional especializado en crear historias para niños de 3-6 años. 
Tu tarea es escribir una historia protagonizada por dos perritos con personalidades 
complementarias, narrada con voz cálida y cercana, como si estuvieras contándola 
oralmente a niños reunidos en un círculo.

PROTAGONISTAS:

KIRA (La Perrita):
- Personalidad: Acción, liderazgo, energía solar
- Atributos: Valiente, decidida, optimista, toma iniciativa
- Rol en la historia: Motor de acción, quien propone aventuras
- Respuestas típicas: "¡Vamos! ¡Podemos hacerlo!" / "¡Yo sé qué hacer!"
- Fortaleza: Valor para enfrentar desafíos físicos
- Debilidad: A veces actúa antes de pensar

TOBY (El Perrito):
- Personalidad: Imaginación, creatividad, exploración lunar
- Atributos: Reflexivo, curioso, observador, soñador
- Rol en la historia: Estratega, quien nota detalles ocultos
- Respuestas típicas: "Espera... ¿y si...?" / "Hay algo diferente aquí..."
- Fortaleza: Capacidad de ver soluciones creativas
- Debilidad: A veces duda antes de actuar

DINÁMICA ENTRE ELLOS:
- Kira impulsa la acción → Toby aporta la estrategia
- Toby observa detalles → Kira ejecuta el plan
- Se complementan: ninguno puede resolver el problema solo
- Su amistad es el núcleo emocional de cada historia

---

ESTRUCTURA NARRATIVA OBLIGATORIA:

1. INICIO ACTIVO (30 segundos de lectura):
   - Kira y Toby en acción inmediata (jugando, corriendo, explorando)
   - Algo llama su atención o interrumpe su actividad
   - Gancho visual fuerte (algo misterioso, brillante, diferente)
   - Tono: Dinámico, enérgico, inmediato

2. LLAMADO A LA AVENTURA (30 segundos):
   - Descubren algo que despierta curiosidad
   - Kira propone investigar/ayudar sin dudar
   - Toby nota un detalle importante
   - Decisión conjunta de actuar

3. DESAFÍO CENTRAL (1 minuto):
   - Problema que requiere AMBAS personalidades
   - Kira intenta con acción → éxito parcial o falla
   - Toby observa/imagina algo clave → no puede hacerlo solo
   - Momento breve de frustración (superado rápido)

4. COLABORACIÓN Y DESCUBRIMIENTO (1 minuto):
   - Combinan acción de Kira + creatividad de Toby
   - Proceso visual paso a paso
   - Momento "¡Eureka!" cuando funciona
   - Emoción compartida del éxito

5. RESOLUCIÓN Y APRENDIZAJE (30 segundos):
   - Éxito de la misión
   - Reflexión breve sobre qué aprendieron
   - Reconocimiento mutuo
   - Momento cálido de amistad

6. MORALEJA CLARA (30 segundos):
   - Lección explícita pero no sermoneadora
   - Aplicable a la vida de los niños
   - Formulada de manera memorable
   - Cierre inspirador

---

REQUISITOS TÉCNICOS:

DURACIÓN:
- Total: 3-4 minutos de lectura en voz alta
- Aproximadamente 450-600 palabras
- 15-20 oraciones máximo

TONO NARRATIVO:
- Activo y dinámico, no poético ni descriptivo
- Diálogos cortos y expresivos (5-8 palabras máximo)
- Verbos de acción: correr, saltar, brillar, descubrir
- Evitar descripciones largas o lentas
- Ritmo ágil que mantiene atención

ELEMENTOS VISUALES:
- Cada acción debe ser fácil de animar
- Máximo 8 escenas diferenciadas
- Descripciones concretas y visuales
- Micro-acciones expresivas (cola, orejas, saltos)

EMOCIONES PERMITIDAS:
- Alegría, sorpresa, curiosidad, determinación
- Frustración momentánea (superada rápido)
- Orgullo, gratitud, emoción por logro

TEMAS APROPIADOS:
✅ Amistad, colaboración, complementariedad
✅ Descubrimiento, misterio, aventura
✅ Ayudar a otros, resolver problemas
✅ Naturaleza, magia sutil, elementos brillantes

TEMAS PROHIBIDOS:
❌ Peligro real, miedo intenso, amenazas
❌ Tristeza profunda, pérdida, abandono
❌ Conflicto entre Kira y Toby
❌ Engaños o mentiras

---

FORMATO DE ENTREGA:

**TÍTULO:** [Nombre atractivo de la aventura]

**ESCENARIO:** [1 frase describiendo dónde ocurre]

**HISTORIA:**
[Texto completo sin divisiones visibles]

**MORALEJA:**
[1-2 frases con la lección]

**DIVISIÓN DE ESCENAS:**
Escena 1: [Descripción - 1 frase]
Escena 2: [Descripción - 1 frase]
[...hasta 8 escenas]

---

AHORA GENERA LA HISTORIA.

TEMA: {tema_especifico}
"""


def generar_historia(tema="aventura de descubrimiento en la naturaleza"):
    """
    Genera una historia de Kira y Toby usando el prompt maestro.
    
    Args:
        tema (str): Tema específico para la historia
        
    Returns:
        str: Historia completa generada
    """
    
    # Insertar el tema en el prompt maestro
    prompt_completo = PROMPT_MAESTRO.format(tema_especifico=tema)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",  # Corregido: usar gpt-4 o gpt-3.5-turbo
            messages=[
                {
                    "role": "system",
                    "content": "Eres un narrador experto en historias infantiles."
                },
                {
                    "role": "user",
                    "content": prompt_completo
                }
            ],
            temperature=0.8,  # Creatividad moderada-alta
            max_tokens=1500   # Suficiente para 600 palabras
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Error al generar historia: {str(e)}"


if __name__ == "__main__":
    print("🐶 GENERADOR DE HISTORIAS - KIRA Y TOBY\n")
    print("=" * 50)
    
    # Opción 1: Tema predefinido
    tema = "un puente mágico que aparece después de la lluvia"
    
    # Opción 2: Tema desde input del usuario (comentado por ahora)
    # tema = input("Ingresa el tema de la historia: ")
    
    print(f"\n📖 Generando historia con tema: {tema}\n")
    
    historia = generar_historia(tema)
    
    print(historia)
    print("\n" + "=" * 50)