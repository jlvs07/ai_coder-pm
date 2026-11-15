# Kanban Studio MVP

Aplicación local de gestión de proyectos con login simulado, tablero Kanban persistente y chat con IA. Next.js se exporta como sitio estático y FastAPI lo sirve junto con la API en `http://localhost:8000`.

## Arranque

```bash
cp .env.example .env
./scripts/start.sh
```

`OPENROUTER_API_KEY` es opcional para navegar y editar el tablero: sin clave, los endpoints de IA responden 503. En Windows usar `scripts/start.ps1`.

Credenciales demo: `usuario` / `contraseña`. La sesión se guarda en `localStorage` y no es autenticación real. La API escucha solo en `127.0.0.1`; no exponerla en red.

Detener y limpiar también el perfil E2E:

```bash
./scripts/stop.sh
```

## Pruebas

Frontend, desde `frontend/`:

```bash
npm run lint
npm run test:unit
npm run build
```

Backend, desde `backend/`:

```bash
uv run --group dev pytest
# Alternativa si uv no está instalado: python3 -m pytest
```

E2E aislado, sin tocar la base persistente:

```bash
docker compose --profile e2e run --rm --build cypress
```

## Desarrollo del frontend

Con el backend levantado, se puede usar Next en modo desarrollo:

```bash
cd frontend
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

El backend permite CORS para `localhost:3000` y `127.0.0.1:3000`. El flujo integrado recomendado sigue siendo Docker en `:8000`.
