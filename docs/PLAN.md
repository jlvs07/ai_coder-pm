# Plan detallado del MVP de gestión de proyectos

## Objetivo general

Construir una aplicación local de gestión de proyectos con autenticación simulada, tablero Kanban persistente, backend FastAPI y conexión con IA a través de OpenRouter. La implementación debe partir del frontend ya existente y evolucionar hacia una solución ejecutable localmente con Docker, con pruebas automatizadas en cada fase.

## Estado inicial (antes de ejecutar el plan)

- El frontend demo ya existe en `frontend/` y muestra un tablero Kanban funcional de ejemplo.
- El backend mínimo y la configuración de Docker se implementaron durante la fase 2.
- La base de datos local SQLite aún no está modelada ni conectada.
- La autenticación simulada y la funcionalidad de IA aún no están integradas.

## Criterio de aprobación del plan

Antes de iniciar la implementación, el usuario debe revisar y aprobar este plan y la estructura de trabajo. La ejecución posterior debe seguir este checklist en orden, marcando cada tarea a medida que avance.

---

## Fase 1: Preparación, documentación y alineación del repositorio

- [x] Revisar y validar la estructura del repositorio y la documentación existente.
- [x] Confirmar que [AGENTS.md](../AGENTS.md) y [docs/PLAN.md](./PLAN.md) reflejan el trabajo correcto para este proyecto.
- [x] Crear el archivo [frontend/AGENTS.md](../frontend/AGENTS.md) con una descripción del código existente del frontend.
- [x] Definir la arquitectura base: frontend Next.js, backend FastAPI, SQLite, scripts de arranque/parada y OpenRouter.
- [x] Confirmar el acuerdo del usuario sobre la secuencia de implementación y los criterios de aceptación del MVP.

Pruebas y validación:
- [x] Verificar que los archivos principales de instrucciones y planificación existen y están documentados.
- [x] Revisar que el plan sea consistente con el estado del repositorio y los requisitos del MVP.

Criterio de éxito:
- [x] El usuario revisó y aprobó la fase 1; el repositorio y el plan quedaron alineados con el alcance del proyecto.

---

## Fase 2: Infraestructura base, Docker y backend inicial

- [x] Crear la estructura de carpetas del backend en `backend/`.
- [x] Configurar Docker y Docker Compose para ejecutar la app localmente.
- [x] Crear scripts de inicio y apagado en `scripts/` para macOS, Linux y Windows.
- [x] Preparar el entorno Python con `uv` como gestor de paquetes.
- [x] Crear una app FastAPI mínima con un endpoint de salud (`/health`) y un endpoint de prueba (`/api/hello`).
- [x] Configurar la aplicación para servir una respuesta HTML estática de ejemplo.
- [x] Verificar las rutas del backend en local con `curl` y comprobar el frontend integrado en navegador con Cypress.

Pruebas y validación:
- `docker compose up` o equivalente ejecuta correctamente la aplicación. Validado con `./scripts/start.sh`.
- `curl http://localhost:8000/health` devuelve `{"status":"ok","service":"kanban-api"}`.
- `curl http://localhost:8000/api/hello` devuelve `{"message":"hello from the Kanban backend"}`.
- `curl http://localhost:8000/` devuelve HTML con estado HTTP 200 y tipo de contenido `text/html`.
- El frontend integrado responde en `/` y las pruebas E2E de Cypress pasan en el contenedor.

Criterio de éxito:
- Validado: la infraestructura base funciona en local y el backend responde correctamente antes de integrar la lógica de negocio.

---

## Fase 3: Integración del frontend con el runtime esperado

- [x] Ajustar la configuración de Next.js para generar una exportación estática compatible con el proyecto.
- [x] Asegurar que FastAPI sirve el tablero Kanban de demostración en `/` en el stack integrado.
- [x] Verificar que los archivos estáticos del frontend se sirven desde FastAPI junto con las rutas `/health` y `/api/hello`.
- [x] Mantener la base visual y funcional del tablero actual sin romper la experiencia de usuario.
- [x] Ejecutar pruebas unitarias y E2E del frontend integrado.

Pruebas y validación:
- [x] `npm test` en `frontend/`: 6 pruebas unitarias pasan.
- [x] `npm run build` genera `frontend/out/index.html` y los assets en `frontend/out/_next/static/`.
- [x] La imagen Docker integrada compila el frontend estático y lo sirve mediante FastAPI en `http://localhost:8000/`.
- [x] `GET /health` y `GET /api/hello` siguen respondiendo correctamente.
- [x] Las pruebas Cypress en contenedor verifican que el tablero carga, permite añadir una tarjeta y renombrar una columna: 3 pasan.
- [x] `npm run lint` pasa sin errores.

Criterio de éxito:
- [x] Validado: el frontend Kanban estático se sirve desde FastAPI en `/`, conserva su funcionalidad demo y está preparado para la integración posterior con la API.

---

## Fase 4: Inicio de sesión simulado

