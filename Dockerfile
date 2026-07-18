# Use the official lightweight Python 3.12 image.
# https://hub.docker.com/_/python
FROM python:3.12-slim

# Prevent Python from writing .pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1

# Prevent Python from buffering stdout and stderr to ensure logs are immediately visible
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Create a non-root user and group for security compliance
RUN groupadd -g 10001 appuser && \
    useradd -u 10001 -g appuser -s /sbin/nologin -c "Docker image user" appuser

# Install dependencies first (utilizing Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application source code with correct ownership
COPY --chown=appuser:appuser . .

# Switch to the non-root user
USER appuser

# Expose the default Cloud Run port
EXPOSE 8080

# Run the web service on container startup.
# Cloud Run dynamically assigns a port via the PORT environment variable at runtime.
# Using 'exec' ensures that SIGTERM signals are sent directly to the uvicorn process for graceful shutdown.
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}
