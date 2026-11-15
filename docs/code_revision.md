# Revisión de código del MVP Kanban

## Datos de la revisión

- Fecha: 2026-11-15
- Commit revisado: `57da187` (`revisado Agents.md por opencode`)
- Alcance: backend FastAPI, frontend Next.js, pruebas, Docker, scripts, configuración y documentación.
- Método: lectura completa de los archivos versionados, ejecución de las suites y auditoría de dependencias.
- Resultado: revisión completada y hallazgos A1-A5 y M1-M7 corregidos; ver "Estado de remediación" y las verificaciones finales.

## Veredicto

El MVP es funcional y está razonablemente bien acotado para un entorno local. Las suites pasan, la API es la fuente de verdad y la IA tiene validación estructural con rollback transaccional. No se encontraron fallos funcionales bloqueantes en los flujos principales.

Los riesgos iniciales no estaban en la lógica del Kanban, sino en el borde operativo y de seguridad. Ya se corrigieron: la API se publica solo en loopback, Next.js está actualizado, el apagado limpia el perfil E2E, el arranque funciona sin `.env`, la documentación para agentes refleja el estado real y Playwright fue retirado. Quedan los hallazgos menores B1-B8 como trabajo futuro.

## Verificaciones ejecutadas

| Comprobación | Comando | Resultado |
| --- | --- | --- |
| Lint frontend | `npm run lint` | Pasa |
| Pruebas unitarias frontend | `npm run test:unit` | 16/16 pasan |
| Build frontend | `npm run build` | Pasa; genera export estático |
| Pruebas backend | `uv run --group dev pytest -q` | 16/16 pasan |
| E2E canónica aislada | `docker compose --profile e2e run --rm --build cypress` | 9/9 pasan |
| Salud integrada | `GET /health` | 200, `{"status":"ok","service":"kanban-api"}` |
| Frontend integrado | `GET /` | 200, `text/html` |
| Tablero integrado | `GET /api/boards/usuario` | 5 columnas, tarjetas cargadas |
| Auditoría de producción | `npm audit --omit=dev` | 0 vulnerabilidades |
| Auditoría completa | `npm audit` | 7 moderadas de desarrollo, sin corrección disponible |
| Playwright | Suite retirada | Eliminados configuración, pruebas, dependencia y artefactos |

Notas de las verificaciones:

- `uv` 0.13.8 se instaló en `~/.local/bin`; las pruebas de backend usan `uv run --group dev pytest` y el lockfile `backend/uv.lock`.
- La base persistente tenía 9 tarjetas en el momento de la revisión (el seed define 8). Es consistente con pruebas manuales previas y no afecta a las suites, pero conviene saberlo al comparar estados.
- Las 7 vulnerabilidades moderadas restantes son de desarrollo (`typescript-eslint` y `minimatch`) y no tienen versión corregida publicada al momento de la revisión.

## Estado de remediación

Fecha de cierre: 2026-11-15. Se corrigieron todos los hallazgos altos y medios.

| ID | Estado | Evidencia |
| --- | --- | --- |
| A1 | Resuelto | `docker-compose.yml` publica `127.0.0.1:8000:8000`; README y AGENTS documentan que no hay autenticación real. |
| A2 | Resuelto | Next.js `16.4.6`, `eslint-config-next` `16.4.6`, Cypress `16.3.0`, Vitest `5.1.0`; auditoría de producción en 0. |
| A3 | Resuelto | `scripts/stop.sh` y `stop.ps1` ejecutan `docker compose --profile e2e down --remove-orphans`; verificado sin contenedores ni red residual. |
| A4 | Resuelto | `.env.example` y `README.md` añadidos; `env_file` es opcional en ambos servicios. |
| A5 | Resuelto | `AGENTS.md` raíz reescrito con estado, modelo, credenciales y comandos reales; `backend/AGENTS.md` y `scripts/AGENTS.md` actualizados. |
| M1 | Resuelto | Playwright, su dependencia y artefactos eliminados; Cypress alineado a `16.3.0`; artefactos ignorados en `.gitignore`. |
| M2 | Resuelto | CORS de desarrollo para `localhost:3000` y `127.0.0.1:3000`; comando `npm run dev` documentado. |
| M3 | Resuelto | `KanbanCard` sincroniza título y detalles desde la tarjeta al abrir la edición; prueba de regresión tras actualización de IA. |
| M4 | Resuelto | `resetBoard` se ejecuta en `beforeEach` y `afterEach`; el perfil E2E sigue usando SQLite aislada. |
| M5 | Resuelto | `backend/uv.lock`, `httpx2>=2.0.0`, `uv sync --frozen --no-dev` en Docker y `pythonpath` de pytest. |
| M6 | Resuelto | Prueba Cypress de arrastre con eventos de puntero y persistencia de columna/orden. |
| M7 | Resuelto | Límites 200/4000/120, `extra="forbid"` y pruebas de rechazo en la API. |

