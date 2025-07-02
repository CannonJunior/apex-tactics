# Docker Deployment Guide

This guide covers deploying the Apex Tactics game engine using Docker containers for development, testing, and production environments.

## Overview

The Docker deployment includes:

- **Game Engine**: Core service with WebSocket support and integrated MCP Gateway
- **AI Service**: Tactical AI with Ollama integration for decision making
- **Redis**: Session management and caching
- **Nginx**: Reverse proxy and load balancer (production)
- **Monitoring**: Prometheus and Grafana stack (optional)

## Quick Start

### Prerequisites

- Docker 20.10+ and Docker Compose 2.0+
- Minimum 4GB RAM (8GB recommended for AI service)
- Ports 8002, 8004, 8001 available

### Basic Deployment

```bash
# Clone repository
git clone <repository-url>
cd apex-tactics

# Copy environment configuration
cp docker/.env.example docker/.env

# Start services
./scripts/docker-deploy.sh start

# Check status
./scripts/docker-deploy.sh status
```

### Service Access

- **Game Engine WebSocket**: http://localhost:8002
- **MCP Gateway**: port 8004 (stdio/HTTP)
- **AI Service**: http://localhost:8001
- **Health Check**: http://localhost:8002/api/health

## Deployment Modes

### Development Mode (Default)

```bash
# Start core services
./scripts/docker-deploy.sh start

# Follow logs
./scripts/docker-deploy.sh logs --follow
```

### Production Mode

```bash
# Start with Nginx reverse proxy
./scripts/docker-deploy.sh start --profile production

# Services available at:
# - http://localhost (main interface)
# - http://localhost/api (game API)
# - http://localhost/ai (AI service)
```

### Monitoring Mode

```bash
# Start with monitoring stack
./scripts/docker-deploy.sh start --profile monitoring

# Access monitoring:
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3000 (admin/admin123)
```

### Persistence Mode

```bash
# Start with database persistence
./scripts/docker-deploy.sh start --profile persistence

# Includes:
# - PostgreSQL database
# - Redis persistence
```

## Configuration

### Environment Variables

Edit `docker/.env` to configure:

```bash
# Service Ports
WEBSOCKET_PORT=8002
MCP_GATEWAY_PORT=8004
AI_SERVICE_PORT=8001

# Performance
MAX_SESSIONS=100
SESSION_TIMEOUT=3600
TURN_TIME_LIMIT=30

# Logging
LOG_LEVEL=INFO
ENVIRONMENT=development

# AI Configuration
OLLAMA_HOST=0.0.0.0
```

### Docker Compose Profiles

Available profiles:
- `monitoring` - Prometheus and Grafana
- `production` - Nginx reverse proxy
- `persistence` - PostgreSQL and Redis persistence
- `testing` - Test environment configuration

## Service Management

### Deployment Script

The `scripts/docker-deploy.sh` script provides comprehensive management:

```bash
# Start services
./scripts/docker-deploy.sh start [--profile <profile>] [--build]

# Stop services
./scripts/docker-deploy.sh stop

# Restart services
./scripts/docker-deploy.sh restart

# Show logs
./scripts/docker-deploy.sh logs [--follow] [--service <name>]

# Check status
./scripts/docker-deploy.sh status

# Clean up
./scripts/docker-deploy.sh clean [--volumes]

# Build images
./scripts/docker-deploy.sh build [--no-cache]

# Run tests
./scripts/docker-deploy.sh test
```

### Manual Docker Compose

```bash
# Start specific profile
docker-compose --profile monitoring up -d

# Scale services
docker-compose up -d --scale ai-service=2

# View logs
docker-compose logs -f game-engine

# Stop and remove
docker-compose down --volumes
```

## Testing

### Integration Tests

```bash
# Run full test suite
./scripts/docker-deploy.sh test

# Run specific tests
docker-compose -f docker-compose.yml -f docker/docker-compose.test.yml up test-runner
```

### Manual Testing

```bash
# Create test session
curl -X POST http://localhost:8002/api/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_123",
    "player_ids": ["player1", "player2"],
    "config": {"mode": "tutorial"}
  }'

# Check MCP Gateway
curl http://localhost:8002/api/mcp/tools

# Health check
curl http://localhost:8002/api/health
```

## Monitoring and Logging

### Built-in Monitoring

Access comprehensive metrics:

