FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for cfgrib
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    g++ \
    libeccodes-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory first (as root)
RUN mkdir -p /data/raw /data/processed /data/metadata && chmod 777 /data

# Create non-root user
RUN useradd -m -u 1000 weatheruser && chown -R weatheruser:weatheruser /app /data
USER weatheruser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python3 -c "import sys; sys.exit(0)" || exit 1

# Default command (can be overridden)
CMD ["python3", "gfs_poc.py", "--help"]