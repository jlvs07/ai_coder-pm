# AGENTS para backend

Este directorio contiene el backend FastAPI del MVP. FastAPI sirve la API y, en la imagen Docker, los archivos exportados estáticamente por Next.js en la ruta raíz.

## Persistencia y API

- Servir el frontend Kanban estático en `/`.
- Guardar usuarios, tableros, columnas y tarjetas en SQLite.
- Inicializar la base, el usuario demo `usuario`, un tablero, cinco columnas y tarjetas de ejemplo al arrancar.
- Mantener la conexión SQLite cerrada al terminar cada operación y activar claves foráneas por conexión.

## Stack

- Python 3.12
- FastAPI
- Uvicorn
- SQLite
- uv como gestor de paquetes

## Estructura

- `app/main.py`: creación de la aplicación, CORS, routers y montaje del frontend estático.
- `app/api/`: routers HTTP (`system.py`, `boards.py`, `ai.py`) y modelos de petición (`schemas.py`).
- `app/boards.py`: lectura y mutaciones de tableros, columnas, tarjetas y orden.
- `app/board_updates.py`: aplicación transaccional de acciones estructuradas de la IA.
- `app/ai.py`: prompt del sistema, construcción de mensajes y parseo de respuestas.
- `app/ai_actions.py`: modelos Pydantic de historial y acciones de la IA.
- `app/database.py`: conexión, esquema SQLite e inicialización del tablero demo.
- `app/openrouter.py`: cliente HTTP de OpenRouter.
- `app/__init__.py` y `app/api/__init__.py`: marcan los paquetes.
- `app/static/`: salida estática de Next.js, copiada a la imagen Docker durante el build.
- `pyproject.toml` y `uv.lock`: dependencias fijadas del proyecto.
- `Dockerfile`: build multi-stage del frontend estático y la imagen FastAPI final.
- `tests/conftest.py`: fixture compartido de cliente y base temporal.
- `tests/test_system.py`, `tests/test_boards.py`, `tests/test_ai.py`: pruebas por dominio.

## Principios para este backend

- Mantener la API pequeña y clara.
- No introducir complejidad innecesaria antes de que el proyecto requiera más estructura.
- Validar entradas con modelos Pydantic y devolver errores HTTP claros.
- Ejecutar cambios de orden multi-fila dentro de una transacción.

## Rutas y validación

- `GET /health`: estado del servicio.
- `GET /api/hello`: respuesta JSON de prueba.
- `POST /api/ai/connectivity`: consulta simple a OpenRouter para comprobar conectividad.
- `POST /api/boards/{username}/chat`: envía mensaje, historial y tablero a OpenRouter; valida y persiste acciones Kanban estructuradas.
- `GET /api/boards/{username}`: tablero con la estructura compatible con `BoardData`.
- `POST /api/boards/{username}/columns/{column_id}/cards`: crear tarjeta.
- `PATCH /api/boards/{username}/cards/{card_id}`: editar título o detalles.
- `DELETE /api/boards/{username}/cards/{card_id}`: borrar tarjeta.
- `PATCH /api/boards/{username}/columns/{column_id}`: renombrar columna.
- `PUT /api/boards/{username}/cards/order`: actualizar orden y columna de todas las tarjetas del tablero.
- `GET /` y archivos estáticos: app Next.js exportada; en ejecución local sin export se muestra una página de prueba.

El nombre de usuario identifica el tablero en esta API de pruebas; no es una verificación de autenticación. El contenedor guarda SQLite en `/data/kanban.db` dentro del volumen `kanban_data`. En la imagen Docker se usa `uv` con `uv.lock` y el comando `uv run --group dev pytest` desde `backend/`. Si `uv` no está disponible en el host, usar `python3 -m pytest` con las dependencias instaladas con pip.
