"""
EJEMPLO: Generar 3 vistas de personajes

Este archivo demuestra cómo usar la nueva función de generación de 3 vistas
para personajes con diferentes ángulos de cámara.
"""

from modules.image_generator import (
    generar_tres_vistas_personaje,
    generar_imagen_personaje,
    POSES_PERSONAJE
)
from modules.data_loader import cargar_datos_historias

# ========================================
# EJEMPLO 1: Generar 3 vistas automáticamente
# ========================================

def ejemplo_tres_vistas():
    """Genera 3 vistas de un personaje utilizando su prompt-3D"""
    
    # Cargar datos
    datos = cargar_datos_historias()
    personajes = datos.get('personajesSecundarios', [])
    
    # Seleccionar un personaje con prompt-3D
    personaje = personajes[0]  # conejito blanco
    
    if isinstance(personaje, dict) and 'prompt-3D' in personaje:
        nombre = personaje['nombre']
        prompt = personaje['prompt-3D']
        
        print(f"🎨 Generando 3 vistas para: {nombre}\n")
        
        # Generar 3 vistas (front, side, quarter)
        vistas = generar_tres_vistas_personaje(nombre, prompt)
        
        # Mostrar resultados
        print(f"\n📊 Resultados:")
        for vista_key, ruta in vistas.items():
            if ruta:
                print(f"  ✅ {POSES_PERSONAJE[vista_key]['nombre']}: {ruta}")
            else:
                print(f"  ❌ {POSES_PERSONAJE[vista_key]['nombre']}: No se generó")


# ========================================
# EJEMPLO 2: Generar 3 vistas a través de generar_imagen_personaje()
# ========================================

def ejemplo_generar_persona_con_vistas():
    """Usa generar_imagen_personaje() con flag generar_tres_vistas=True"""
    
    datos = cargar_datos_historias()
    personajes = datos.get('personajesSecundarios', [])
    
    # Seleccionar personaje
    personaje = personajes[1]  # ardilla energética
    
    if isinstance(personaje, dict) and 'prompt-3D' in personaje:
        print(f"🎨 Generando personaje: {personaje['nombre']}\n")
        
        # Opción 1: Generar 3 vistas (por defecto)
        vistas = generar_imagen_personaje(personaje, generar_tres_vistas=True)
        print(f"✅ Generadas {len([v for v in vistas.values() if v])} vistas")
        
        # Opción 2: Generar solo 1 vista
        # imagen_unica = generar_imagen_personaje(personaje, generar_tres_vistas=False)


# ========================================
# EJEMPLO 3: Personalizar las poses
# ========================================

def ver_poses_disponibles():
    """Muestra las poses disponibles"""
    
    print("📸 Poses disponibles para personajes:\n")
    
    for key, info in POSES_PERSONAJE.items():
        print(f"  {key.upper()}")
        print(f"    Nombre: {info['nombre']}")
        print(f"    Descripción: {info['descripcion']}")
        print(f"    Archivo: {info['archivo']}\n")


# ========================================
# ESTRUCTURA DE CARPETAS GENERADA
# ========================================

"""
El resultado después de generar 3 vistas será:

assets/personajes/
├── conejito-blanco/
│   ├── front.jpg       (vista frontal)
│   ├── side.jpg        (vista de perfil derecho)
│   └── quarter.jpg     (vista 3/4)
├── ardilla-energetica/
│   ├── front.jpg
│   ├── side.jpg
│   └── quarter.jpg
└── ...otros personajes

Cada imagen tendrá el prompt específico con su pose:
- front: "centered composition"
- side: "right side profile view, full body visible from nose to tail tip"
- quarter: "three-quarter view at 45-degree angle, full body visible, looking slightly toward camera"
"""


# ========================================
# EJECUTAR EJEMPLOS
# ========================================

if __name__ == "__main__":
    print("=" * 70)
    print("EJEMPLOS: Generación de 3 vistas de personajes")
    print("=" * 70)
    
    # Ver poses disponibles
    print("\n1️⃣ POSES DISPONIBLES")
    print("-" * 70)
    ver_poses_disponibles()
    
    # Descomentar para ejecutar ejemplos reales (requiere GOOGLE_API_KEY):
    
    # print("\n2️⃣ GENERAR 3 VISTAS (función directa)")
    # print("-" * 70)
    # ejemplo_tres_vistas()
    
    # print("\n3️⃣ GENERAR A TRAVÉS DE generar_imagen_personaje()")
    # print("-" * 70)
    # ejemplo_generar_persona_con_vistas()
    
    print("\n" + "=" * 70)
    print("ℹ️  Para ejecutar ejemplos reales, descomentar las funciones")
    print("   y configurar tu GOOGLE_API_KEY en .env")
    print("=" * 70)
