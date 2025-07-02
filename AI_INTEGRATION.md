# AI WebSocket Integration

This document describes the AI WebSocket integration system that connects the Apex Tactics game engine with the AI service for real-time tactical decision making.

## Overview

The AI integration consists of several key components:

- **AIWebSocketClient**: Handles WebSocket communication with the AI service
- **AIIntegrationManager**: Coordinates AI decision making with game systems
- **WebSocketHandler**: Manages client connections to the game engine

## Architecture

```
Game Engine ←→ AI Integration Manager ←→ AI WebSocket Client ←→ AI Service
     ↕                    ↕                       ↕
 Game Systems        Event Bus              WebSocket Protocol
```

## AI WebSocket Client

### Features

- **Connection Management**: Automatic connection, reconnection with exponential backoff
- **Message Handling**: Structured message types for different AI operations
- **Request Tracking**: Tracks pending AI decision requests with timeouts
- **Heartbeat System**: Maintains connection health with periodic pings

### Message Types

#### Engine to AI Service

- `REQUEST_DECISION`: Request AI decision for a unit
- `GAME_STATE_UPDATE`: Send updated game state
- `UNIT_SPAWN`: Notify of unit spawn
- `UNIT_DEATH`: Notify of unit death
- `BATTLE_START`: Notify of battle start
- `BATTLE_END`: Notify of battle end

#### AI Service to Engine

- `DECISION_RESPONSE`: AI decision for requested unit
- `AI_READY`: AI service ready notification
- `AI_ERROR`: AI service error notification
- `AI_STATUS`: AI service status update

#### Bidirectional

- `PING`/`PONG`: Connection health checks
- `HEARTBEAT`: Keep-alive messages

### Usage Example

```python
from src.engine.integrations.ai_websocket import AIWebSocketClient

client = AIWebSocketClient("ws://localhost:8003/ws", event_bus)
await client.connect()

# Request AI decision
request_id = await client.request_ai_decision(
    session_id="game_123",
    game_state=current_state,
    unit_id="unit_456", 
    available_actions=actions
)
```

## AI Integration Manager

### Features

- **Unit Management**: Tracks AI-controlled units across sessions
- **Decision Coordination**: Manages AI decision requests and execution
- **Control Levels**: Supports multiple AI difficulty levels
- **Game State Building**: Constructs comprehensive game state for AI analysis

### AI Control Levels

1. **SCRIPTED**: Basic scripted behavior patterns
2. **STRATEGIC**: Strategic decision making with game analysis
3. **ADAPTIVE**: Adaptive learning AI that adjusts to player tactics  
4. **LEARNING**: Advanced learning AI with pattern recognition

### Decision Types

- **MOVE**: Unit movement to target position
- **ATTACK**: Attack target unit
- **ABILITY**: Use special ability
- **DEFEND**: Defensive action
- **WAIT**: End turn without action
- **RETREAT**: Withdraw from combat

### Usage Example

```python
from src.engine.integrations.ai_integration import AIIntegrationManager

ai_manager = AIIntegrationManager(ecs, event_bus, battlefield, game_state)
await ai_manager.initialize()

# Set unit AI control level
ai_manager.set_unit_control_level(unit_id, AIControlLevel.ADAPTIVE)
```

## Game State Format

The AI receives comprehensive game state in the following format:

```json
{
  "session_id": "game_123",
  "battlefield": {
    "grid_size": {"width": 10, "height": 10},
    "terrain": [["plains", "forest", ...], ...],
    "units": [
      {
        "unit_id": "unit_456",
        "position": {"x": 5, "y": 3, "z": 0},
        "team": "player1",
        "is_ai": true,
        "stats": {
          "hp": {"current": 80, "max": 100},
          "mp": {"current": 50, "max": 60},
          "attributes": {"strength": 15, "finesse": 12, ...},
          "alive": true
        },
        "movement": {
          "can_move": true,
          "has_moved": false,
          "movement_speed": 3
        },
        "equipment": {
          "attack_bonus": 25,
          "defense_bonus": 18,
          "abilities": ["power_strike", "charge"]
        },
        "status_effects": {
          "active_count": 2,
          "buffs": ["attack_boost"],
          "debuffs": ["slowed"],
          "can_act": true,
          "can_move": true
        }
      }
    ],
    "obstacles": []
  },
  "game_state": {
    "phase": "active",
    "turn_state": {
      "turn_number": 15,
      "current_player": "ai_team",
      "time_remaining": 25.3
    }
  },
  "timestamp": "2024-01-15T10:30:45Z"
}
```

