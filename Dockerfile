FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY src/ ./src/
COPY mcp_configs/ ./mcp_configs/

RUN pip install --no-cache-dir uv && uv sync --frozen

ENV PYTHONPATH=/app

CMD ["uv", "run", "python", "-m", "src.notion_mcp.server"]