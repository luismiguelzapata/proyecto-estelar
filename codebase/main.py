"""
MAIN.PY - Punto de entrada principal del proyecto Estelar

Orquesta la generación de historias, escenas e imágenes.
Este es el archivo que debes ejecutar para usar el sistema.
"""

import argparse
from pathlib import Path

# Imports del proyecto
from modules import (
    cargar_datos_historias,
    generar_historia_aleatoria,
    # generar_multiples_historias,
    guardar_historia,
    generar_imagen_personaje,
    generar_imagenes_escena,
    inicializar_generador,
    crear_imagen_placeholder
)
from config.config import ASSETS_PERSONAJES_DIR


def main():
    """Función principal con menú de opciones"""
    
    parser = argparse.ArgumentParser(
        description="🐶 Generador de Historias Animadas - Kira y Toby"
    )
    
    parser.add_argument(
        '--modo',
        choices=['historia', 'historias', 'imagen', 'completo'],
        default='historia',
        help='Modo de ejecución (default: historia)'
    )
    
    parser.add_argument(
        '--cantidad',
        type=int,
        default=1,
        help='Número de historias a generar (para modo historias)'
    )
    
    parser.add_argument(
        '--placeholder',
        action='store_true',
        help='Crear imágenes placeholder para testing (sin usar API)'
    )
    
    args = parser.parse_args()
    
    print("="*70)
    print("🐶 GENERADOR DE HISTORIAS ANIMADAS - KIRA Y TOBY")
    print("="*70)
    print()
    
    try:
        # Inicializar generador
        print("📚 Inicializando generador...\n")
        inicializar_generador()
        
        # Ejecutar según modo
        if args.modo == 'historia':
            ejecutar_historia_unica()
            
        elif args.modo == 'historias':
            ejecutar_multiples_historias(args.cantidad)
            
        elif args.modo == 'imagen':
            ejecutar_generador_imagenes(args.placeholder)
            
        elif args.modo == 'completo':
            ejecutar_modo_completo()
        
        print("\n✅ Proceso completado exitosamente")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        exit(1)


def ejecutar_historia_unica():
    """Genera una única historia aleatoria"""
    
    print("📖 Generando historia única...\n")
    
    resultado = generar_historia_aleatoria()
    
    if "historia" in resultado:
        print("\n" + "="*70)
        print(resultado["historia"])
        print("="*70)
        print(f"\n📊 Tokens utilizados: {resultado['tokens']}")
        
        # Guardar la historia
        print("\n💾 Guardando historia...\n")
        resultado_guardado = guardar_historia(resultado)
        
        if resultado_guardado:
            print(f"\n🎉 Historia guardada exitosamente")
            print(f"   📂 Directorio: {resultado_guardado['ruta_directorio']}")
            return resultado_guardado
    else:
        print(f"\n❌ Error: {resultado['error']}")
        return None


# def ejecutar_multiples_historias(cantidad: int):
#     """Genera múltiples historias aleatorias"""
    
#     if cantidad < 1 or cantidad > 10:
#         print("⚠️ Cantidad debe estar entre 1 y 10. Usando 5.")
#         cantidad = 5
    
#     print(f"📚 Generando {cantidad} historias...\n")
    
#     historias = generar_multiples_historias(cantidad)
    
#     # Guardar cada historia
#     print(f"\n💾 Guardando {len(historias)} historias...\n")
    
#     resultados_guardado = []
#     for i, historia in enumerate(historias, 1):
#         if "historia" in historia:
#             resultado = guardar_historia(historia)
#             if resultado:
#                 resultados_guardado.append(resultado)
#                 print(f"✅ Historia {i}/{cantidad} guardada")
#         else:
#             print(f"❌ Historia {i}/{cantidad} falló: {historia.get('error')}")
    
#     print(f"\n✅ {len(resultados_guardado)}/{cantidad} historias guardadas exitosamente")
#     return resultados_guardado


def ejecutar_generador_imagenes(usar_placeholder: bool = False):
    """Genera imágenes para personajes secundarios"""
    
    print("🎨 Generador de Imágenes de Personajes\n")
    
    try:
        datos = cargar_datos_historias()
        personajes = datos.get('personajesSecundarios', [])
        
        print(f"📊 Total de personajes: {len(personajes)}\n")
        
        generadas = 0
        errores = 0
        
        for personaje in personajes:
            if isinstance(personaje, dict):
                nombre = personaje.get('nombre', 'desconocido')
                
                if usar_placeholder:
                    resultado = crear_imagen_placeholder(nombre)
                else:
                    resultado = generar_imagen_personaje(personaje)
                
                if resultado:
                    generadas += 1
                else:
                    errores += 1
            else:
                print(f"⚠️ {personaje} (formato antiguo, omitiendo)")
        
        print(f"\n📊 Resultados:")
        print(f"   ✅ Generadas: {generadas}")
        print(f"   ❌ Errores: {errores}")
        print(f"   📂 Ubicación: {ASSETS_PERSONAJES_DIR}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")


def ejecutar_modo_completo():
    """
    Modo completo: Genera historia + escenas + imágenes de personajes
    """
    
    print("🚀 MODO COMPLETO: Historia + Escenas + Imágenes\n")
    
    # Generar historia
    print("1️⃣  GENERANDO HISTORIA...")
    resultado_historia = ejecutar_historia_unica()
    
    if not resultado_historia:
        print("❌ No se pudo generar la historia")
        return
    
    # Obtener personaje secundario
    print("\n2️⃣  GENERANDO IMÁGENES DEL PERSONAJE...")
    historia_dict = {
        "historia": resultado_historia.get("historia", ""),
        "elementos": resultado_historia.get("elementos", {})
    }
    
    # Generar imagen del personaje
    resultado_imagen = generar_imagenes_escena(historia_dict)
    
    if resultado_imagen:
        print(f"\n📊 Imágenes generadas: {resultado_imagen.get('total_imagenes', 0)}")
        print(f"\n✅ MODO COMPLETO FINALIZADO")
        print(f"   📝 Historia: {resultado_historia['ruta_directorio']}")
        print(f"   🎨 Personaje: {resultado_imagen.get('personaje', 'N/A')}")
    else:
        print(f"\n⚠️ No se generaron imágenes del personaje")
        print(f"\n✅ MODO COMPLETO FINALIZADO")
        print(f"   📝 Historia: {resultado_historia['ruta_directorio']}")


if __name__ == "__main__":
    main()
