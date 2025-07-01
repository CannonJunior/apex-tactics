# MCP Server Registry

This document tracks all MCP servers, their tools, resources, prompts, and templates in the tactical RPG engine.

## Active MCP Servers

### TacticalRPG_AI_Server
**Location**: @src/ai/mcp/tactical_server.py
**Purpose**: AI decision making and tactical analysis for combat scenarios
**Status**: Implemented (Phase 1 Complete)
**Port**: 8765 (configurable)

#### Tools
- `analyze_tactical_situation(unit_id: str)` - Comprehensive battlefield analysis for AI decision-making
  - Returns: position_value, threat_assessment, action_opportunities, resource_status
  - Performance: Real-time analysis with caching
  - Error handling: Graceful fallback for missing units

- `execute_complex_action(unit_id: str, action_type: str, parameters: Dict)` - Execute tactical actions with full validation
  - Supports: All action types with parameter validation
  - Returns: Execution result with success status and feedback
  - Logging: All actions logged for debugging

- `evaluate_position_value(position_x: float, position_y: float, position_z: float, unit_id: str = None)` - Calculate tactical value of battlefield position
  - Factors: Cover value, visibility, mobility, strategic importance
  - Context-aware: Optional unit_id for personalized evaluation
  - Performance: Fast calculation for real-time use

- `predict_battle_outcome(scenario_data: str)` - Predict likely battle outcomes based on current state
  - Input: JSON string containing battle scenario
  - Analysis: Victory probability, duration estimate, key factors
  - Strategy: Recommended tactical approach

#### Resources
- `tactical_state` - Current tactical battle state and unit positions
  - Contains: entity_count, world_stats, unit positions and components
  - Format: JSON with timestamp and metadata
  - Limit: First 10 entities for performance

- `unit_capabilities` - Available actions and abilities for units
  - Actions: move, attack, defend, wait
  - Categories: combat, movement, support abilities
  - Extensible: Easy to add new capabilities

#### Implementation Details
- **FastMCP Integration**: Uses FastMCP library with graceful fallback
- **Performance Monitoring**: All tool calls tracked for optimization
- **Error Recovery**: Comprehensive error handling prevents server crashes
- **Thread Safety**: Safe for concurrent AI agent access
- **Extensibility**: Easy to add new tools and resources

#### Usage Example
```python
# Start MCP server
mcp_server = TacticalMCPServer(world=game_world)
mcp_server.start()

# AI agents can now call tools via MCP protocol
analysis = mcp_client.call_tool("analyze_tactical_situation", unit_id="unit_123")
```

### Planned MCP Servers

#### AssetManager_MCP_Server
**Planned Location**: @src/core/assets/mcp_server.py
**Purpose**: Asset management and streaming coordination
**Phase**: Phase 2-3
**Planned Tools**:
- `load_asset_with_dependencies(asset_id: str)`
- `stream_environment_zone(zone_id: str)`
- `generate_asset_variation(base_id: str, params: Dict)`

#### ProceduralGen_MCP_Server
**Planned Location**: @src/game/procedural/mcp_server.py
**Purpose**: Procedural level and content generation
**Phase**: Phase 3-4
**Planned Tools**:
- `generate_tactical_map(parameters: Dict)`
- `create_asset_variation(asset_id: str, variation_rules: Dict)`
- `populate_environment(zone_id: str, density: float)`

#### PerformanceMonitor_MCP_Server
**Planned Location**: @src/core/performance/mcp_server.py
**Purpose**: Real-time performance monitoring and optimization
**Phase**: Phase 4-5
**Planned Tools**:
- `get_performance_metrics()`
- `optimize_memory_usage()`
- `analyze_frame_time_bottlenecks()`

## MCP Integration Patterns

### Standard Tool Registration
```python
from fastmcp import FastMCP

mcp = FastMCP("ServerName")

@mcp.tool
def tool_name(param: str) -> Dict[str, Any]:
    """Tool description for AI agents"""
    # Implementation
    return result
```

### Resource Registration
```python
@mcp.resource("resource_name")
def get_resource() -> str:
    """Resource description"""
    return json.dumps(data)
```

### Error Handling Pattern
```python
@mcp.tool
def safe_tool(param: str) -> Dict[str, Any]:
    try:
        result = perform_operation(param)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

## Development Guidelines

### Tool Naming Convention
- Use descriptive verbs: `analyze_`, `execute_`, `evaluate_`, `predict_`
- Include context: `tactical_`, `battle_`, `unit_`
- Be specific: `position_value` not just `value`

### Response Format Standards
All tools should return consistent response formats:
```python
{
    "success": bool,
    "data": Any,          # Main response data
    "metadata": Dict,     # Additional context
    "error": str          # Error message if success=False
}
```

### Security Considerations
- Validate all input parameters
- Limit resource-intensive operations
- Implement rate limiting for expensive tools
- Log all tool invocations for debugging

## Testing MCP Servers

### Local Testing
```bash
# Start MCP server locally
python -m src.ai.mcp.tactical_server

# Test tool invocation
mcp-client call analyze_tactical_situation --unit_id "unit_123"
```

### Integration Testing
- Test all tools with various input scenarios
- Verify resource access patterns
- Check error handling and edge cases
- Performance testing under load

Additional MCP servers will be documented here as they are implemented.