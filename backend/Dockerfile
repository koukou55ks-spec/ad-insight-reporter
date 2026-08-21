FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev

COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

CMD ["sh", "-c", "uv run --no-dev alembic upgrade head && exec uv run --no-dev uvicorn app.main:app --host 0.0.0.0 --port 8080"]