Los hallazgos menores B1-B8 no forman parte de este cierre y siguen documentados abajo como trabajo futuro.

### Refactor modular posterior

- `backend/app/main.py` queda limitado a crear la app, CORS, routers y frontend estático.
- `backend/app/api/` separa routers (`system`, `boards`, `ai`) y esquemas HTTP (`schemas.py`).
- `backend/app/boards.py` conserva persistencia y mutaciones del tablero.
- `backend/app/board_updates.py` aplica acciones de la IA en una transacción.
- `backend/app/ai.py` solo construye el prompt y parsea respuestas; `ai_actions.py` define los modelos.
- Las pruebas se dividen en `conftest.py`, `test_system.py`, `test_boards.py` y `test_ai.py`.
- Verificado de nuevo: backend 16/16, frontend 16/16, build correcto, imagen Docker reconstruida y E2E 9/9.

## Hallazgos

### Tabla resumen de la revisión inicial

| ID | Severidad | Área | Ubicación | Hallazgo |
| --- | --- | --- | --- | --- |
| A1 | Alto | Seguridad | `docker-compose.yml:7-8`, `backend/app/main.py:169` | API sin autenticación publicada en todas las interfaces |
| A2 | Alto | Dependencias | `frontend/package.json:21` | Next.js 16.1.6 con vulnerabilidades críticas conocidas |
| A3 | Alto | Operación | `scripts/stop.sh:7` | `docker compose down` no detiene el perfil `e2e` |
| A4 | Alto | Onboarding | `docker-compose.yml:9-10` | `.env` obligatorio y ausente en el repositorio, sin `.env.example` |
| A5 | Alto | Documentación | `AGENTS.md:14`, `AGENTS.md:27`, `AGENTS.md:33` | Instrucciones raíz desactualizadas (modelo, credenciales, estado) |
| M1 | Medio | Pruebas | `frontend/tests/kanban.spec.ts`, `frontend/playwright.config.ts` | Playwright roto, sin script ni login; artefactos versionados |
| M2 | Medio | DX | `frontend/src/lib/kanbanApi.ts:3`, `frontend/src/lib/kanbanApi.ts:29` | `npm run dev` no puede cargar el tablero sin proxy/CORS |
| M3 | Medio | Frontend | `frontend/src/components/KanbanCard.tsx:21-22` | Estado local de edición no se sincroniza con cambios de la IA |
| M4 | Medio | Pruebas | `frontend/cypress/e2e/kanban.cy.ts:54-94` | E2E contra API persistente muta el tablero |
| M5 | Medio | Reproducibilidad | `backend/pyproject.toml:13`, `backend/Dockerfile:19-20` | Sin `uv.lock`; `httpx2>=1.0.0` desalineado con Starlette actual |
| M6 | Medio | Cobertura | `frontend/cypress/e2e/kanban.cy.ts:237-250` | El arrastre con puntero no tiene prueba automatizada |
| M7 | Medio | Validación | `backend/app/main.py:36-81` | Límites de longitud y rigor de modelos inconsistentes con la IA |
| B1 | Bajo | Accesibilidad | `frontend/src/components/NewCardForm.tsx:29-46`, `frontend/src/components/KanbanCard.tsx:54-58`, `frontend/src/app/layout.tsx:26` | Faltan etiquetas y hay semántica ARIA incorrecta |
| B2 | Bajo | Limpieza | `frontend/src/lib/kanban.ts:149` | `createId` no se usa |
| B3 | Bajo | Docker | `backend/Dockerfile:11`, `docker-compose.yml:6`, `scripts/start.sh:7` | Contenedor root, `container_name`, sin espera de salud |
| B4 | Bajo | SQLite | `backend/app/main.py:199-209` | Posible carrera de posición en creaciones concurrentes |
| B5 | Bajo | IA | `backend/app/ai.py:151-165` | Prompt injection y ausencia de control de coste/ritmo |
| B6 | Bajo | Documentación | `frontend/README.md:12-15`, `backend/AGENTS.md:20-28`, `scripts/AGENTS.md:1` | Comandos y estructura desactualizados |
| B7 | Bajo | UX/i18n | `frontend/src/components/AIChatPanel.tsx:43`, `frontend/src/components/KanbanColumn.tsx:73` | Mezcla de inglés y español |
| B8 | Bajo | Mantenibilidad | `backend/app/main.py:264-283` | Compactación de posiciones correcta pero innecesariamente compleja |

