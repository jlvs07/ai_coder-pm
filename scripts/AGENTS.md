# AGENTS para scripts

Scripts de arranque y parada para Linux/macOS (`.sh`) y Windows (`.ps1`).

- `start.*`: construye y levanta el servicio `api`; espera a que el healthcheck esté listo.
- `stop.*`: detiene `api` y limpia también los servicios del perfil `e2e` con `--remove-orphans`.

La API escucha en `127.0.0.1:8000`. Mantener los scripts simples y equivalentes entre plataformas.
