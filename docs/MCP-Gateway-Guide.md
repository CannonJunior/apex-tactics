# MCP Gateway Integration Guide

The Apex Tactics MCP Gateway provides external tool integration using the Model Context Protocol (MCP), allowing external agents and tools to interact with the game engine for analysis, control, and monitoring.

## Overview

The MCP Gateway exposes 13 comprehensive tools for game interaction:

### Game State Tools
- `get_game_sessions()` - List all active game sessions
- `get_session_state(session_id)` - Get detailed session state
- `get_battlefield_state(session_id)` - Get battlefield information
- `get_turn_info(session_id)` - Get current turn information

### Unit Management Tools
- `get_all_units(session_id)` - Get all units in a session
- `get_unit_details(session_id, unit_id)` - Get detailed unit information
- `get_available_actions(session_id, unit_id)` - Get valid actions for a unit

### Action Execution Tools
- `execute_unit_action(session_id, player_id, action)` - Execute unit actions
- `send_notification(session_id, type, title, message, player_id?)` - Send notifications
- `highlight_tiles(session_id, tiles, highlight_type, duration?)` - Highlight battlefield tiles

### Analysis Tools
- `analyze_tactical_situation(session_id, team?)` - Comprehensive tactical analysis
- `get_game_statistics(session_id)` - Performance and game statistics

### Testing Tools
- `create_test_session(battlefield_size?, player_count?)` - Create test sessions

## Usage

### Standalone MCP Gateway

Launch the MCP Gateway as a standalone server:

```bash
# stdio mode (for MCP clients)
python scripts/launch_mcp_gateway.py

# HTTP mode (for testing)
python scripts/launch_mcp_gateway.py --http --port 8004

# With test session
python scripts/launch_mcp_gateway.py --create-test-session
```

### Integrated Game Server

Run the full game server with MCP Gateway:

```bash
# Full server with WebSocket and MCP
python scripts/run_game_with_mcp.py

# Custom ports
python scripts/run_game_with_mcp.py --websocket-port 8002 --mcp-port 8004

# Disable MCP Gateway
python scripts/run_game_with_mcp.py --disable-mcp
```

### Programmatic Integration

Enable MCP Gateway in your game engine:

```python
from src.engine.game_engine import GameEngine, GameConfig

# Create game engine
engine = GameEngine(GameConfig())

# Enable MCP Gateway
await engine.enable_mcp_gateway(port=8004)
```

## Tool Examples

### Tactical Analysis

```python
# Analyze battlefield situation
analysis = await mcp_client.call_tool("analyze_tactical_situation", {
    "session_id": "game_123",
    "team": "player_1"
})

# Returns team strengths, positions, threats, opportunities
```

### Unit Control

```python
# Get available actions for a unit
actions = await mcp_client.call_tool("get_available_actions", {
    "session_id": "game_123",
    "unit_id": "unit_456"
})

# Execute movement action
result = await mcp_client.call_tool("execute_unit_action", {
    "session_id": "game_123",
    "player_id": "player_1",
    "action": {
        "type": "move",
        "unit_id": "unit_456",
        "target_position": {"x": 5, "y": 3}
    }
})
```

### Visual Feedback

```python
# Highlight movement range
await mcp_client.call_tool("highlight_tiles", {
    "session_id": "game_123",
    "tiles": [{"x": 4, "y": 3}, {"x": 5, "y": 3}, {"x": 6, "y": 3}],
    "highlight_type": "movement",
    "duration": 5.0
})

# Send notification
await mcp_client.call_tool("send_notification", {
    "session_id": "game_123",
    "type": "info",
    "title": "AI Move",
    "message": "AI unit moved to strategic position",
    "player_id": "player_1"
})
```

## Configuration

### Environment Variables

- `MCP_GATEWAY_PORT` - Default port for MCP Gateway (default: 8004)
- `WEBSOCKET_PORT` - Default port for WebSocket server (default: 8002)
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)

### Command Line Options

#### MCP Gateway Launcher

```bash
python scripts/launch_mcp_gateway.py --help
```

- `--port` - MCP Gateway port (default: 8004)
- `--http` - Use HTTP mode for testing
- `--log-level` - Set logging level
- `--create-test-session` - Create test session on startup

#### Integrated Server

```bash
python scripts/run_game_with_mcp.py --help
```

- `--websocket-port` - WebSocket server port (default: 8002)
- `--mcp-port` - MCP Gateway port (default: 8004)
- `--disable-mcp` - Disable MCP Gateway
- `--mode` - Default game mode (single_player, multiplayer, ai_vs_ai, tutorial)

## Health Monitoring

### Health Check Endpoints

Access server health status:

```bash
# Basic health check
curl http://localhost:8002/api/health

# MCP tools list
curl http://localhost:8002/api/mcp/tools

# Server status with performance metrics
curl http://localhost:8002/api/status
```

### Performance Metrics

The MCP Gateway provides comprehensive performance statistics:

- FPS and frame timing
- Active sessions and connections
- AI integration statistics
- UI system performance
- Notification system metrics

## Error Handling

The MCP Gateway includes robust error handling:

- Session validation for all operations
- Permission checks for player actions
- Graceful degradation on component failures
- Comprehensive error messages with context

## Security Considerations

- Session-based access control
- Player permission validation
- Input sanitization and validation
- Rate limiting on action execution
- Audit logging for all tool calls

## Integration Examples

### External AI Agent

```python
import asyncio
from mcp_client import MCPClient

async def ai_agent_turn(session_id, player_id):
    client = MCPClient("stdio://python scripts/launch_mcp_gateway.py")
    
    # Analyze battlefield
    analysis = await client.call_tool("analyze_tactical_situation", {
        "session_id": session_id,
        "team": player_id
    })
    
    # Get all units
    units = await client.call_tool("get_all_units", {"session_id": session_id})
    
    # Make tactical decisions and execute actions
    for unit in units:
        if unit["team"] == player_id and unit["stats"]["alive"]:
            actions = await client.call_tool("get_available_actions", {
                "session_id": session_id,
                "unit_id": unit["unit_id"]
            })
            
            # AI decision logic here...
            best_action = choose_best_action(unit, actions, analysis)
            
            await client.call_tool("execute_unit_action", {
                "session_id": session_id,
                "player_id": player_id,
                "action": best_action
            })
```

### Game Analytics Tool

```python
async def collect_game_metrics(session_id):
    client = MCPClient("http://localhost:8004")
    
    # Get comprehensive statistics
    stats = await client.call_tool("get_game_statistics", {
        "session_id": session_id
    })
    
    # Analyze battlefield state
    battlefield = await client.call_tool("get_battlefield_state", {
        "session_id": session_id
    })
    
    # Generate analytics report
    return generate_analytics_report(stats, battlefield)
```

## Troubleshooting

### Common Issues

1. **Connection Refused**: Check that the MCP Gateway is running on the correct port
2. **Session Not Found**: Verify session ID and ensure game session is active
3. **Permission Denied**: Check player ID and turn ownership
4. **Tool Not Found**: Ensure you're using the correct tool name and parameters

### Debug Mode

Enable debug logging for detailed troubleshooting:

```bash
python scripts/launch_mcp_gateway.py --log-level DEBUG
```

### Testing MCP Tools

Use the HTTP mode for interactive testing:

```bash
# Start in HTTP mode
python scripts/launch_mcp_gateway.py --http --create-test-session

# Test tools via HTTP
curl -X POST http://localhost:8004/mcp/call \
  -H "Content-Type: application/json" \
  -d '{"tool": "get_game_sessions", "args": {}}'
```