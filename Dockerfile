FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (exclude web/ via .dockerignore)
COPY alembic.ini .
COPY alembic/ alembic/
COPY api/ api/
COPY src/ src/
COPY config/ config/
COPY scripts/ scripts/

# Railway provides PORT env var, default to 8000
ENV PORT=8000

CMD alembic upgrade head && uvicorn api.main:app --host 0.0.0.0 --port ${PORT}
