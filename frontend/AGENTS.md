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
- Consumir la API del backend como fuente de verdad del tablero persistido.

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
- `src/lib/kanban.ts`: modelo de datos del tablero, `initialData` (referencia para pruebas) y lógica de movimiento de tarjetas (`moveCard`, `createId`).
- `src/lib/kanban.test.ts`: pruebas unitarias de la lógica del tablero.
- `src/lib/kanbanApi.ts`: cliente HTTP de la API (obtener tablero, CRUD de tarjetas, renombrar columna, guardar orden y chat). Usa rutas relativas `/api/...` y el usuario codificado `usuario`.
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

La data inicial de referencia contiene 5 columnas y varias tarjetas de ejemplo. El tablero real se carga desde la API al iniciar sesión.

## Comportamiento actual

- El tablero se carga desde la API al montar (`getBoard`); no hay fallback silencioso a `initialData`.
- La ruta principal monta `SessionGate`; sin sesión se muestra el formulario y el tablero no se renderiza.
- El marcador local de sesión sobrevive a recargas y se elimina al cerrar sesión. Este mecanismo es solo una simulación frontend, no una autenticación segura.
- Renombrar una columna llama a `renameColumn` y refleja el cambio en la UI tras la confirmación de la API.
- Crear una tarjeta llama a `createCard` y añade la tarjeta devuelta al estado.
- Editar una tarjeta llama a `updateCard` y actualiza el estado con la respuesta.
- Eliminar una tarjeta llama a `deleteCard` y quita la referencia de la columna y la entrada de `cards`.
- El movimiento entre columnas y la reordenación dentro de una columna se resuelven con `moveCard` y se persisten con `saveCardOrder` (`PUT /api/boards/usuario/cards/order`).
- El drag & drop usa `@dnd-kit` con `PointerSensor` y `KeyboardSensor`, y `closestCorners`.
- El chat envía el mensaje y el historial al backend; sustituye el estado local con el tablero devuelto solo después de una respuesta satisfactoria.
- Los estados de carga y los errores de la API se muestran de forma explícita; los cambios se aplican solo tras confirmación del backend.

## Convenciones de desarrollo

- Mantener la lógica de negocio en `src/lib/` y la UI en `src/components/`.
- Preferir datos simples y explícitos sobre abstracciones complejas.
- No añadir dependencias nuevas sin necesidad clara.
- Mantener un estilo sencillo y consistente con el diseño actual del MVP.
- Mantener la misma separación entre estado visual y datos del dominio.
- La API y SQLite son la fuente de verdad; no reintroducir datos mock como estado inicial del tablero.

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
- Mantener la separación entre estado visual y datos del dominio; la persistencia ya está integrada vía `kanbanApi.ts`.

## Notas importantes

El tablero persiste en SQLite a través de la API del backend. La sesión sigue siendo una simulación en `localStorage`, no autenticación real. En Docker, `next build` genera `out/` y FastAPI sirve esa exportación estática; para desarrollo de UI se puede usar `npm run dev` (requiere el backend aparte en `:8000`).
