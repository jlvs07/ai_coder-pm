# Kanban Studio

## Ejecutar

```bash
npm install
npm run dev
```

En Docker, FastAPI sirve el frontend exportado en `http://localhost:8000/`:

```bash
docker compose up --build -d api
docker compose run --rm cypress
```

El acceso demo es `usuario` / `contraseña`. La sesión se guarda localmente en el navegador; no es autenticación segura.

## Pruebas

```bash
npm run test:unit
npm run test:e2e
```
