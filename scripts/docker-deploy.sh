#!/bin/bash

# Apex Tactics Docker Deployment Script

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Help function
show_help() {
    cat << EOF
Apex Tactics Docker Deployment Script

Usage: $0 [COMMAND] [OPTIONS]

Commands:
    start       Start all services (default)
    stop        Stop all services
    restart     Restart all services
    logs        Show service logs
    status      Show service status
    clean       Clean up containers and volumes
    build       Build Docker images
    pull        Pull latest images
    test        Run tests

Options:
    --profile PROFILE   Use docker-compose profile (monitoring, production, persistence)
    --build            Force rebuild of images
    --no-cache         Build without using cache
    --detach           Run in background (default for start)
    --follow           Follow logs output
    --service SERVICE  Target specific service
    --help             Show this help message

Examples:
    $0 start --profile monitoring      # Start with monitoring stack
    $0 logs --follow --service game-engine
    $0 clean --volumes                 # Clean including volumes
    $0 test                           # Run integration tests

EOF
}

# Default values
COMMAND="start"
PROFILE=""
BUILD_FLAG=""
CACHE_FLAG=""
DETACH_FLAG="-d"
FOLLOW_FLAG=""
SERVICE=""
CLEAN_VOLUMES=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        start|stop|restart|logs|status|clean|build|pull|test)
            COMMAND="$1"
            shift
            ;;
        --profile)
            PROFILE="--profile $2"
            shift 2
            ;;
        --build)
            BUILD_FLAG="--build"
            shift
            ;;
        --no-cache)
            CACHE_FLAG="--no-cache"
            shift
            ;;
        --detach)
            DETACH_FLAG="-d"
            shift
            ;;
        --follow)
            FOLLOW_FLAG="-f"
            shift
            ;;
        --service)
            SERVICE="$2"
            shift 2
            ;;
        --volumes)
            CLEAN_VOLUMES="--volumes"
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            ;;
    esac
done

# Check if Docker and Docker Compose are available
check_dependencies() {
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed or not in PATH"
    fi

    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed or not in PATH"
    fi

    log "Dependencies check passed"
}

# Check if .env file exists
check_env_file() {
    if [ ! -f "docker/.env" ]; then
        if [ -f "docker/.env.example" ]; then
            warn ".env file not found, copying from .env.example"
            cp docker/.env.example docker/.env
            warn "Please review and update docker/.env with your configuration"
        else
            error ".env file not found and no .env.example available"
        fi
    fi
}

# Start services
start_services() {
    log "Starting Apex Tactics services..."
    
    if [ -n "$SERVICE" ]; then
        docker-compose $PROFILE up $DETACH_FLAG $BUILD_FLAG $SERVICE
    else
        docker-compose $PROFILE up $DETACH_FLAG $BUILD_FLAG
    fi
    
    if [ "$DETACH_FLAG" = "-d" ]; then
        log "Services started in background"
        log "Use '$0 logs --follow' to see logs"
        log "Use '$0 status' to check service status"
    fi
}

# Stop services
stop_services() {
    log "Stopping Apex Tactics services..."
    
    if [ -n "$SERVICE" ]; then
        docker-compose $PROFILE stop $SERVICE
    else
        docker-compose $PROFILE down
    fi
    
    log "Services stopped"
}

# Restart services
restart_services() {
    log "Restarting Apex Tactics services..."
    stop_services
    sleep 2
    start_services
}

# Show logs
show_logs() {
    if [ -n "$SERVICE" ]; then
        docker-compose $PROFILE logs $FOLLOW_FLAG $SERVICE
    else
        docker-compose $PROFILE logs $FOLLOW_FLAG
    fi
}

# Show status
show_status() {
    log "Service Status:"
    docker-compose $PROFILE ps
    
    echo ""
    log "Container Health:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" --filter "name=apex-"
}

# Clean up
clean_up() {
    log "Cleaning up Apex Tactics containers and networks..."
    
    docker-compose $PROFILE down $CLEAN_VOLUMES --remove-orphans
    
    if [ -n "$CLEAN_VOLUMES" ]; then
        log "Removing volumes..."
        docker volume prune -f
    fi
    
    log "Removing dangling images..."
    docker image prune -f
    
    log "Cleanup complete"
}

# Build images
build_images() {
    log "Building Apex Tactics Docker images..."
    
    if [ -n "$SERVICE" ]; then
        docker-compose $PROFILE build $CACHE_FLAG $SERVICE
    else
        docker-compose $PROFILE build $CACHE_FLAG
    fi
    
    log "Build complete"
}

# Pull images
pull_images() {
    log "Pulling latest Docker images..."
    
    docker-compose $PROFILE pull
    
    log "Pull complete"
}

# Run tests
run_tests() {
    log "Running integration tests..."
    
    # Start services in test mode
    docker-compose -f docker-compose.yml -f docker/docker-compose.test.yml $PROFILE up -d
    
    # Wait for services to be ready
    sleep 30
    
    # Run tests
    if docker-compose exec game-engine python -m pytest tests/ -v; then
        log "Tests passed!"
    else
        error "Tests failed!"
    fi
    
    # Cleanup test environment
    docker-compose -f docker-compose.yml -f docker/docker-compose.test.yml $PROFILE down
}

# Health check
health_check() {
    log "Performing health check..."
    
    services=("game-engine:8002" "ai-service:8001")
    
    for service in "${services[@]}"; do
        IFS=':' read -r name port <<< "$service"
        
        if curl -f -s "http://localhost:$port/health" > /dev/null 2>&1; then
            log "✓ $name is healthy"
        else
            warn "✗ $name is not responding"
        fi
    done
}

# Main execution
main() {
    check_dependencies
    check_env_file
    
    case $COMMAND in
        start)
            start_services
            sleep 5
            health_check
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            sleep 5
            health_check
            ;;
        logs)
            show_logs
            ;;
        status)
            show_status
            ;;
        clean)
            clean_up
            ;;
        build)
            build_images
            ;;
        pull)
            pull_images
            ;;
        test)
            run_tests
            ;;
        *)
            error "Unknown command: $COMMAND"
            ;;
    esac
}

# Run main function
main