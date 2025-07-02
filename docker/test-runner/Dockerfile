# Dockerfile for Test Runner
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY docker/test-runner/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy test scripts and source code
COPY docker/test-services.py .
COPY tests/ ./tests/
COPY src/ ./src/

# Set Python path
ENV PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Run comprehensive tests by default
CMD ["python", "-m", "pytest", "tests/", "-v", "--tb=short"]