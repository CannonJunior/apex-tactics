# Testing Guide

Comprehensive testing guide for the Apex Tactics game engine, covering unit tests, integration tests, and performance testing.

## Overview

The testing suite includes:

- **Integration Tests**: End-to-end system testing with all services
- **Unit Tests**: Fast, isolated component testing  
- **Performance Tests**: Load testing and benchmarking
- **Docker Tests**: Containerized environment testing

## Test Structure

```
tests/
├── conftest.py                 # Shared fixtures and utilities
├── pytest.ini                 # Pytest configuration
├── integration/                # Integration test suites
│   ├── test_game_engine_integration.py
│   ├── test_websocket_integration.py
│   ├── test_mcp_gateway_integration.py
│   ├── test_ai_service_integration.py
│   ├── test_ui_systems_integration.py
│   └── test_full_system_integration.py
└── unit/                      # Unit tests (future)
    └── test_components.py
```

## Quick Start

### Prerequisites

Ensure all services are running:

```bash
# Start all services
./scripts/docker-deploy.sh start

# Check service health
./scripts/docker-deploy.sh status
```

### Running Tests

```bash
# Run all integration tests
python scripts/run_tests.py integration

# Run specific test categories
python scripts/run_tests.py integration --markers "websocket"
python scripts/run_tests.py integration --markers "mcp"
python scripts/run_tests.py integration --markers "not slow"

# Run with verbose output
python scripts/run_tests.py integration -v

# Run specific test file
python scripts/run_tests.py integration --test-pattern "tests/integration/test_websocket_integration.py"
```

### Docker Testing

```bash
# Run tests in Docker environment
./scripts/docker-deploy.sh test

# Run specific test profile
docker-compose -f docker-compose.yml -f docker/docker-compose.test.yml up test-runner
```

## Test Categories

### Integration Tests

#### Game Engine Integration
- **File**: `test_game_engine_integration.py`
- **Coverage**: Session lifecycle, turn system, combat, AI integration
- **Key Tests**:
  - `test_session_lifecycle`: Complete session creation to cleanup
  - `test_multiple_sessions`: Concurrent session handling
  - `test_turn_system_integration`: Turn progression with real units
  - `test_unit_actions_integration`: Movement and action execution
  - `test_combat_system_integration`: Unit combat mechanics
  - `test_performance_tracking`: Engine performance metrics

#### WebSocket Integration
- **File**: `test_websocket_integration.py`
- **Coverage**: Real-time communication, multiplayer updates
- **Key Tests**:
  - `test_websocket_connection`: Basic connection and handshake
  - `test_websocket_player_actions`: Action execution via WebSocket
  - `test_multiple_websocket_connections`: Concurrent connections
  - `test_websocket_real_time_updates`: Cross-player update propagation
  - `test_websocket_message_throughput`: Performance testing

#### MCP Gateway Integration
- **File**: `test_mcp_gateway_integration.py`  
- **Coverage**: External tool integration, MCP protocol
- **Key Tests**:
  - `test_mcp_tools_list`: Available tool enumeration
  - `test_create_test_session_tool`: Session creation via MCP
  - `test_analyze_tactical_situation_tool`: AI analysis integration
  - `test_mcp_concurrent_requests`: Load testing
  - `test_mcp_ai_agent_workflow`: Complete AI agent scenario

#### AI Service Integration
- **File**: `test_ai_service_integration.py`
- **Coverage**: AI decision making, difficulty scaling, learning
- **Key Tests**:
  - `test_ai_decision_making`: Tactical decision generation
  - `test_ai_difficulty_scaling`: Adaptive difficulty adjustment
  - `test_ai_multi_unit_coordination`: Multi-unit strategy
  - `test_ai_decision_speed`: Performance benchmarking
  - `test_full_ai_game_scenario`: Complete AI vs AI game

