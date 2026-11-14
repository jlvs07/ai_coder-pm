# AGENTS para backend

Este directorio contiene el backend FastAPI del MVP. FastAPI sirve la API y, en la imagen Docker, los archivos exportados estáticamente por Next.js en la ruta raíz.

## Objetivo actual

- Servir el frontend Kanban estático en `/`.
- Proporcionar endpoints de prueba y salud.
- Servir como base para la futura integración con SQLite, autenticación y OpenRouter.

## Stack previsto

- Python 3.12
- FastAPI
- Uvicorn
- SQLite
- uv como gestor de paquetes

## Estructura prevista

- `app/main.py`: aplicación principal de FastAPI.
- `app/__init__.py`: marca el paquete de la app.
- `app/static/`: salida estática de Next.js, copiada a la imagen Docker durante el build.
- `pyproject.toml`: configuración del proyecto y dependencias.
- `Dockerfile`: build multi-stage del frontend estático y la imagen FastAPI final.
- `tests/`: pruebas del backend cuando se implemente la lógica real.

## Principios para este backend

- Mantener la API pequeña y clara.
- No introducir complejidad innecesaria antes de que el proyecto requiera más estructura.
- Permitir pruebas simples de salud, HTML y JSON.
- Preparar la capa de datos para persistencia futura sin overengineering.

## Rutas y validación

- `GET /health`: estado del servicio.
- `GET /api/hello`: respuesta JSON de prueba.
- `GET /` y archivos estáticos: app Next.js exportada; en ejecución local sin export se muestra una página de prueba.

Validar el stack integrado con `docker compose up --build -d api` y las pruebas E2E de Cypress.
