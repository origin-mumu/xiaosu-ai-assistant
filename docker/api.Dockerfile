FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

COPY apps/api/pyproject.toml apps/api/uv.lock ./
COPY apps/api/src ./src
RUN uv sync --frozen --no-dev

RUN mkdir -p /app/logs /app/uploads

ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000

CMD ["uvicorn", "xiaosu.main:app", "--host", "0.0.0.0", "--port", "8000"]
