# Dockerfile for MCP Gateway Service
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy MCP Gateway code
COPY src/ ./src/
COPY tools/ ./tools/

# Set Python path
ENV PYTHONPATH=/app/src

# Expose port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Run the MCP Gateway service
CMD ["uvicorn", "src.mcp.gateway:app", "--host", "0.0.0.0", "--port", "8002", "--reload"]