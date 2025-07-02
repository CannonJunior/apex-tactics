#!/bin/bash

# Test script for Apex Tactics microservices
# Builds and tests the 3-service architecture

set -e

echo "🚀 Starting Apex Tactics Microservices Test"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
print_status "Checking prerequisites..."

if ! command_exists docker; then
    print_error "Docker is not installed!"
    exit 1
fi

if ! command_exists docker-compose; then
    if ! command_exists docker compose; then
        print_error "Docker Compose is not installed!"
        exit 1
    fi
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

print_status "✅ Prerequisites check passed"

# Change to project root directory
cd "$(dirname "$0")/.."

# Stop any running services
print_status "Stopping any existing services..."
$DOCKER_COMPOSE -f docker-compose.yml down 2>/dev/null || true
$DOCKER_COMPOSE -f docker/docker-compose.test.yml down 2>/dev/null || true

# Clean up test volumes
print_status "Cleaning up test volumes..."
docker volume rm apex-tactics_ollama_test_data 2>/dev/null || true

# Build all services
print_status "Building all services..."
if ! $DOCKER_COMPOSE -f docker-compose.yml build; then
    print_error "Failed to build services!"
    exit 1
fi

print_status "✅ All services built successfully"

# Start services for testing
print_status "Starting services for testing..."
if ! $DOCKER_COMPOSE -f docker-compose.yml up -d; then
    print_error "Failed to start services!"
    exit 1
fi

print_status "Waiting for services to be ready..."
sleep 10

# Function to check service health
check_service() {
    local service_name=$1
    local url=$2
    local max_attempts=30
    local attempt=1
    
    print_status "Checking $service_name health..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "$url/health" > /dev/null 2>&1; then
            print_status "✅ $service_name is healthy"
            return 0
        fi
        
        print_warning "Attempt $attempt/$max_attempts: $service_name not ready yet..."
        sleep 2
        ((attempt++))
    done
    
    print_error "❌ $service_name failed to become healthy"
    return 1
}

# Check all services
services_healthy=true

if ! check_service "Game Engine" "http://localhost:8000"; then
    services_healthy=false
fi

if ! check_service "MCP Gateway" "http://localhost:8002"; then
    services_healthy=false
fi

if ! check_service "AI Service" "http://localhost:8001"; then
    services_healthy=false
fi

if [ "$services_healthy" = false ]; then
    print_error "Some services failed health checks. Showing logs..."
    $DOCKER_COMPOSE -f docker-compose.yml logs --tail=50
    exit 1
fi

print_status "✅ All services are healthy"

# Run integration tests
print_status "Running integration tests..."

# Install test dependencies if not in container
if [ ! -f "/.dockerenv" ]; then
    if command_exists python3; then
        print_status "Installing test dependencies..."
        python3 -m pip install httpx structlog --quiet || {
            print_warning "Failed to install test dependencies. Running tests in container..."
            
            # Build and run test container
            docker build -t apex-test-runner docker/test-runner/
            
            if docker run --rm --network apex-tactics_apex-network \
                -e GAME_ENGINE_URL=http://game-engine:8000 \
                -e AI_SERVICE_URL=http://ai-service:8001 \
                -e MCP_GATEWAY_URL=http://mcp-gateway:8002 \
                apex-test-runner; then
                print_status "✅ Integration tests passed (container)"
            else
                print_error "❌ Integration tests failed (container)"
                exit 1
            fi
        }
        
        # Run tests directly
        if python3 docker/test-services.py; then
            print_status "✅ Integration tests passed"
        else
            print_error "❌ Integration tests failed"
            exit 1
        fi
    else
        print_warning "Python3 not available. Running tests in container..."
        
        # Build and run test container
        docker build -t apex-test-runner docker/test-runner/
        
        if docker run --rm --network apex-tactics_apex-network \
            -e GAME_ENGINE_URL=http://game-engine:8000 \
            -e AI_SERVICE_URL=http://ai-service:8001 \
            -e MCP_GATEWAY_URL=http://mcp-gateway:8002 \
            apex-test-runner; then
            print_status "✅ Integration tests passed (container)"
        else
            print_error "❌ Integration tests failed (container)"
            exit 1
        fi
    fi
fi

# Performance test (optional)
if [ "$1" = "--performance" ]; then
    print_status "Running performance tests..."
    
    # Basic load test
    print_status "Testing game engine performance..."
    for i in {1..10}; do
        curl -s "http://localhost:8000/health" > /dev/null
    done
    
    print_status "Testing MCP gateway performance..."
    for i in {1..10}; do
        curl -s "http://localhost:8002/health" > /dev/null
    done
    
    print_status "✅ Performance tests completed"
fi

# Show service status
print_status "Current service status:"
$DOCKER_COMPOSE -f docker-compose.yml ps

# Cleanup option
if [ "$1" = "--cleanup" ] || [ "$2" = "--cleanup" ]; then
    print_status "Cleaning up services..."
    $DOCKER_COMPOSE -f docker-compose.yml down
    docker volume prune -f
    print_status "✅ Cleanup completed"
else
    print_warning "Services are still running. Use '$DOCKER_COMPOSE -f docker-compose.yml down' to stop them."
fi

print_status "🎉 All tests completed successfully!"
print_status "Access the services at:"
print_status "  • Game Engine API: http://localhost:8000"
print_status "  • MCP Gateway: http://localhost:8002" 
print_status "  • AI Service: http://localhost:8001"