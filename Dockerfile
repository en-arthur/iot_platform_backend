FROM python:3.12-slim

# System environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

# Application configuration placeholders (override these in Render dashboard)
ENV ENVIRONMENT="production" \
    PROJECT_NAME="DeviceStack Technologies API" \
    SUPABASE_URL="https://your-project-ref.supabase.co" \
    SUPABASE_ANON_KEY="placeholder-supabase-anon-key" \
    SUPABASE_SERVICE_ROLE_KEY="placeholder-supabase-service-role-key" \
    SUPABASE_JWT_SECRET="placeholder-supabase-jwt-secret" \
    FRONTEND_URL="https://your-frontend-domain.com" \
    BACKEND_CORS_ORIGINS='["https://your-frontend-domain.com"]' \
    MQTT_BROKER_HOST="broker.example.com" \
    MQTT_BROKER_PORT="1883" \
    MQTT_ADMIN_USER="admin" \
    MQTT_ADMIN_PASSWORD="placeholder-mqtt-password" \
    MQTT_USE_TLS="false" \
    AI_MODEL_PROVIDER="gemini" \
    AI_MODEL_NAME="gemini-2.5-flash" \
    GEMINI_API_KEY="placeholder-gemini-api-key" \
    SANDBOX_PROVIDER="e2b" \
    E2B_API_KEY="placeholder-e2b-api-key" \
    WORKERSCRAFT_URL="https://your-workerscraft-service.onrender.com"

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
