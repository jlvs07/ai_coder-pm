# Kanban Studio

## Desarrollo

Con el backend levantado en `http://localhost:8000`:

```bash
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

En Docker, FastAPI sirve el frontend exportado en `http://localhost:8000/`. Desde la raíz del repositorio:

```bash
./scripts/start.sh
```

El acceso demo es `usuario` / `contraseña`. La sesión se guarda localmente en el navegador; no es autenticación segura.

## Pruebas

```bash
npm run lint
npm run test:unit
npm run build
```

E2E con el stack aislado, desde la raíz:

```bash
docker compose --profile e2e run --rm --build cypress
```
