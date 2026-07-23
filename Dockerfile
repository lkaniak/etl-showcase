FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY packages packages
COPY apps apps
COPY scripts scripts
COPY migrations migrations

RUN pip install uv && uv sync --package etl-usage-example --frozen

ENV PATH="/app/.venv/bin:$PATH"

CMD ["python", "-m", "my_marketplace_etl.main"]
