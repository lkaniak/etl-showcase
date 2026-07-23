FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml ./
COPY src src

RUN pip install uv && uv pip install --system -e .

ENV SEED_MOCK_API_PATH=/app/scripts/seed_mock_api.json

CMD ["uvicorn", "mock_source_api.main:app", "--host", "0.0.0.0", "--port", "8080"]