## AI Decision Format

AI decisions are returned in the following format:

```json
{
  "type": "decision_response",
  "request_id": "req_789",
  "decision": {
    "action_type": "move",
    "target_position": {"x": 7, "y": 4},
    "priority": "high"
  },
  "confidence": 0.85,
  "reasoning": "Moving to flank enemy archer while maintaining cover",
  "alternatives": [
    {
      "action_type": "attack",
      "target_id": "enemy_unit_123",
      "confidence": 0.65
    }
  ]
}
```

## Performance Monitoring

The AI integration includes comprehensive performance monitoring:

### Metrics Tracked

- **Connection Status**: WebSocket connection health
- **Decision Times**: Average time for AI decisions
- **Request Queues**: Pending decision requests
- **Error Rates**: Connection and decision failures
- **Unit Counts**: Active AI units per session

### Accessing Statistics

```python
# Get AI integration statistics
stats = ai_manager.get_ai_stats()
print(f"Active AI units: {stats['active_ai_units']}")
print(f"Average decision time: {stats['average_decision_time']:.2f}s")
```

## Configuration

### Environment Variables

```bash
# AI service connection
AI_SERVICE_URL=ws://localhost:8003/ws
AI_REQUEST_TIMEOUT=30.0
AI_RECONNECT_ATTEMPTS=5

# Performance tuning
AI_HEARTBEAT_INTERVAL=10.0
AI_STATE_UPDATE_THROTTLE=1.0
```

### Game Engine Configuration

```python
config = GameConfig(
    ai_difficulty="adaptive",
    turn_time_limit=30.0,
    enable_ai_learning=True
)
```

## Error Handling

The system includes robust error handling:

### Connection Errors

- **Automatic Reconnection**: Exponential backoff strategy
- **Graceful Degradation**: Fallback to scripted AI if connection fails
- **Timeout Handling**: Request timeouts with cleanup

### Decision Errors

- **Validation**: Validates AI decisions before execution
- **Fallback Actions**: Default actions if AI decision is invalid
- **Error Reporting**: Detailed error logging and metrics

## Testing

Run the AI integration tests:

```bash
# Run all AI integration tests
python -m pytest tests/test_ai_integration.py -v

# Run specific test categories
python -m pytest tests/test_ai_integration.py::TestAIWebSocketClient -v
python -m pytest tests/test_ai_integration.py::TestAIIntegrationManager -v
```

## Deployment

### Starting the Game Engine

```bash
# Start with default configuration
python run_game_engine.py

# Start with custom AI service URL
python run_game_engine.py --ai-service-url ws://ai-service:8003/ws

# Start with specific difficulty
python run_game_engine.py --ai-difficulty expert --port 8002
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ src/
COPY run_game_engine.py .

EXPOSE 8002
CMD ["python", "run_game_engine.py", "--host", "0.0.0.0"]
```

## Integration with Phase 2 AI Service

This WebSocket integration is designed to work seamlessly with the AI service implemented in Phase 2:

1. **Compatible Message Format**: Uses the same message structure as Phase 2
2. **Tool Integration**: Supports MCP tool calls for complex analysis
3. **Session Management**: Maintains session state across both services
4. **Scalability**: Supports multiple concurrent game sessions

## Troubleshooting

### Common Issues

1. **Connection Refused**: Ensure AI service is running on specified URL
2. **Decision Timeouts**: Check AI service response times and network latency
3. **Invalid Decisions**: Verify game state format matches AI expectations
4. **Memory Leaks**: Monitor connection cleanup in long-running sessions

### Debug Logging

Enable debug logging for detailed troubleshooting:

```python
import logging
logging.getLogger("src.engine.integrations").setLevel(logging.DEBUG)
```

## Future Enhancements

- **Multi-AI Support**: Support for different AI personalities
- **Learning Persistence**: Save AI learning data between sessions
- **Real-time Analytics**: Live AI decision analysis dashboard
- **A/B Testing**: Compare different AI strategies
- **Tournament Mode**: AI vs AI tournaments with automated analysis