# Multi-stage Dockerfile for DDoSPot Honeypot
# Stage 1: Builder - Install dependencies and compile packages
FROM python:3.13-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    make \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Create wheels from requirements
RUN pip install --user --no-cache-dir --wheel --no-binary :all: -r requirements.txt

# Stage 2: Runtime - Lightweight production image
FROM python:3.13-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libffi8 \
    libssl3 \
    curl \
    dnsutils \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Set environment variables
ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    FLASK_APP=app/main.py \
    FLASK_ENV=production

# Create necessary directories
RUN mkdir -p logs monitoring/data

# Set permissions
RUN chmod +x /app/start-dashboard.py /app/start-honeypot.py

# Health check for dashboard
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Default to running honeypot
# Can be overridden with: docker run <image> python start-dashboard.py
CMD ["python", "start-honeypot.py"]