- [x] Añadir una pantalla de login inicial en la aplicación al acceder a `/` por primera vez.
- [x] Implementar las credenciales temporales ficticias acordadas: `usuario` / `contraseña`.
- [x] Guardar la sesión simulada en `localStorage` para mantenerla tras recargar la página.
- [x] Permitir cerrar sesión y volver a la vista de login.
- [x] Proteger la visualización del tablero para que solo sea visible cuando la sesión esté activa.
- [x] Ejecutar pruebas unitarias y E2E de autenticación simulada.

Pruebas y validación:
- [x] El usuario no autenticado no puede ver el tablero.
- [x] Con credenciales correctas entra al tablero y la sesión se conserva al recargar.
- [x] Con credenciales incorrectas se muestra un error y la sesión no se crea.
- [x] El cierre de sesión elimina el acceso al contenido protegido.
- [x] `npm test`: 9 pruebas unitarias pasan; `npm run lint` y `npm run build` pasan.
- [x] Cypress en contenedor: 5 pruebas E2E pasan contra el frontend servido desde FastAPI.

Criterio de éxito:
- [x] Validado: la experiencia de autenticación simulada funciona con `usuario` / `contraseña`; no representa autenticación segura y podrá sustituirse por el backend en una fase posterior.

---

## Fase 5: Modelado de la base de datos

- [x] Definir la propuesta de esquema de usuarios, tableros, columnas, tarjetas y sus relaciones.
- [x] Guardar la propuesta en [docs/database-schema.json](./database-schema.json).
- [x] Documentar las entidades y el enfoque de persistencia en [docs/DATABASE.md](./DATABASE.md).
- [x] Obtener la aprobación del usuario sobre el esquema final antes de construir la migración o el modelo real.
- [x] Preparar la propuesta para soportar múltiples usuarios en una evolución futura, aunque el MVP use un único usuario.

Pruebas y validación:
- [x] Validar que el archivo JSON es sintácticamente correcto y cubre el modelo Kanban.
- [x] Confirmar que el modelo relaciona usuarios con un tablero, tableros con columnas y columnas con tarjetas, incluyendo el orden necesario.

Criterio de éxito:
- [x] Validado: el usuario aprobó el esquema documentado; ya puede usarse como base para implementar la persistencia en la fase 6.

---

## Fase 6: Backend de persistencia del tablero Kanban

- [x] Crear la conexión a SQLite en FastAPI y activar claves foráneas por conexión.
- [x] Crear la base de datos y las tablas si no existen al arrancar la aplicación.
- [x] Crear las tablas aprobadas para usuarios, tableros, columnas y tarjetas.
- [x] Añadir endpoint para leer el tablero del usuario demo.
- [x] Añadir endpoints para crear, actualizar y borrar tarjetas.
- [x] Añadir endpoints para renombrar columnas y reordenar tarjetas entre columnas.
- [x] Validar entradas y devolver respuestas HTTP consistentes ante recursos inexistentes o datos inválidos.
- [x] Ejecutar pruebas unitarias del backend para los flujos principales.

Pruebas y validación:
- [x] `pytest` en `backend/`: 5 pruebas pasan sin avisos.
- [x] Crear, actualizar parcialmente y borrar tarjetas se comprobó en las pruebas y contra el contenedor.
- [x] Renombrar columna y reordenar/mover tarjetas entre columnas se comprobó en las pruebas y contra el contenedor.
- [x] El borrado elimina la tarjeta del mapa y de la columna y compacta las posiciones.
- [x] La base de datos se crea automáticamente en un archivo temporal y en el volumen Docker.
- [x] Los cambios del tablero sobreviven al reinicio del contenedor mediante el volumen SQLite.
- [x] La suite Cypress existente sigue pasando: 5 pruebas E2E.

Criterio de éxito:
- [x] Validado: FastAPI proporciona API CRUD y orden persistente para el tablero Kanban con SQLite.

---

## Fase 7: Integración Frontend + Backend

- [x] Conectar el frontend con la API del backend para cargar el tablero persistido del usuario demo.
- [x] Usar el estado cargado desde la API como fuente de datos del tablero, sin fallback silencioso a datos de demostración si falla la carga.
- [x] Mantener renombrado de columnas, movimiento, edición, creación y borrado de tarjetas conectados a sus endpoints.
- [x] Mostrar estados de carga y errores de carga o guardado.
- [x] Aplicar en la interfaz los cambios persistidos solo después de que la API confirme el guardado.
- [x] Validar la persistencia tras recargar, incluido el orden de tarjetas y sus columnas.
- [x] Ejecutar pruebas unitarias, compilación y E2E para la integración frontend-backend.

Pruebas y validación:
- [x] El tablero se carga desde la API.
- [x] La creación, edición, borrado y renombrado se guardan en la API; las pruebas E2E verifican persistencia tras recargar.
- [x] El movimiento de tarjetas se guarda mediante el endpoint de orden y se conserva al recargar.
- [x] La aplicación sigue funcionando con la base de datos local.
- [x] `npm test`: 14 pruebas unitarias pasan.
- [x] `npm run lint` y `npm run build` pasan.
- [x] Cypress en contenedor: 7 pruebas E2E pasan.
- [x] Se verificó manualmente el arrastre con ratón desde cualquier zona de la tarjeta y la persistencia tras recargar.
- [x] Se verificó manualmente que se puede soltar una tarjeta en una columna vacía.
- [x] Se verificó manualmente que soltar encima o debajo de otra tarjeta determina correctamente la posición, incluido el final de la lista.
- [x] Durante el arrastre se muestra una línea resaltada en la posición prevista de inserción.
- [x] El movimiento con teclado sigue disponible como alternativa accesible.

