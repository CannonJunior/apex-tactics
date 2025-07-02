"""
Pytest configuration and fixtures for Apex Tactics integration tests.

Provides shared fixtures for game engine, sessions, and test utilities.
"""

import asyncio
import pytest
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

import httpx
import websockets
import structlog

from src.engine.game_engine import GameEngine, GameConfig, GameMode
from src.core.ecs import EntityID

logger = structlog.get_logger()


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def game_engine():
    """Create a test game engine instance"""
    config = GameConfig(
        mode=GameMode.TUTORIAL,
        battlefield_size=(8, 8),
        max_turns=20,
        turn_time_limit=10.0,
        ai_difficulty="easy"
    )
    
    engine = GameEngine(config)
    yield engine
    
    # Cleanup
    await engine.shutdown()


@pytest.fixture
async def test_session(game_engine):
    """Create a test game session"""
    session_id = f"test_session_{datetime.now().timestamp()}"
    player_ids = ["player_1", "player_2"]
    
    session = await game_engine.create_session(session_id, player_ids)
    await game_engine.start_game(session_id)
    
    yield session_id, player_ids, session
    
    # Cleanup
    await game_engine.cleanup_session(session_id)


@pytest.fixture
async def http_client():
    """HTTP client for API testing"""
    async with httpx.AsyncClient(base_url="http://localhost:8002") as client:
        yield client


@pytest.fixture
async def websocket_client():
    """WebSocket client for real-time testing"""
    uri = "ws://localhost:8002/ws/test_session"
    
    async with websockets.connect(uri) as websocket:
        yield websocket


@pytest.fixture
async def mcp_client():
    """MCP client for testing MCP Gateway"""
    async with httpx.AsyncClient(base_url="http://localhost:8004") as client:
        yield client


@pytest.fixture
def sample_unit_data():
    """Sample unit data for testing"""
    return {
        "unit_id": "test_unit_001",
        "position": {"x": 2, "y": 2, "z": 0},
        "team": "player_1",
        "stats": {
            "hp": {"current": 100, "max": 100},
            "mp": {"current": 50, "max": 50},
            "attributes": {
                "strength": 10,
                "fortitude": 8,
                "finesse": 12,
                "wisdom": 9,
                "wonder": 7,
                "worthy": 11,
                "faith": 6,
                "spirit": 8,
                "speed": 10
            }
        }
    }


@pytest.fixture
def sample_action_data():
    """Sample action data for testing"""
    return {
        "type": "move",
        "unit_id": "test_unit_001",
        "target_position": {"x": 3, "y": 3}
    }


@pytest.fixture
async def populated_session(game_engine, test_session):
    """Session with units and battlefield setup"""
    session_id, player_ids, session = test_session
    
    # Add test units
    test_units = [
        {
            "entity_id": EntityID("unit_001"),
            "team": "player_1",
            "position": (1, 1),
            "stats": {"hp": 100, "mp": 50}
        },
        {
            "entity_id": EntityID("unit_002"),
            "team": "player_1", 
            "position": (2, 1),
            "stats": {"hp": 80, "mp": 40}
        },
        {
            "entity_id": EntityID("unit_003"),
            "team": "player_2",
            "position": (6, 6),
            "stats": {"hp": 90, "mp": 60}
        },
        {
            "entity_id": EntityID("unit_004"),
            "team": "player_2",
            "position": (7, 6),
            "stats": {"hp": 120, "mp": 30}
        }
    ]
    
    # Initialize units in the game engine
    for unit in test_units:
        await _create_test_unit(game_engine, session_id, unit)
    
    yield session_id, player_ids, session, test_units


async def _create_test_unit(game_engine, session_id: str, unit_data: Dict[str, Any]):
    """Helper to create a test unit in the game engine"""
    from src.engine.components.position_component import PositionComponent
    from src.engine.components.stats_component import StatsComponent
    from src.engine.components.team_component import TeamComponent
    
    entity_id = unit_data["entity_id"]
    
    # Create entity
    entity = game_engine.ecs.create_entity(entity_id)
    
    # Add position component
    position = PositionComponent(
        x=unit_data["position"][0],
        y=unit_data["position"][1],
        z=0
    )
    game_engine.ecs.add_component(entity_id, position)
    
    # Add stats component
    stats = StatsComponent(
        max_hp=unit_data["stats"]["hp"],
        current_hp=unit_data["stats"]["hp"],
        max_mp=unit_data["stats"]["mp"],
        current_mp=unit_data["stats"]["mp"]
    )
    game_engine.ecs.add_component(entity_id, stats)
    
    # Add team component
    team = TeamComponent(
        team=unit_data["team"],
        is_ai=(unit_data["team"] == "player_2")  # Make player_2 AI for testing
    )
    game_engine.ecs.add_component(entity_id, team)


@pytest.fixture
def test_timeouts():
    """Timeout values for different test operations"""
    return {
        "api_request": 5.0,
        "websocket_message": 3.0,
        "game_action": 10.0,
        "ai_decision": 15.0,
        "session_start": 20.0
    }


class TestUtilities:
    """Utility functions for testing"""
    
    @staticmethod
    async def wait_for_condition(condition_func, timeout: float = 5.0, interval: float = 0.1):
        """Wait for a condition to become true"""
        import time
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if await condition_func():
                return True
            await asyncio.sleep(interval)
        
        return False
    
    @staticmethod
    async def send_websocket_message(websocket, message_type: str, data: Dict[str, Any]):
        """Send a message via WebSocket and return response"""
        message = {
            "type": message_type,
            "data": data
        }
        
        await websocket.send(json.dumps(message))
        response = await websocket.recv()
        return json.loads(response)
    
    @staticmethod
    async def wait_for_websocket_message(websocket, expected_type: str, timeout: float = 5.0):
        """Wait for a specific WebSocket message type"""
        try:
            while True:
                message = await asyncio.wait_for(websocket.recv(), timeout=timeout)
                data = json.loads(message)
                
                if data.get("type") == expected_type:
                    return data
                    
        except asyncio.TimeoutError:
            return None


@pytest.fixture
def test_utils():
    """Test utility functions"""
    return TestUtilities