### A1. API sin autenticación publicada en todas las interfaces

`docker-compose.yml:7-8` publica `8000:8000`, lo que en Docker equivale a `0.0.0.0:8000`. La API no tiene middleware de autenticación y el nombre de usuario de la ruta solo identifica el tablero (`backend/app/main.py:169`). Cualquier equipo en la red local puede leer y modificar el tablero, y disparar el chat de IA, consumiendo la clave de OpenRouter.

Acción:

- Para el MVP local, publicar en loopback: `127.0.0.1:8000:8000`.
- Documentar que la autenticación es simulada y que el servicio no debe exponerse.
- Si se necesita acceso desde la red, añadir autenticación real antes de cambiar el binding.

### A2. Next.js 16.1.6 con vulnerabilidades críticas conocidas

`frontend/package.json:21` fija `next` en `16.1.6`. `npm audit --omit=dev` reporta una vulnerabilidad crítica en Next.js (rango afectado `9.3.4-canary.0` a `16.4.0`), además de vulnerabilidades altas en `sharp`, `postcss`, `source-map-js` y `nanoid`.

Las dos vulnerabilidades críticas descritas afectan a `rewrites` y al caché de `next/image`; la aplicación no usa ninguna de esas funciones, lo que reduce la explotabilidad actual. Aun así, la versión debe actualizarse.

Acción:

- Actualizar Next.js a `16.4.6` o superior, regenerar el lockfile y repetir `npm run lint`, `npm run test:unit`, `npm run build` y E2E.
- Revisar `npm audit` después de la actualización.
- Las vulnerabilidades críticas restantes de la auditoría completa (`vitest`, `tinypool`, `@vitest/coverage-v8`) son de desarrollo; actualizarlas también si se ejecutan suites en CI.

### A3. El apagado no detiene el perfil E2E

`scripts/stop.sh:7` ejecuta `docker compose down` sin perfiles. Los servicios `api-e2e` y `cypress` están bajo el perfil `e2e` (`docker-compose.yml:25-27`), por lo que no se detienen. Se reprodujo durante la revisión: tras el E2E, `ai_coder-pm-api-e2e-1` seguía activo y `docker compose down` no pudo eliminar la red porque seguía en uso.

Acción:

- Cambiar el apagado a `docker compose --profile e2e down --remove-orphans` (o ejecutar ambos `down`).
- Actualizar `scripts/stop.ps1` de forma equivalente.
- Añadir una verificación en los scripts de que no quedan contenedores del proyecto.

### A4. Arranque bloqueado en un clon limpio