#### UI Systems Integration
- **File**: `test_ui_systems_integration.py`
- **Coverage**: Visual feedback, notifications, real-time UI
- **Key Tests**:
  - `test_notification_system`: Notification creation and delivery
  - `test_tile_highlighting_system`: Battlefield visual feedback
  - `test_real_time_ui_updates`: WebSocket UI synchronization
  - `test_notification_types_and_priorities`: Comprehensive notification testing
  - `test_ui_session_isolation`: Multi-session UI isolation

#### Full System Integration
- **File**: `test_full_system_integration.py`
- **Coverage**: End-to-end scenarios, system interactions
- **Key Tests**:
  - `test_complete_game_session_lifecycle`: Full game workflow
  - `test_multi_player_scenario`: Real multiplayer gameplay
  - `test_ai_vs_ai_scenario`: AI vs AI game progression
  - `test_system_performance_under_load`: Concurrent load testing
  - `test_error_propagation_and_recovery`: Error handling across systems

## Test Configuration

### Pytest Configuration (`pytest.ini`)

```ini
[tool:pytest]
addopts = -ra --strict-markers -v --tb=short --asyncio-mode=auto
testpaths = tests
markers =
    integration: integration tests (may be slow)
    websocket: requires WebSocket server
    mcp: requires MCP Gateway
    ai: requires AI Service
    slow: slow tests (deselect with '-m "not slow"')
    performance: performance measurement tests
timeout = 300
```

### Test Markers

Use markers to categorize and filter tests:

```bash
# Run only fast tests
pytest -m "not slow"

# Run WebSocket-specific tests
pytest -m "websocket"

# Run MCP Gateway tests  
pytest -m "mcp"

# Run performance tests
pytest -m "performance"

# Combine markers
pytest -m "integration and not slow"
```

## Fixtures and Utilities

### Core Fixtures (`conftest.py`)

- **`game_engine`**: Test game engine instance
- **`test_session`**: Created and started game session
- **`populated_session`**: Session with test units placed
- **`http_client`**: HTTP client for API testing
- **`websocket_client`**: WebSocket client for real-time testing
- **`mcp_client`**: MCP Gateway HTTP client
- **`test_utils`**: Utility functions for testing

### Test Utilities

```python
# Wait for conditions
await test_utils.wait_for_condition(
    lambda: check_condition(),
    timeout=5.0
)

# Send WebSocket messages
response = await test_utils.send_websocket_message(
    websocket, "player_action", {"type": "move"}
)

# Wait for specific message types
message = await test_utils.wait_for_websocket_message(
    websocket, "action_result", timeout=5.0
)
```

## Running Specific Test Scenarios

### Smoke Tests (Fast)

```bash
# Quick validation of core functionality
python scripts/run_tests.py smoke

# Equivalent to:
python scripts/run_tests.py integration -m "not slow"
```

### Performance Tests

```bash
# Run performance benchmarks
python scripts/run_tests.py performance

# Specific performance categories
pytest -m "performance" tests/integration/test_websocket_integration.py::TestWebSocketPerformance
```

### Service-Specific Tests

```bash
# Test only WebSocket functionality
pytest -m "websocket" tests/integration/

# Test only MCP Gateway
pytest -m "mcp" tests/integration/test_mcp_gateway_integration.py

# Test only AI Service
pytest -m "ai" tests/integration/test_ai_service_integration.py
```

### Docker Environment Tests

```bash
# Run full test suite in Docker
./scripts/docker-deploy.sh test

# Run with custom configuration
docker-compose -f docker-compose.yml -f docker/docker-compose.test.yml up test-runner

# Interactive testing
docker-compose exec test-runner python -m pytest tests/integration/ -v
```

## Continuous Integration

### GitHub Actions Integration

```yaml
name: Integration Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Start services
        run: ./scripts/docker-deploy.sh start --profile testing
      - name: Run integration tests
        run: python scripts/run_tests.py integration --output-file test-results.xml
      - name: Upload test results
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: test-results.xml
```

### Test Reports

```bash
# Generate comprehensive test report
python scripts/run_tests.py integration --generate-report

# Outputs:
# - htmlcov/index.html (coverage report)
# - test-results.xml (JUnit format)
# - test_reports/ (summary reports)
```

