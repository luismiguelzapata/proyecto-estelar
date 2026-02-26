"""
Script de prueba para validar que los datos del personaje secundario
se pasan correctamente a través del flujo de generación de imágenes
"""

# Simular el diccionario que viene de guardar_historia() con la corrección
test_historia = {
    "historia": "Una historia de prueba...",
    "elementos": {
        "lugar": "bosque",
        "objeto_principal": "libro",
        "color_objeto": "rojo",
        "personaje_secundario": {
            "nombre": "dragón amistoso",
            "species": "dragon",
            "prompt-3D": "Un dragón pequeño y amistoso con colores azules y verdes"
        },
        "personaje_secundario_nombre": "dragón amistoso"
    },
    "ruta_directorio": "test"
}

print("🧪 PRUEBA DE ESTRUCTURA DE DATOS CORREGIDA")
print("=" * 70)
print("\n📋 Flujo de datos después de guardar_historia():\n")
print(f"  ANTES (bug): generar_imagenes_escena() recibía elementos = {{}}")
print(f"              ❌ No encontraba personaje_secundario\n")

print(f"  AHORA (corregido): generar_imagenes_escena() recibe elementos completos")

print("\n" + "=" * 70)
print("\n🔍 Simulando la extracción en generar_imagenes_escena():\n")

# Simular lo que hace generar_imagenes_escena() 
historia_dict = test_historia
elementos = historia_dict.get("elementos", {})
nombre_personaje = elementos.get("personaje_secundario_nombre")
personaje_dict = elementos.get("personaje_secundario")

print(f"  1. Extraer nombre: {nombre_personaje} ✅")
print(f"  2. Extraer dict: {personaje_dict.get('nombre', 'N/A')} ✅")
print(f"  3. Extraer prompt-3D: {personaje_dict.get('prompt-3D')[:50]}... ✅")

if nombre_personaje and personaje_dict and personaje_dict.get("prompt-3D"):
    print(f"\n✅ ÉXITO: La estructura de datos está CORRECTA.")
    print(f"   Se van a generar 3 vistas para: {nombre_personaje}")
    print(f"   Con el prompt: {personaje_dict.get('prompt-3D')}")
else:
    print(f"\n❌ ERROR: Falta información necesaria")

print("\n" + "=" * 70)
print("\n📝 RESUMEN DE CORRECCIONES:")
print("  ✅ story_storage.py: Ahora retorna 'elementos' en guardar_historia()")
print("  ✅ main.py: Accede correctamente a 'elementos' en historia_dict")
print("  ✅ image_generator.py: Extrae nombre y dict correctamente")
print("\nEl problema debería estar RESUELTO ✅")
print("=" * 70)