`docker-compose.yml:9-10` y `docker-compose.yml:31-32` declaran `env_file: .env` para `api` y `api-e2e`. El repositorio no incluye `.env.example` ni un `README.md` raíz que explique crearlo. En un clon limpio, `docker compose up` falla antes de arrancar. Además, el E2E aislado no necesita la clave real porque mockea la IA, pero también exige el archivo.

Acción:

- Añadir `.env.example` con `OPENROUTER_API_KEY=` y un README raíz mínimo con los pasos de arranque.
- Alternativa: usar `env_file: { path: .env, required: false }` y dejar que los endpoints de IA respondan 503 sin clave.
- Mantener `.env` fuera de git; ya está correctamente ignorado.

### A5. Instrucciones raíz para agentes desactualizadas

`AGENTS.md` describe un estado que ya no existe:

- Línea 14: credenciales `user` / `password`; el login real es `usuario` / `contraseña` (`frontend/src/components/SessionGate.tsx:43`).
- Línea 27: modelo `google/gemma-4-26b-a4b-it:free`; el código usa `inclusionai/ling-3.2-flash:free` (`backend/app/openrouter.py:7`).
- Línea 33: afirma que el frontend es una demo puramente frontend sin Docker; el proyecto ya está integrado y persiste en SQLite.

Esto es especialmente costoso en un repositorio que se trabaja con agentes, porque induce cambios basados en supuestos falsos.

Acción:

- Reescribir `AGENTS.md` con el estado real: arquitectura, comandos verificados, modelo, credenciales, export estático y limitaciones.
- Revisar también `backend/AGENTS.md` (faltan `ai.py`, `boards.py` y `openrouter.py` en la estructura) y `scripts/AGENTS.md` (sigue en futuro y no describe los scripts actuales).

### M1. Playwright roto y artefactos de prueba versionados

- `frontend/tests/kanban.spec.ts:3-7` navega a `/` y espera el tablero sin hacer login; `SessionGate` muestra el formulario, por lo que la prueba no puede pasar.
- `frontend/playwright.config.ts:10` apunta a `http://127.0.0.1:3000` y arranca `next dev` (`frontend/playwright.config.ts:13-18`). En ese puerto la API relativa `/api/...` no existe y el backend no tiene CORS, así que el tablero tampoco podría cargarse.
- `frontend/test-results/.last-run.json` registra 3 fallos y los `trace.zip` están versionados. No hay script npm de Playwright ni servicio Compose; Cypress es la suite canónica.
- `frontend/package.json:26` mantiene `@playwright/test` como dependencia sin uso.

Acción:

- Preferible: retirar Playwright (config, tests, dependencia y `test-results`) y quedarse con Cypress.
- Alternativa: reparar Playwright con login real, backend en `:8000`, `NEXT_PUBLIC_API_URL`/CORS y un script npm; solo entonces integrarlo en Compose/CI.
- Añadir `frontend/test-results/`, `frontend/playwright-report/` y `frontend/cypress/screenshots/` a `.gitignore` y dejar de versionar artefactos.

### M2. `npm run dev` no puede cargar el tablero

`frontend/src/lib/kanbanApi.ts:3` usa `NEXT_PUBLIC_API_URL` o cadena vacía; con cadena vacía, las rutas son relativas (`frontend/src/lib/kanbanApi.ts:29-30`). En `npm run dev` (puerto 3000), `/api/...` se resuelve contra Next, que no tiene rewrites ni proxy, y devuelve 404. Si se define `NEXT_PUBLIC_API_URL=http://localhost:8000`, el navegador hace peticiones cross-origin y FastAPI no tiene CORS, por lo que se bloquean.

Acción:

- Documentar que el flujo integrado de desarrollo es Docker en `:8000`.
- O añadir CORS restrictivo en FastAPI para desarrollo y documentar `NEXT_PUBLIC_API_URL`.
- Tener en cuenta que el export estático no admite rewrites en tiempo de ejecución; no es una solución para producción estática.

