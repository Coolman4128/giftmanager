# Use Python 3.10 slim image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=giftmanager.settings

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# Create directory for SQLite database and static files
RUN mkdir -p /app/data /app/static /app/media

# Copy and set up entrypoint script
COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

# Create a non-root user for better security
RUN groupadd -r django && useradd -r -g django django

# Set proper permissions for all directories - ensure django user owns and can write to data
RUN chown -R django:django /app
RUN chmod -R 755 /app/data /app/static /app/media
RUN chmod 775 /app/data  # Make data directory writable by group

USER django

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Set the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
