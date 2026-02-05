FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including wgrib2
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    gcc \
    g++ \
    libeccodes-dev \
    libeccodes-tools \
    && wget -q -O /tmp/wgrib2.deb https://www.ftp.cpc.ncep.noaa.gov/wd51we/wgrib2/wgrib2.tgz.v3.1.1.deb \
    && dpkg -i /tmp/wgrib2.deb || apt-get install -f -y \
    && rm -rf /var/lib/apt/lists/* /tmp/*

# Verify wgrib2 installation
RUN which wgrib2 && wgrib2 --version

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install additional weather data libraries
RUN pip install --no-cache-dir \
    cfgrib \
    xarray \
    netcdf4 \
    h3-py \
    pyarrow \
    pandas \
    numpy

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 weatheruser && chown -R weatheruser:weatheruser /app
USER weatheruser

# Create data directory
RUN mkdir -p /data/raw /data/processed /data/metadata

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python3 -c "import sys; sys.exit(0)" || exit 1

# Default command (can be overridden)
CMD ["python3", "gfs_poc.py", "--help"]