### M3. Estado local de la tarjeta no se sincroniza tras cambios de la IA

`frontend/src/components/KanbanCard.tsx:21-22` inicializa `title` y `details` con `useState(card.title)` y `useState(card.details)`. Si la IA edita una tarjeta, `KanbanBoard` reemplaza el tablero (`frontend/src/components/KanbanBoard.tsx:377-382`), pero el componente no se remonta si solo cambian título o detalles. Al pulsar "Edit", el formulario muestra los valores antiguos y guardarlos sobrescribe el cambio de la IA.

Acción:

- Sincronizar el estado local al abrir la edición desde las props actuales, o con un efecto que actualice cuando no se está editando.
- Añadir una prueba: la IA actualiza una tarjeta, se pulsa "Edit" y el formulario muestra el valor actualizado.

### M4. E2E contra la API persistente muta el tablero

`frontend/cypress/e2e/kanban.cy.ts:54-94` restaura el estado inicial antes de cada prueba, pero la última prueba mueve `card-1` a Discovery (`frontend/cypress/e2e/kanban.cy.ts:237-250`) y no restaura al final. Si se ejecuta `npm run test:e2e` contra la API de `:8000` (el README sugiere `docker compose up --build -d api`), el volumen persistente queda modificado. La suite aislada con `api-e2e` evita este problema.

Acción:

- Documentar el E2E aislado como comando canónico y desaconsejar ejecutarlo contra la API persistente.
- Opcional: añadir un `afterEach`/`after` que restablezca el estado inicial, o usar siempre una base temporal.

### M5. Sin lockfile Python y restricción de `httpx2` desalineada

`backend/pyproject.toml` solo declara mínimos (`fastapi>=0.115.0`, `uvicorn>=0.30.0`, `httpx2>=1.0.0`) y no hay `uv.lock`. `backend/Dockerfile:19-20` instala con `uv pip install -r pyproject.toml`, por lo que dos builds en fechas distintas pueden resolver versiones diferentes. Además, Starlette actual declara `httpx2>=2.0.0` en su extra `full` y su `TestClient` importa `httpx2` como cliente preferente; el mínimo `1.0.0` del proyecto permite una versión potencialmente incompatible. Las pruebas pasan hoy con `httpx2 2.16.0` y Starlette 1.10.0, pero la reproducibilidad no está garantizada.

Acción:

- Generar y versionar `uv.lock`; en Docker usar `uv sync --frozen --no-dev` o exportar un requirements bloqueado.
- Subir el mínimo a `httpx2>=2.0.0` o usar `httpx` si se prefiere el cliente histórico de TestClient.
- Fijar también FastAPI/Starlette de forma reproducible mediante el lock.

### M6. El arrastre con puntero no tiene cobertura automatizada

La lógica pura de `moveCard` está bien cubierta (`frontend/src/lib/kanban.test.ts`), y Cypress prueba el movimiento con teclado (`frontend/cypress/e2e/kanban.cy.ts:237-250`). El arrastre con ratón, la línea indicadora y el soltar en columna vacía solo se validaron manualmente según `docs/PLAN.md`. Playwright, que podría cubrirlo, está roto.

Acción:

- Añadir una prueba Cypress de arrastre con `mousedown`/`mousemove`/`mouseup` sobre una tarjeta, verificando la persistencia tras recargar.
- Cubrir también soltar en columna vacía y reordenar dentro de la misma columna.

### M7. Validación de longitud y rigor de modelos inconsistente

La IA limita títulos y detalles (`backend/app/ai.py:57`, `backend/app/ai.py:71-72`, `backend/app/ai.py:86-87`), pero la API directa no:

- `backend/app/main.py:36-38`: `CardCreate.title` y `details` sin longitud máxima.
- `backend/app/main.py:49-51`: `CardUpdate` sin longitud máxima.
- `backend/app/main.py:72-73`: `ColumnUpdate.title` sin longitud máxima.
- Los modelos de `main.py` no usan `extra="forbid"`, así que campos desconocidos se ignoran silenciosamente; los de IA sí son estrictos.

