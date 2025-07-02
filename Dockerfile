# Apex Tactics Game Engine Docker Image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY data/ ./data/
COPY assets/ ./assets/
COPY docs/ ./docs/
COPY CLAUDE.md .

# Create necessary directories
RUN mkdir -p /app/logs /app/tmp /app/saves

# Set permissions
RUN chmod +x scripts/*.py

# Expose ports
EXPOSE 8002 8004

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8002/api/health || exit 1

# Default command
CMD ["python", "scripts/run_game_with_mcp.py"]