FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

ENV UV_COMPILE_BYTECODE=1

RUN uv pip install --system guardrails-ai

ARG GUARDRAILS_API_KEY
ENV GUARDRAILS_API_KEY=$GUARDRAILS_API_KEY

RUN guardrails configure --token $GUARDRAILS_API_KEY --disable-metrics --disable-remote-inferencing

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --only-group app --no-install-project

ENV PATH="/app/.venv/bin:$PATH"

COPY app.py settings.py guards.py mcp_client.py ./

CMD ["python", "-u", "app.py"]