No es un problema grave en local, pero permite payloads desproporcionados y hace que la API directa y la vía IA tengan contratos distintos.

Acción:

- Alinear límites: título de tarjeta 200, detalles 4000, título de columna 120.
- Usar `ConfigDict(extra="forbid")` en los modelos de entrada de la API.
- Añadir pruebas para títulos/detalles excesivos y campos extra.

### Hallazgos menores

- B1. Accesibilidad: `NewCardForm` usa solo placeholders, sin `<label>` ni `aria-label` (`frontend/src/components/NewCardForm.tsx:29-46`). En `KanbanCard`, `role="group"` se aplica después de `{...attributes}` y anula el rol interactivo de dnd-kit; `aria-disabled={undefined}` no aporta nada (`frontend/src/components/KanbanCard.tsx:54-58`). El documento declara `lang="en"` con UI mayoritariamente en español (`frontend/src/app/layout.tsx:26`).
- B2. `createId` está exportado pero no se usa en ningún punto del frontend (`frontend/src/lib/kanban.ts:149`); se puede eliminar. Los SVG por defecto de Next en `frontend/public/` tampoco se usan.
- B3. El contenedor final corre como root (`backend/Dockerfile:11`), usa `container_name: kanban-api` (`docker-compose.yml:6`), y `scripts/start.sh:7` no espera al healthcheck. Para un MVP local es aceptable, pero conviene un usuario no root y `docker compose up --wait`.
- B4. `create_card` calcula `MAX(position)+1` y luego inserta (`backend/app/main.py:199-209`). Dos creaciones concurrentes podrían chocar con `UNIQUE(column_id, position)`. SQLite serializa escrituras, pero no hay reintento ni transacción explícita para ese cálculo. Impacto bajo en un único usuario.
- B5. El prompt del sistema incluye el JSON del tablero y el historial del cliente (`backend/app/ai.py:151-180`). Una tarjeta con instrucciones maliciosas podría intentar dirigir al modelo. La validación de acciones limita el daño al tablero, pero no hay rate limiting ni control de coste en `/api/ai/connectivity` ni `/chat`.
- B6. Documentación secundaria: `frontend/README.md:12-15` arranca `api` y luego ejecuta Cypress, pero Cypress usa `api-e2e`; el paso de `api` es innecesario y confuso. `backend/AGENTS.md:20-28` no lista `ai.py`, `boards.py` ni `openrouter.py`. `scripts/AGENTS.md:1` sigue describiendo una carpeta futura. `docs/DATABASE.md:20-22` dice que se crea el tablero si no existe, pero el seed de columnas depende de que el tablero no tenga columnas.
- B7. Hay mensajes y textos en inglés en una interfaz mayoritariamente española: `frontend/src/components/AIChatPanel.tsx:43`, `frontend/src/components/KanbanColumn.tsx:73`, cabecera del tablero en `frontend/src/components/KanbanBoard.tsx:431-448`.
- B8. `delete_card` compacta posiciones con un desplazamiento temporal y dos `UPDATE` (`backend/app/main.py:264-283`). Es correcto, pero difícil de leer; un `position = position - 1 WHERE position > ?` tras el borrado sería suficiente si se garantiza el orden de actualización. Añadir una prueba de borrado en posición intermedia y al final.

## Plan de acción

Este plan ya se ejecutó para A1-A5 y M1-M7; se conserva como registro de la revisión.

### P0: antes de compartir o exponer la aplicación

- [ ] A1. Publicar la API solo en `127.0.0.1` y documentar que no hay autenticación real.
- [ ] A2. Actualizar Next.js a 16.4.6 o superior y repetir build, unitarias y E2E; revisar `npm audit`.
- [ ] A3. Hacer que `stop.sh` y `stop.ps1` detengan también el perfil `e2e` y verifiquen que no quedan contenedores.
- [ ] A4. Añadir `.env.example` y un README raíz mínimo con el arranque; decidir si `.env` es opcional para E2E.

