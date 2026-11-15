# Aplicación de Gestión de Proyectos MVP

## Estado actual

El MVP está implementado y empaquetado en Docker. FastAPI sirve la API y la exportación estática de Next.js en `http://localhost:8000`. La persistencia usa SQLite y el chat usa OpenRouter. La autenticación es una simulación local, no seguridad real: la API escucha solo en `127.0.0.1` y no debe exponerse en red.

## Requisitos de negocio

- Login de un único usuario demo: `usuario` / `contraseña`.
- Un tablero Kanban por usuario, con cinco columnas fijas que se pueden renombrar.
- Tarjetas editables, eliminables y movibles con arrastrar y soltar o teclado.
- Chat lateral con IA que puede crear, editar, mover o eliminar tarjetas.
- Ejecución local en un contenedor Docker.

La base de datos está preparada para múltiples usuarios y tableros, aunque el MVP solo use uno.

## Arquitectura

- `frontend/`: Next.js 16 con React 19, TypeScript, Tailwind y @dnd-kit. Se exporta como sitio estático.
- `backend/`: FastAPI con SQLite. En Docker copia `frontend/out` a `app/static`.
- `backend/app/api/`: routers HTTP por dominio (`system`, `boards`, `ai`) y esquemas de petición.
- `backend/app/boards.py`: persistencia y operaciones del tablero.
- `backend/app/board_updates.py`: aplicación transaccional de acciones de la IA.
- `backend/app/ai.py` y `backend/app/ai_actions.py`: prompt, parseo y modelos estructurados del asistente.
- `backend/app/openrouter.py`: cliente de OpenRouter; modelo `inclusionai/ling-3.2-flash:free`.
- `docker-compose.yml`: servicio `api`, perfil `e2e` aislado y Cypress.
- `scripts/`: arranque y parada para Linux/macOS (`.sh`) y Windows (`.ps1`).
- `docs/`: planificación y revisión de código (`docs/PLAN.md`, `docs/code_revision.md`).

## Arranque y pruebas

```bash
cp .env.example .env
./scripts/start.sh
```

`OPENROUTER_API_KEY` es opcional para el tablero; sin clave los endpoints de IA responden 503. Parar y limpiar también el perfil E2E con `./scripts/stop.sh`.

Pruebas:

```bash
cd frontend && npm run lint && npm run test:unit && npm run build
cd backend && uv run --group dev pytest
docker compose --profile e2e run --rm --build cypress
```

Si `uv` no está instalado, usar `python3 -m pytest` en `backend/`. E2E local usa `frontend/cypress` y el stack de `docker compose`; el comando canónico aísla la base en `api-e2e`.

## Decisiones técnicas

- Python 3.12 en Docker; dependencias fijadas en `backend/uv.lock`.
- SQLite local en el volumen `kanban_data`; se crea si no existe.
- Next.js se compila a estático y FastAPI lo sirve en `/`.
- La API escucha en `127.0.0.1:8000`; no hay autenticación real.
- CORS solo para desarrollo en `localhost:3000` y `127.0.0.1:3000`.
- Variables de entorno vía `.env` opcional en Compose; `.env.example` documenta la clave.
- El perfil E2E usa `DATABASE_PATH=/tmp/kanban-e2e.db` para no tocar la base persistente.

## Esquema de color

- Amarillo acentuado: `#ecad0a` - líneas acentuadas, destacados
- Azul primario: `#209dd7` - enlaces, secciones clave
- Púrpura secundario: `#753991` - botones de envío, acciones importantes
- Azul marino oscuro: `#032147` - títulos principales
- Texto gris: `#888888` - texto de apoyo, etiquetas

## Estándares de codificación

1. Usar versiones actuales y enfoques idiomáticos.
2. Mantenerlo simple: no sobre-ingenierizar ni añadir funciones extra.
3. Ser conciso y mantener los README mínimos. Nunca usar emojis.
4. Identificar la causa raíz con evidencia antes de corregir; no adivinar.
5. Mantener la API y SQLite como fuente de verdad; no reintroducir datos mock como estado del tablero.
6. Idioma: español para documentación y mensajes visibles; identificadores de código en inglés.
