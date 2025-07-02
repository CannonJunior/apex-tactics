#!/bin/bash

# Start Ollama server in background
echo "Starting Ollama server..."
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo "Waiting for Ollama to be ready..."
until curl -f http://localhost:11434/api/version; do
    echo "Waiting for Ollama server..."
    sleep 2
done

# Pull required models if they don't exist
echo "Checking for required AI models..."
models=("llama2:7b" "codellama:7b" "mistral:7b")

for model in "${models[@]}"; do
    if ! ollama list | grep -q "$model"; then
        echo "Pulling model: $model"
        ollama pull "$model"
    else
        echo "Model $model already available"
    fi
done

echo "Starting AI Service..."
# Start the AI service
python -m uvicorn src.ai.service:app --host 0.0.0.0 --port 8001 --reload &
AI_SERVICE_PID=$!

# Function to handle shutdown
shutdown() {
    echo "Shutting down services..."
    kill $AI_SERVICE_PID 2>/dev/null
    kill $OLLAMA_PID 2>/dev/null
    wait
    exit 0
}

# Trap signals
trap shutdown SIGTERM SIGINT

# Wait for either process to exit
wait