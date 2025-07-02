# Dockerfile for AI Service with Ollama
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including Ollama
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.ai/install.sh | sh

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy AI service code
COPY src/ ./src/
COPY models/ ./models/

# Set Python path
ENV PYTHONPATH=/app/src

# Expose ports
EXPOSE 8001 11434

# Create directories for Ollama
RUN mkdir -p /root/.ollama

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8001/health && curl -f http://localhost:11434/api/version || exit 1

# Start script that launches both Ollama and the AI service
COPY docker/ai-service/start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]