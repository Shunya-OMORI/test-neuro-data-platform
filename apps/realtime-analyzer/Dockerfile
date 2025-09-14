# Stage 1: Build stage to install dependencies
FROM python:3.11-slim as builder

WORKDIR /app
RUN pip install poetry
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.in-project true && \
    poetry install --no-root --no-dev

# Stage 2: Final stage
FROM python:3.11-slim

WORKDIR /app

# MatplotlibがGUIのない環境で動作するために必要なライブラリをインストール
RUN apt-get update && apt-get install -y libgomp1

# Copy virtual environment from builder stage
COPY --from=builder /app/.venv ./.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy source code
COPY src/ ./src/

EXPOSE 5002
CMD ["python", "src/main.py"]