## Troubleshooting

### Common Issues

1. **Services Not Ready**
   ```bash
   # Check service health
   curl http://localhost:8002/api/health
   curl http://localhost:8004/health
   curl http://localhost:8001/health
   
   # Restart services
   ./scripts/docker-deploy.sh restart
   ```

2. **WebSocket Connection Issues**
   ```bash
   # Check WebSocket endpoint
   wscat -c ws://localhost:8002/ws/test_session
   
   # Check firewall/port access
   netstat -tulpn | grep :8002
   ```

3. **Test Timeouts**
   ```bash
   # Run with longer timeout
   pytest --timeout=600 tests/integration/
   
   # Skip slow tests
   pytest -m "not slow" tests/integration/
   ```

4. **Memory Issues**
   ```bash
   # Monitor resource usage
   docker stats
   
   # Reduce concurrent tests
   pytest -n 1 tests/integration/
   ```

### Debug Mode

```bash
# Run with debug logging
LOG_LEVEL=DEBUG python scripts/run_tests.py integration

# Run specific test with debug output
pytest -s -vv tests/integration/test_websocket_integration.py::TestWebSocketIntegration::test_websocket_connection

# Enable asyncio debug mode
PYTHONASYNCIODEBUG=1 pytest tests/integration/
```

### Service Logs

```bash
# View service logs during testing
./scripts/docker-deploy.sh logs --follow --service game-engine

# View all logs
docker-compose logs -f

# View specific service logs
docker logs apex-game-engine
```

## Performance Benchmarks

### Target Performance Metrics

- **WebSocket Message Throughput**: >5 messages/second
- **API Response Time**: <1 second for simple operations
- **MCP Tool Response Time**: <5 seconds for complex operations
- **AI Decision Time**: <5 seconds for simple scenarios
- **Session Creation Time**: <5 seconds
- **Memory Usage**: <2GB total for full system

### Performance Test Examples

```python
# WebSocket throughput test
async def test_websocket_throughput():
    message_count = 100
    start_time = time.time()
    
    for i in range(message_count):
        await websocket.send(json.dumps({"type": "ping"}))
        await websocket.recv()
    
    duration = time.time() - start_time
    throughput = message_count / duration
    assert throughput > 5  # messages per second

# API response time test  
async def test_api_response_time():
    start_time = time.time()
    response = await client.get("/api/sessions/test/state")
    response_time = time.time() - start_time
    
    assert response_time < 1.0  # less than 1 second
    assert response.status_code == 200
```

## Contributing Tests

### Writing New Tests

1. **Choose appropriate test category** (integration vs unit)
2. **Use existing fixtures** when possible
3. **Follow naming conventions** (`test_*` functions)
4. **Add appropriate markers** (`@pytest.mark.integration`)
5. **Include docstrings** explaining test purpose
6. **Handle service availability** with skip conditions

### Test Guidelines

- **Isolation**: Tests should not depend on each other
- **Cleanup**: Always clean up created resources
- **Timeouts**: Use reasonable timeouts for async operations
- **Error Handling**: Test both success and failure cases
- **Documentation**: Include clear descriptions of test scenarios

### Example Test Structure

```python
class TestNewFeature:
    """Test new feature integration"""
    
    async def test_feature_basic_functionality(self, test_utils):
        """Test basic feature operation"""
        try:
            # Test implementation
            result = await some_operation()
            assert result is not None
            
        except Exception as e:
            pytest.skip(f"Service not available: {e}")
    
    async def test_feature_error_handling(self):
        """Test feature error conditions"""
        # Test error scenarios
        with pytest.raises(ValueError):
            await invalid_operation()
    
    @pytest.mark.slow
    async def test_feature_performance(self):
        """Test feature performance characteristics"""
        # Performance testing
        start_time = time.time()
        await performance_operation()
        duration = time.time() - start_time
        
        assert duration < 5.0  # Performance requirement
```

For detailed API documentation and system architecture, see the main project documentation.