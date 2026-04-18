# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.11-slim

# Allow statements and log messages to immediately appear in logs
ENV PYTHONUNBUFFERED=True

# Create app directory
ENV APP_HOME=/app
WORKDIR $APP_HOME

# Copy requirements first for better layer caching
COPY requirements.txt requirements.txt

# Install production dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)"

# Default port
ENV PORT=8000

# Run the web service on container startup using Uvicorn (more lightweight than gunicorn for this use case)
# For production with multiple workers, use gunicorn with uvicorn workers
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
