# AGENTS para frontend

Este directorio contiene el frontend MVP de la aplicación de gestión de proyectos. Next.js exporta el login y el tablero como archivos estáticos y FastAPI los sirve desde `/` en el contenedor integrado.

## Objetivo del frontend actual

- Renderizar un tablero Kanban con columnas fijas y tarjetas editables.
- Mostrar un chat lateral de IA que puede operar sobre el tablero y sincroniza los cambios confirmados por la API.
- Exigir el login simulado antes de mostrar el tablero.
- Permitir cerrar sesión; la sesión demo se conserva en `localStorage`.
- Permitir renombrar columnas.
- Permitir crear, borrar y reordenar tarjetas con arrastrar y soltar.
- Compilar como exportación estática para servirla con FastAPI.
- Servir como base para la integración con la API, base de datos y chat con IA en fases posteriores.

## Stack y runtime

- Next.js 16
- React 19
- TypeScript
- @dnd-kit para drag & drop
- Vitest + Testing Library para pruebas unitarias
- Cypress para pruebas E2E

## Estructura principal

- `src/app/page.tsx`: punto de entrada de la vista principal; renderiza `KanbanBoard`.
- `src/components/KanbanBoard.tsx`: contenedor principal del tablero. Mantiene el estado del tablero, maneja drag & drop, creación y eliminación de tarjetas, y renombrado de columnas.
- `src/components/AIChatPanel.tsx`: panel lateral de chat, historial de conversación de la sesión, estado de envío y errores.
- `src/components/SessionGate.tsx`: protege la vista del tablero con el login local simulado (`usuario` / `contraseña`) y controla el cierre de sesión.
- `src/components/SessionGate.test.tsx`: pruebas unitarias de acceso, credenciales incorrectas, persistencia local y cierre de sesión.
- `src/components/KanbanColumn.tsx`: representa cada columna del Kanban y contiene la UI de edición y creación de tarjetas.
- `src/components/KanbanCard.tsx`: tarjeta individual de la columna.
- `src/components/KanbanCardPreview.tsx`: preview visual que se usa durante el arrastre.
- `src/components/NewCardForm.tsx`: formulario para crear nuevas tarjetas.
- `src/lib/kanban.ts`: estado inicial, modelo de datos del tablero y lógica de movimiento de tarjetas (`moveCard`, `createId`).
- `src/lib/kanban.test.ts`: pruebas unitarias de la lógica del tablero.
- `src/components/KanbanBoard.test.tsx`: pruebas de UI del tablero.
- `cypress/e2e/kanban.cy.ts`: pruebas E2E con Cypress.
- `cypress.config.ts`: configuración E2E; por defecto apunta al stack local en `http://127.0.0.1:8000`.

## Modelo de datos actual

El estado del Kanban está definido en `src/lib/kanban.ts`:

- `BoardData`
  - `columns: Column[]`
  - `cards: Record<string, Card>`
- `Column`
  - `id`
  - `title`
  - `cardIds`
- `Card`
  - `id`
  - `title`
  - `details`

La data inicial contiene 5 columnas y varias tarjetas de ejemplo.

## Comportamiento actual

- El tablero se inicializa con `initialData`.
- La ruta principal monta `SessionGate`; sin sesión se muestra el formulario y el tablero no se renderiza.
- El marcador local de sesión sobrevive a recargas y se elimina al cerrar sesión. Este mecanismo es solo una simulación frontend, no una autenticación segura.
- Renombrar una columna actualiza el título en el estado local.
- Crear una tarjeta añade la tarjeta al mapa `cards` y la referencia a la columna.
- Eliminar una tarjeta elimina la referencia de la columna y la entrada de la tarjeta.
- El movimiento entre columnas y reordenación dentro de una misma columna se resuelve con `moveCard`.
- El drag & drop usa `@dnd-kit` con `PointerSensor` y `closestCorners`.
- El chat envía el mensaje y el historial al backend; sustituye el estado local con el tablero devuelto solo después de una respuesta satisfactoria.

## Convenciones de desarrollo

- Mantener la lógica de negocio en `src/lib/` y la UI en `src/components/`.
- Preferir datos simples y explícitos sobre abstracciones complejas.
- No añadir dependencias nuevas sin necesidad clara.
- Mantener un estilo sencillo y consistente con el diseño actual del MVP.
- Cuando se integren backend y base de datos, evitar romper la estructura de datos ya usada por el tablero.

## Pruebas

Comandos actuales disponibles en `frontend/package.json`:

- `npm run test` / `npm run test:unit`: ejecuta pruebas unitarias con Vitest.
- `npm run test:e2e`: ejecuta pruebas E2E con Cypress contra el servidor en el puerto 8000.
- `npm run test:all`: ejecuta unitarias + E2E.
- `npm run build`: compila la app de Next.js.
- `npm run lint`: ejecuta ESLint.

## Recomendaciones para trabajos futuros

- Algebra de estado y lógica del tablero debe mantenerse centralizada en `src/lib` para facilitar pruebas.
- Los cambios de backend no deben hacer que la UI dependa de datos mock localizados en componentes.
- Cuando se introduzca autenticación y persistencia, mantener la misma separación entre estado visual y datos del dominio.

## Notas importantes

El frontend sigue siendo una demostración local sin persistencia ni autenticación real. En Docker, `next build` genera `out/` y FastAPI sirve esa exportación estática; para desarrollo de UI se puede usar `npm run dev`.