### P1: siguiente iteración

- [ ] A5. Reescribir `AGENTS.md` raíz y corregir `backend/AGENTS.md` y `scripts/AGENTS.md`.
- [ ] M1. Retirar Playwright o repararlo y integrarlo; dejar de versionar `test-results` y añadirlo a `.gitignore`.
- [ ] M2. Documentar Docker como flujo de desarrollo integrado, o añadir CORS de desarrollo y `NEXT_PUBLIC_API_URL`.
- [ ] M3. Sincronizar el estado de edición de `KanbanCard` con las props y añadir prueba de regresión.
- [ ] M5. Generar `uv.lock`, usarlo en Docker y alinear el mínimo de `httpx2`.

### P2: calidad y mantenimiento

- [ ] M4. Documentar y automatizar el E2E aislado; evitar mutaciones del volumen persistente.
- [ ] M6. Añadir prueba E2E de arrastre con puntero, columna vacía y reordenación.
- [ ] M7. Alinear límites de longitud y usar modelos estrictos en la API directa.
- [ ] B1. Corregir etiquetas y ARIA; revisar `lang` y textos.
- [ ] B2. Eliminar `createId` si no se va a usar.
- [ ] B3. Endurecer el contenedor y esperar al healthcheck en el arranque.
- [ ] B4. Revisar concurrencia de creación de tarjetas y añadir reintento o transacción.
- [ ] B5. Delimitar el tablero en el prompt y considerar rate limiting para IA.
- [ ] B6. Corregir README, AGENTS secundarios y `DATABASE.md`.
- [ ] B7. Unificar idioma de la interfaz y los mensajes.
- [ ] B8. Simplificar la compactación de posiciones y cubrirla con pruebas.

## Limitaciones aceptadas

- No hay autenticación real: el login es una simulación en `localStorage` y el usuario está codificado como `usuario`.
- Un solo usuario y un solo tablero en el MVP; el esquema permite múltiples usuarios, pero no hay endpoints de gestión.
- Ejecución local; no hay despliegue, TLS ni gestión de secretos más allá de `.env`.
- No hay migraciones de base de datos; los cambios de esquema futuros requerirán una estrategia.
- No hay CI; las suites se ejecutan manualmente.
- El modelo de IA es gratuito y puede cambiar de disponibilidad o comportamiento.

## Observaciones positivas

- SQL parametrizado en todas las consultas; no se encontraron inyecciones SQL evidentes.
- Validación Pydantic de las acciones de IA y rechazo de respuestas inválidas sin mutar el tablero.
- Escrituras de orden y actualizaciones de IA dentro de transacciones; rollback ante error.
- Separación clara entre lógica pura (`src/lib/kanban.ts`), cliente API (`kanbanApi.ts`) y UI.
- La API es la fuente de verdad: el frontend no aplica cambios locales antes de la confirmación.
- `.env` está ignorado y no aparece en el historial de git; no se versionaron secretos.
- La suite aislada de E2E usa una base temporal y no toca el volumen persistente.
- Los tests de backend simulan OpenRouter, por lo que no dependen de red ni de la clave real.

## Anexo: entorno y comandos

Entorno de la revisión:

- Python 3.14.4
- Node.js v24.22.0
- npm 11.19.1
- Docker 29.9.3
- Docker Compose v5.7.0
- `uv` no disponible en el PATH local

Comandos de verificación ejecutados:

```bash
# frontend
npm run lint
npm run test:unit
npm run build
npm audit --omit=dev
npm audit

# backend
python3 -m pytest -q

# integración y E2E
docker compose --profile e2e run --rm cypress
curl -sS http://localhost:8000/health
curl -sS -o /dev/null -w '%{http_code} %{content_type}\n' http://localhost:8000/
curl -sS http://localhost:8000/api/boards/usuario

# limpieza
./scripts/stop.sh
docker compose --profile e2e down --remove-orphans
```