Decisiones de diseño:
- El frontend estático y FastAPI comparten origen; el cliente usa rutas relativas `/api/...` y no requiere CORS.
- La API es la fuente de verdad: las mutaciones actualizan la UI solo tras una respuesta satisfactoria y los errores se muestran explícitamente.
- El sensor de puntero permite iniciar el arrastre desde la tarjeta; mientras se edita una tarjeta, su arrastre queda desactivado para no interferir con los controles de edición.
- La detección durante el arrastre prioriza el elemento bajo el puntero. La mitad vertical de la tarjeta objetivo determina si la inserción es anterior o posterior; la columna vacía permite insertar en el índice cero y la propia columna sirve como destino al final de la lista.
- Una línea azul resaltada marca el punto de inserción calculado. El sensor de teclado con coordenadas sortables se conserva además del sensor de puntero.
- El usuario confirmó la validación de la fase 7 el 14/11/2026.

Criterio de éxito:
- [x] Validado: el tablero funciona como una aplicación persistente y no solo como demo estática.

---

## Fase 8: Conectividad con IA mediante OpenRouter

- [ ] Configurar la conexión a OpenRouter usando la clave disponible en `.env`.
- [ ] Usar el modelo `google/gemma-4-26b-a4b-it:free`.
- [ ] Crear una prueba simple de conectividad con una consulta básica como `2 + 2`.
- [ ] Confirmar que el backend puede invocar la API externa y obtener una respuesta válida.
- [ ] Manejar errores, timeouts y respuestas vacías con lógica simple y clara.

Pruebas y validación:
- Llamada de prueba `2 + 2` responde adecuadamente.
- El backend captura y devuelve un resultado del modelo.
- La aplicación no rompe el flujo principal si la IA falla temporalmente.

Criterio de éxito:
- La conectividad con OpenRouter queda verificada y lista para usarse en la lógica del Kanban con IA.

---

## Fase 9: Integración de IA con el estado del tablero y salidas estructuradas

- [ ] Enviar al modelo el JSON del tablero actual junto con la pregunta del usuario y el historial de conversación.
- [ ] Definir un esquema de respuesta estructurada para la IA que incluya:
  - respuesta textual al usuario
  - actualización opcional del tablero
  - cambios de columnas o tarjetas
- [ ] Validar que la IA responde con una estructura clara y procesable.
- [ ] Implementar la lógica para aplicar actualizaciones del tablero cuando la IA las propone.
- [ ] Capturar y registrar respuestas inválidas o incompletas para evitar corrupción del estado.
- [ ] Ejecutar pruebas exhaustivas del flujo de IA.

Pruebas y validación:
- La IA puede responder a una solicitud de edición del Kanban.
- La respuesta tiene formato estructurado y es parseable.
- Si la IA devuelve una actualización válida, se refleja en la UI.
- Si la respuesta no es válida, el sistema no rompe el tablero.

Criterio de éxito:
- La IA puede operar sobre el tablero con salida estructurada y cambios controlados.

---

## Fase 10: Widget lateral de chat con IA y sincronización del Kanban

- [ ] Añadir un panel lateral atractivo con chat para el usuario.
- [ ] Permitir enviar mensajes al backend con el context del tablero actual y el historial de conversación.
- [ ] Mostrar la respuesta de la IA en la interfaz.
- [ ] Si la IA propone cambios al Kanban, aplicarlos automáticamente en la UI.
- [ ] Mantener sincronizado el estado del tablero con la respuesta del modelo.
- [ ] Ejecutar pruebas de UI y de integración junto con el flujo de IA.

Pruebas y validación:
- El usuario puede iniciar conversación con la IA desde la barra lateral.
- La UA del sistema refleja cambios del Kanban provocados por la respuesta del modelo.
- El usuario puede seguir usando el tablero sin inconsistencias.

Criterio de éxito:
- La aplicación completa cumple el flujo de trabajo del MVP: login, tablero persistente, IA con chat y actualizaciones automáticas del Kanban.

---

## Validación final del proyecto

- [ ] Ejecutar la batería completa de pruebas: frontend, backend, integración y E2E.
- [ ] Validar el arranque completo con Docker y scripts de entorno.
- [ ] Revisar que no haya errores funcionales ni de integridad en el flujo completo.
- [ ] Confirmar que la aplicación queda lista para demostra el MVP en local.

Pruebas finales:
- `npm run test` en frontend
- `pytest` en backend
- pruebas de Docker y arranque local
- verificación del flujo de login, tablero y chat IA

Criterio final de éxito:
- La aplicación queda funcionando localmente como MVP con autenticación simulada, persistencia, tablero Kanban y asistente de IA integrado.
