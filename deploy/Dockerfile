FROM node:22-alpine AS frontend-build
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build-only

FROM python:3.12-slim AS backend-build
WORKDIR /build/backend
COPY backend/pyproject.toml ./
COPY backend/app ./app
RUN python -m pip wheel --no-cache-dir --wheel-dir /wheels .

FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    NODEWATCH_STATIC_DIR=/app/static
WORKDIR /app
RUN useradd --system --uid 10001 --create-home nodewatch
COPY --from=backend-build /wheels /wheels
RUN python -m pip install --no-cache-dir /wheels/*.whl && rm -rf /wheels
COPY backend/alembic.ini ./alembic.ini
COPY backend/alembic ./alembic
COPY --from=frontend-build /build/frontend/dist ./static
COPY deploy/entrypoint.sh /usr/local/bin/nodewatch-entrypoint
RUN chmod 0755 /usr/local/bin/nodewatch-entrypoint && chown -R nodewatch:nodewatch /app
USER nodewatch
EXPOSE 8000
ENTRYPOINT ["nodewatch-entrypoint"]
