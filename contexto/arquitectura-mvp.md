# 🏗️ Arquitectura del Proyecto – Versión Estratégica MVP
## Cadena de Producción Audiovisual Automatizada

---

# 🎯 Objetivo del MVP

Construir una primera versión funcional del sistema que permita:

- Generar historias infantiles con IA
- Dividirlas en escenas estructuradas
- Generar material visual consistente
- Producir un video final
- Gestionarlo todo desde un panel privado (dashboard)

⚠️ En esta fase NO buscamos automatización total.
Buscamos validar el sistema y el flujo completo de creación.

---

# 🧠 1. Arquitectura General (Vista Macro)

El sistema se divide en 5 bloques principales:

1. 🔐 Acceso y Control
2. 📝 Generación Narrativa
3. 🎬 Dirección de Escenas
4. 🖼️ Producción Visual
5. 🚀 Exportación y Publicación

---

# 🔐 2. Bloque 1 – Acceso y Control

## Función:
Permitir que solo tú (o futuros usuarios) accedan al sistema.

## Componentes:

- Landing Page simple
- Sistema de Login (email + password)
- Dashboard principal

## Dashboard debe incluir:

- Botón: “Crear Nueva Historia”
- Listado de historias creadas
- Estado del proyecto:
  - 🟡 Borrador
  - 🔵 En producción
  - 🟢 Finalizado
- Estadísticas básicas (en fases posteriores)

## Tecnología sugerida (MVP):

- Frontend: Next.js o React
- Backend: Supabase o Firebase (auth + base de datos)
- Diseño mobile-first (optimizado para Android)

---

# 📝 3. Bloque 2 – Generación Narrativa

## Objetivo:
Convertir una idea en una historia estructurada.

## Flujo:

1. El usuario introduce:
   - Tema
   - Edad objetivo
   - Moraleja
   - Duración estimada

2. El sistema genera:
   - Título
   - Resumen
   - Historia completa
   - Diálogos
   - Descripción emocional

3. El usuario revisa y aprueba.

## Resultado:
Historia validada lista para dividir en escenas.

---

# 🎬 4. Bloque 3 – Director de Escenas (Showrunner Mode)

## Objetivo:
Convertir la historia en estructura audiovisual profesional.

Cada escena debe contener:

- Número de escena
- Descripción visual detallada
- Personajes presentes
- Emoción dominante
- Tipo de plano (general, medio, primer plano)
- Iluminación
- Movimiento sugerido
- Duración aproximada

⚠️ Aquí es donde se afina el prompt para evitar inconsistencias visuales.

## Resultado:
Guión técnico listo para producción visual.

---

# 🖼️ 5. Bloque 4 – Producción Visual

## Paso 1: Generación de imágenes base

Cada escena → 1 imagen coherente con:

- Rasgos fijos de personajes
- Paleta de colores consistente
- Estilo visual definido (caricatura 3D estilo animación cinematográfica)

## Paso 2: Conversión a clips animados

Cada imagen se transforma en:

- Clip corto (3–6 segundos)
- Movimiento sutil
- Expresión coherente

## Paso 3: Unión de clips

Se ensamblan:

- Clips en orden narrativo
- Música de fondo
- Narración IA
- Transiciones suaves

## Resultado:
Video final exportable.

---

# 🚀 6. Bloque 5 – Exportación y Publicación

## MVP:

- Descarga manual del video
- Subida manual a YouTube

## Fase futura:

- Publicación automática
- Generación de título SEO
- Descripción optimizada
- Miniatura coherente
- Programación automática

---

# 🗄️ 7. Base de Datos – Estructura Simplificada

## Tabla: Users
- id
- email
- password_hash

## Tabla: Stories
- id
- user_id
- title
- summary
- full_text
- status
- created_at

## Tabla: Scenes
- id
- story_id
- scene_number
- visual_description
- emotional_tone
- shot_type
- duration

## Tabla: Videos
- id
- story_id
- file_url
- views
- likes
- retention

---

# ⚙️ 8. Nivel de Automatización del MVP

En esta versión:

- Generación de historia → Automática
- División en escenas → Automática con revisión manual
- Generación visual → Semi-manual
- Edición → Manual asistida
- Publicación → Manual

Automatización total será Fase 2.

---

# 📈 9. Métricas Clave del MVP

Debemos medir:

- Tiempo desde idea hasta video final
- Calidad visual consistente
- Tiempo de producción por episodio
- Primeras métricas de visualización

El objetivo del MVP no es ganar dinero.
Es validar el sistema completo.

---

# 🧭 10. Filosofía del MVP

No estamos creando solo videos.
Estamos construyendo una infraestructura.

Primero:
✔️ Flujo sólido
✔️ Identidad clara
✔️ Consistencia

Después:
💰 Escalado
🤖 Automatización total
🌍 Expansión a nuevos públicos

---

# 🎯 Resultado Esperado del MVP

Al finalizar esta fase deberías tener:

- Sistema funcional desde tu móvil
- 1–3 episodios publicados
- Flujo de producción probado
- Identidad visual estable
- Base lista para escalar

---

# 🔮 Próximo Nivel

Cuando el MVP esté validado:

- Automatización completa
- Generación en lote
- Producción semanal
- Escalado a otros nichos
- Posible apertura a otros creadores

---

Fin del documento.