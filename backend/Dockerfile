FROM node:22-alpine AS frontend-builder

WORKDIR /frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN CYPRESS_INSTALL_BINARY=0 npm ci

COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY backend/pyproject.toml ./
RUN pip install --no-cache-dir uv \
    && uv pip install --system --no-cache-dir -r pyproject.toml

COPY backend/app ./app
COPY --from=frontend-builder /frontend/out ./app/static

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
