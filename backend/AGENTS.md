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

## Estructura prevista

- `app/main.py`: aplicación principal de FastAPI.
- `app/database.py`: conexión, esquema SQLite e inicialización del tablero demo.
- `app/__init__.py`: marca el paquete de la app.
- `app/static/`: salida estática de Next.js, copiada a la imagen Docker durante el build.
- `pyproject.toml`: configuración del proyecto y dependencias.
- `Dockerfile`: build multi-stage del frontend estático y la imagen FastAPI final.
- `tests/test_api.py`: pruebas de API y persistencia SQLite.

## Principios para este backend

- Mantener la API pequeña y clara.
- No introducir complejidad innecesaria antes de que el proyecto requiera más estructura.
- Validar entradas con modelos Pydantic y devolver errores HTTP claros.
- Ejecutar cambios de orden multi-fila dentro de una transacción.

## Rutas y validación

- `GET /health`: estado del servicio.
- `GET /api/hello`: respuesta JSON de prueba.
- `GET /api/boards/{username}`: tablero con la estructura compatible con `BoardData`.
- `POST /api/boards/{username}/columns/{column_id}/cards`: crear tarjeta.
- `PATCH /api/boards/{username}/cards/{card_id}`: editar título o detalles.
- `DELETE /api/boards/{username}/cards/{card_id}`: borrar tarjeta.
- `PATCH /api/boards/{username}/columns/{column_id}`: renombrar columna.
- `PUT /api/boards/{username}/cards/order`: actualizar orden y columna de todas las tarjetas del tablero.
- `GET /` y archivos estáticos: app Next.js exportada; en ejecución local sin export se muestra una página de prueba.

El nombre de usuario identifica el tablero en esta API de pruebas; no es una verificación de autenticación. Ejecutar las pruebas con `uv run --group dev pytest` desde `backend/`. El contenedor guarda SQLite en `/data/kanban.db` dentro del volumen `kanban_data`.
