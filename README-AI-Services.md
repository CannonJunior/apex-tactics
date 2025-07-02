# Apex Tactics AI Services Architecture

This document describes the implementation of the AI game service architecture for Apex Tactics, featuring a 3-container microservices setup with Model Context Protocol (MCP) integration.

## Architecture Overview

The system consists of three main services:

1. **Game Engine API** (Port 8000) - Core game logic and state management
2. **MCP Gateway** (Port 8002) - Model Context Protocol tools for AI interaction
3. **AI Service** (Port 8001) - Ollama-powered AI decision making

## Services Details

### Game Engine API (`src/api/game_engine.py`)

**Responsibilities:**
- Game session management
- Unit movement and combat logic
- Real-time WebSocket connections
- RESTful API for game operations

**Key Endpoints:**
- `POST /sessions` - Create new game session
- `GET /sessions/{id}/state` - Get current game state
- `POST /sessions/{id}/actions/move` - Execute unit movement
- `POST /sessions/{id}/actions/attack` - Execute unit attacks
- `WS /sessions/{id}/ws` - Real-time updates

### MCP Gateway (`src/mcp/gateway.py`)

**Responsibilities:**
- Provides MCP tools for AI agents
- Analyzes battlefield conditions
- Proxies requests to game engine
- Tactical and strategic analysis

**Available MCP Tools:**
- `move_unit` - Move units on battlefield
- `attack_unit` - Execute attacks
- `get_game_state` - Retrieve current state
- `analyze_battlefield` - Tactical analysis
- `get_available_actions` - Query unit capabilities
- `end_turn` - End unit turns
- `cast_spell` - Magic actions (planned)
- `use_item` - Inventory actions (planned)

### AI Service (`src/ai/service.py`)

**Responsibilities:**
- Ollama model management
- AI decision making for units
- Strategic and tactical analysis
- Chat interface for strategy advice

**Key Features:**
- Multiple difficulty levels (easy/normal/hard/expert)
- Model hot-swapping
- Performance metrics
- Tactical reasoning with LLMs

## Installation and Setup

### Prerequisites

- Docker and Docker Compose
- 4GB+ RAM (for Ollama models)
- Python 3.11+ (for development)

### Quick Start

1. **Clone and navigate to project:**
```bash
cd /home/junior/src/apex-tactics
```

2. **Build and start all services:**
```bash
docker-compose up --build
```

3. **Run integration tests:**
```bash
./scripts/test-services.sh
```

### Manual Testing

1. **Check service health:**
```bash
curl http://localhost:8000/health  # Game Engine
curl http://localhost:8001/health  # AI Service  
curl http://localhost:8002/health  # MCP Gateway
```

2. **Create a game session:**
```bash
curl -X POST "http://localhost:8000/sessions?session_id=test123"
```

3. **Get MCP tools:**
```bash
curl http://localhost:8002/mcp/tools
```

4. **Test AI chat:**
```bash
curl -X POST "http://localhost:8001/ai/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is a good opening strategy?"}'
```

## Development Workflow

### Adding New MCP Tools

1. Create tool class in `src/mcp/tools.py`:
```python
class NewActionTool(Tool):
    def __init__(self, game_client: GameEngineClient):
        super().__init__(
            name="new_action",
            description="Description of the action",
            parameters_schema={...}
        )
    
    async def execute(self, **kwargs):
        # Implementation
        pass
```

2. Register in `src/mcp/gateway.py`:
```python
tools = [
    # ... existing tools
    NewActionTool(game_client),
]
```

### Extending AI Capabilities

1. Add new analysis types in `src/ai/service.py`
2. Implement specialized AI engines for different aspects
3. Add new Ollama model configurations

### Configuration Management

The services use environment variables for configuration:

```yaml
environment:
  - ENVIRONMENT=development  # development, production, test
  - LOG_LEVEL=info          # debug, info, warning, error
  - AI_SERVICE_URL=http://ai-service:8001
  - MCP_GATEWAY_URL=http://mcp-gateway:8002
```

## API Documentation

### Game Engine API

Full OpenAPI documentation available at: `http://localhost:8000/docs`

### MCP Gateway API

- `GET /mcp/tools` - List available tools
- `POST /mcp/call-tool` - Execute MCP tool
- `GET /game/sessions/{id}/state` - Proxy game state
- `POST /game/sessions/{id}/analyze` - Battlefield analysis

### AI Service API

- `POST /ai/decide` - Make AI decision for unit
- `POST /ai/analyze/tactical` - Tactical analysis
- `POST /ai/analyze/strategic` - Strategic analysis
- `GET /ai/models` - List Ollama models
- `POST /ai/chat` - Chat with AI advisor

## Performance Considerations

### Resource Requirements

- **Game Engine**: 512MB RAM minimum
- **AI Service**: 2GB RAM minimum (for Ollama models)  
- **MCP Gateway**: 256MB RAM minimum

### Scaling

- Game Engine can be scaled horizontally with session partitioning
- AI Service benefits from GPU acceleration for larger models
- MCP Gateway is stateless and scales easily

### Monitoring

Services expose Prometheus metrics at `/metrics` endpoints:
- Request rates and response times
- Game session counts
- AI decision performance
- Ollama model usage

## Security

### Authentication

Currently using development mode with no authentication. For production:

1. Add JWT authentication to all services
2. Implement API rate limiting
3. Add RBAC for different user types

### Network Security

- Services communicate within Docker network
- Only necessary ports exposed externally
- Add TLS termination at load balancer

## Troubleshooting

### Common Issues

1. **Ollama models not downloading:**
   ```bash
   docker exec -it apex-ai-service ollama pull llama2:7b
   ```

2. **Services not communicating:**
   - Check Docker network configuration
   - Verify service URLs in environment variables
   - Check firewall/port blocking

3. **High memory usage:**
   - Reduce Ollama model size
   - Implement model switching
   - Add memory limits to containers

### Logs

View service logs:
```bash
docker-compose logs -f game-engine
docker-compose logs -f ai-service  
docker-compose logs -f mcp-gateway
```

### Health Checks

All services provide health endpoints that return:
```json
{
  "status": "healthy",
  "service": "service-name", 
  "version": "1.0.0",
  "additional_info": {...}
}
```

## Roadmap

### Phase 2 Enhancements (Weeks 3-4)
- WebSocket integration between all services
- Advanced AI personality system
- Performance optimization
- Comprehensive testing suite

### Phase 3 Features (Weeks 5-6) 
- Multi-player support
- AI learning from game outcomes
- Advanced tactical patterns
- Real-time strategy adaptation

### Phase 4 Production (Weeks 7-8)
- Authentication and authorization
- Horizontal scaling
- Monitoring and alerting
- Load balancing

## Contributing

1. Follow the existing code structure
2. Add tests for new features
3. Update API documentation
4. Test with integration suite

## License

Part of the Apex Tactics project - see main project LICENSE file.