```bash
# Game engine performance
curl http://localhost:8002/api/status

# Service health
./scripts/docker-deploy.sh status
```

### Prometheus Metrics

When using `--profile monitoring`:

```bash
# View metrics in Prometheus
open http://localhost:9090

# Grafana dashboards
open http://localhost:3000
```

### Log Management

```bash
# Service logs
./scripts/docker-deploy.sh logs --service game-engine

# All logs
docker-compose logs

# Log streaming
docker-compose logs -f --tail=100
```

## Production Deployment

### Security Configuration

1. **Environment Security**:
   ```bash
   # Set secure passwords
   POSTGRES_PASSWORD=secure_random_password
   GRAFANA_ADMIN_PASSWORD=secure_admin_password
   SECRET_KEY=your-secret-key-here
   ```

2. **Network Security**:
   ```bash
   # Use production profile with Nginx
   ./scripts/docker-deploy.sh start --profile production
   ```

3. **SSL/TLS Setup**:
   - Add SSL certificates to `docker/nginx/ssl/`
   - Update `docker/nginx/nginx.conf` for HTTPS

### Resource Management

```yaml
# docker-compose.override.yml
services:
  game-engine:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'

  ai-service:
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
```

### High Availability

```bash
# Scale services
docker-compose up -d --scale game-engine=2 --scale ai-service=2

# Load balancing via Nginx
./scripts/docker-deploy.sh start --profile production
```

## Troubleshooting

### Common Issues

1. **Port Conflicts**:
   ```bash
   # Check port usage
   netstat -tulpn | grep :8002
   
   # Use different ports
   WEBSOCKET_PORT=8012 ./scripts/docker-deploy.sh start
   ```

2. **Memory Issues**:
   ```bash
   # Check resource usage
   docker stats
   
   # Reduce AI service memory
   docker-compose up -d --scale ai-service=0
   ```

3. **Service Health**:
   ```bash
   # Check health status
   docker ps --format "table {{.Names}}\t{{.Status}}"
   
   # Restart unhealthy services
   docker-compose restart game-engine
   ```

### Debug Mode

```bash
# Start with debug logging
LOG_LEVEL=DEBUG ./scripts/docker-deploy.sh start

# Inspect container
docker exec -it apex-game-engine /bin/bash

# Check configuration
docker-compose config
```

### Log Analysis

```bash
# Error pattern search
docker-compose logs | grep ERROR

# Performance analysis
docker-compose logs game-engine | grep "performance"

# AI decision tracking
docker-compose logs ai-service | grep "decision"
```

## Development Workflow

### Local Development

```bash
# Development mode with live reloading
docker-compose up -d
# Code changes are reflected via volume mounts

# Rebuild after dependency changes
./scripts/docker-deploy.sh build --no-cache
```

### Testing Workflow

```bash
# Run tests before deployment
./scripts/docker-deploy.sh test

# Deploy to staging
./scripts/docker-deploy.sh start --profile production

# Monitor deployment
./scripts/docker-deploy.sh status
```

### Container Updates

```bash
# Pull latest base images
./scripts/docker-deploy.sh pull

# Rebuild with updates
./scripts/docker-deploy.sh build

# Rolling update
./scripts/docker-deploy.sh restart
```

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐
│   Game Engine   │    │   AI Service    │
│  (WebSocket +   │◄──►│   (Ollama +     │
│  MCP Gateway)   │    │   Tactical AI)  │
│   Port 8002     │    │   Port 8001     │
│   Port 8004     │    │                 │
└─────────────────┘    └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│     Redis       │    │    Nginx        │
│   (Sessions)    │    │ (Load Balancer) │
│   Port 6379     │    │   Port 80/443   │
└─────────────────┘    └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│  Prometheus     │    │    Grafana      │
│  (Metrics)      │    │  (Dashboards)   │
│   Port 9090     │    │   Port 3000     │
└─────────────────┘    └─────────────────┘
```

## Performance Tuning

### Resource Optimization

```bash
# Monitor resource usage
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Tune memory limits
docker-compose up -d --scale ai-service=1 \
  --memory=2g --cpus=1.0
```

### Network Optimization

```bash
# Check network latency
docker exec apex-game-engine ping ai-service

# Monitor connections
docker exec apex-game-engine netstat -an | grep :8001
```

For detailed configuration options and advanced deployment scenarios, see the individual service documentation in the `docs/` directory.