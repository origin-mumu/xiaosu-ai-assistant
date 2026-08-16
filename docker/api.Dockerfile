FROM python:3.13-slim

WORKDIR /app

# Install uv using Aliyun mirror (super fast)
RUN pip install --no-cache-dir uv -i https://mirrors.aliyun.com/pypi/simple/

COPY apps/api/pyproject.toml apps/api/uv.lock ./
COPY apps/api/src ./src

# Sync dependencies using Aliyun PyPI mirror
RUN uv sync --frozen --no-dev --index-url https://mirrors.aliyun.com/pypi/simple/

RUN mkdir -p /app/logs /app/uploads

ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000

CMD ["uvicorn", "xiaosu.main:app", "--host", "0.0.0.0", "--port", "8000"]
