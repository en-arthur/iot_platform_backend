FROM python:3.12-slim

# System environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

# Non-secret defaults only. Secrets MUST come from the platform env
# (Render dashboard / render.yaml) — baking placeholder credentials into the
# image previously made HS256 JWT verification "available" with a known secret.
ENV ENVIRONMENT="production" \
    PROJECT_NAME="DeviceStack Technologies API" \
    AI_MODEL_PROVIDER="gemini" \
    AI_MODEL_NAME="gemini-2.5-flash" \
    SANDBOX_PROVIDER="e2b" \
    MQTT_BROKER_PORT="1883"

WORKDIR /app

# Install system dependencies for cryptography / networking if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency resolution
RUN pip install uv

# Copy project definition, README, and application code
COPY backend/pyproject.toml backend/README.md* ./
COPY backend/app ./app

# Install dependencies into system environment
RUN uv pip install --system -e .

# Expose ports (standard 8000 and Render default 10000)
EXPOSE 8000 10000

# Render dynamically sets $PORT (e.g. 10000). Fallback to $PORT or 8000.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
