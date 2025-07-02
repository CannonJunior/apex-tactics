"""
Test AI Integration

Tests for the AI WebSocket integration and decision-making system.
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

from src.engine.integrations.ai_websocket import AIWebSocketClient, AIMessageType
from src.engine.integrations.ai_integration import AIIntegrationManager, AIControlLevel
from src.core.events import EventBus, GameEvent, EventType
from src.core.ecs import ECSManager, EntityID
from src.engine.battlefield import BattlefieldManager
from src.engine.game_state import GameStateManager


class TestAIWebSocketClient:
    """Test AI WebSocket client functionality"""
    
    @pytest.fixture
    def event_bus(self):
        return EventBus()
    
    @pytest.fixture
    def ai_client(self, event_bus):
        return AIWebSocketClient("ws://localhost:8003/ws", event_bus)
    
    def test_ai_client_initialization(self, ai_client):
        """Test AI client initializes correctly"""
        assert ai_client.ai_service_url == "ws://localhost:8003/ws"
        assert not ai_client.is_connected
        assert ai_client.websocket is None
        assert len(ai_client.pending_requests) == 0
    
    @pytest.mark.asyncio
    async def test_message_handling(self, ai_client):
        """Test message processing"""
        # Test decision response handling
        decision_data = {
            "type": AIMessageType.DECISION_RESPONSE.value,
            "request_id": "test_request",
            "decision": {
                "action_type": "move",
                "target_position": {"x": 5, "y": 5}
            },
            "confidence": 0.8,
            "reasoning": "Strategic positioning"
        }
        
        # Add pending request
        ai_client.pending_requests["test_request"] = {
            "session_id": "test_session",
            "unit_id": "test_unit"
        }
        
        await ai_client._process_message(decision_data)
        
        # Request should be removed after processing
        assert "test_request" not in ai_client.pending_requests
    
    def test_connection_status(self, ai_client):
        """Test connection status reporting"""
        status = ai_client.get_connection_status()
        
        assert "is_connected" in status
        assert "service_url" in status
        assert "pending_requests" in status
        assert "reconnect_attempts" in status
        assert status["is_connected"] is False
        assert status["service_url"] == "ws://localhost:8003/ws"


class TestAIIntegrationManager:
    """Test AI Integration Manager functionality"""
    
    @pytest.fixture
    def ecs(self):
        return ECSManager()
    
    @pytest.fixture
    def event_bus(self):
        return EventBus()
    
    @pytest.fixture
    def battlefield(self):
        return BattlefieldManager((10, 10))
    
    @pytest.fixture
    def game_state(self):
        return GameStateManager()
    
    @pytest.fixture
    def ai_integration(self, ecs, event_bus, battlefield, game_state):
        return AIIntegrationManager(ecs, event_bus, battlefield, game_state)
    
    def test_ai_integration_initialization(self, ai_integration):
        """Test AI integration manager initializes correctly"""
        assert ai_integration.ecs is not None
        assert ai_integration.event_bus is not None
        assert ai_integration.battlefield is not None
        assert ai_integration.game_state is not None
        assert len(ai_integration.ai_units) == 0
        assert len(ai_integration.pending_decisions) == 0
    
    @pytest.mark.asyncio
    async def test_ai_unit_registration(self, ai_integration):
        """Test AI unit registration and management"""
        session_id = "test_session"
        entity_id = EntityID("test_unit_1")
        team = "team_ai"
        
        await ai_integration._register_ai_unit(session_id, entity_id, team)
        
        assert session_id in ai_integration.ai_units
        assert entity_id in ai_integration.ai_units[session_id]
        assert entity_id in ai_integration.unit_control_levels
        assert ai_integration.unit_control_levels[entity_id] == AIControlLevel.STRATEGIC
    
    @pytest.mark.asyncio
    async def test_ai_unit_unregistration(self, ai_integration):
        """Test AI unit cleanup"""
        session_id = "test_session"
        entity_id = EntityID("test_unit_1")
        team = "team_ai"
        
        # Register then unregister
        await ai_integration._register_ai_unit(session_id, entity_id, team)
        await ai_integration._unregister_ai_unit(session_id, entity_id)
        
        assert entity_id not in ai_integration.ai_units.get(session_id, set())
        assert entity_id not in ai_integration.unit_control_levels
    
    def test_set_unit_control_level(self, ai_integration):
        """Test setting AI control levels"""
        entity_id = EntityID("test_unit")
        
        ai_integration.set_unit_control_level(entity_id, AIControlLevel.ADAPTIVE)
        
        assert ai_integration.unit_control_levels[entity_id] == AIControlLevel.ADAPTIVE
    
    def test_get_ai_stats(self, ai_integration):
        """Test AI statistics reporting"""
        stats = ai_integration.get_ai_stats()
        
        assert "connection_status" in stats
        assert "active_ai_units" in stats
        assert "pending_decisions" in stats
        assert "average_decision_time" in stats
        assert "total_decisions" in stats
        assert stats["active_ai_units"] == 0
        assert stats["pending_decisions"] == 0


class TestAIDecisionExecution:
    """Test AI decision execution"""
    
    @pytest.fixture
    def setup_ai_integration(self):
        """Setup AI integration with mocked dependencies"""
        ecs = ECSManager()
        event_bus = EventBus()
        battlefield = MagicMock()
        game_state = MagicMock()
        
        ai_integration = AIIntegrationManager(ecs, event_bus, battlefield, game_state)
        
        return ai_integration, ecs, event_bus
    
    @pytest.mark.asyncio
    async def test_move_action_execution(self, setup_ai_integration):
        """Test AI move action execution"""
        ai_integration, ecs, event_bus = setup_ai_integration
        
        session_id = "test_session"
        entity_id = EntityID("test_unit")
        
        # Create mock position component
        from src.engine.components.position_component import PositionComponent
        position_component = PositionComponent(x=0, y=0, z=0)
        ecs.add_component(entity_id, position_component)
        
        decision = {
            "action_type": "move",
            "target_position": {"x": 3, "y": 4}
        }
        
        # Mock event emission
        event_bus.emit = AsyncMock()
        
        await ai_integration._execute_move_action(session_id, entity_id, decision)
        
        # Check position was updated
        updated_position = ecs.get_component(entity_id, PositionComponent)
        assert updated_position.x == 3
        assert updated_position.y == 4
        assert updated_position.has_moved is True
        
        # Check event was emitted
        event_bus.emit.assert_called_once()
        call_args = event_bus.emit.call_args[0][0]
        assert call_args.type == EventType.UNIT_MOVED
        assert call_args.session_id == session_id
    
    @pytest.mark.asyncio 
    async def test_attack_action_execution(self, setup_ai_integration):
        """Test AI attack action execution"""
        ai_integration, ecs, event_bus = setup_ai_integration
        
        session_id = "test_session"
        entity_id = EntityID("attacker_unit")
        target_id = "target_unit"
        
        decision = {
            "action_type": "attack",
            "target_id": target_id
        }
        
        # Mock event emission
        event_bus.emit = AsyncMock()
        
        await ai_integration._execute_attack_action(session_id, entity_id, decision)
        
        # Check attack event was emitted
        event_bus.emit.assert_called_once()
        call_args = event_bus.emit.call_args[0][0]
        assert call_args.type == EventType.UNIT_ATTACKED
        assert call_args.session_id == session_id
        assert call_args.data["attacker_id"] == str(entity_id)
        assert call_args.data["target_id"] == target_id
        assert call_args.data["ai_controlled"] is True


class TestAIGameStateBuilding:
    """Test AI game state building for decision making"""
    
    @pytest.fixture
    def setup_full_integration(self):
        """Setup full AI integration with battlefield and game state"""
        ecs = ECSManager()
        event_bus = EventBus()
        battlefield = BattlefieldManager((5, 5))
        game_state = GameStateManager()
        
        ai_integration = AIIntegrationManager(ecs, event_bus, battlefield, game_state)
        
        return ai_integration, ecs, battlefield, game_state
    
    @pytest.mark.asyncio
    async def test_build_game_state(self, setup_full_integration):
        """Test building comprehensive game state for AI"""
        ai_integration, ecs, battlefield, game_state = setup_full_integration
        
        session_id = "test_session"
        
        # Initialize battlefield and game state
        await battlefield.initialize_for_session(session_id, (5, 5))
        await game_state.initialize_session(session_id, {})
        
        # Build game state
        state = await ai_integration._build_game_state(session_id)
        
        assert "session_id" in state
        assert "battlefield" in state
        assert "game_state" in state
        assert "timestamp" in state
        assert state["session_id"] == session_id
        
        # Check battlefield structure
        battlefield_data = state["battlefield"]
        assert "grid_size" in battlefield_data
        assert "terrain" in battlefield_data
        assert "units" in battlefield_data
        assert battlefield_data["grid_size"]["width"] == 5
        assert battlefield_data["grid_size"]["height"] == 5
    
    @pytest.mark.asyncio
    async def test_get_unit_data(self, setup_full_integration):
        """Test unit data extraction for AI"""
        ai_integration, ecs, battlefield, game_state = setup_full_integration
        
        # Create test unit with components
        entity_id = EntityID("test_unit")
        ecs.create_entity(entity_id)
        
        from src.engine.components.position_component import PositionComponent
        from src.engine.components.stats_component import StatsComponent
        from src.engine.components.team_component import TeamComponent
        
        position = PositionComponent(x=2, y=3, z=0)
        stats = StatsComponent()
        team = TeamComponent(team="player1", is_ai=True)
        
        ecs.add_component(entity_id, position)
        ecs.add_component(entity_id, stats)
        ecs.add_component(entity_id, team)
        
        # Get unit data
        unit_data = await ai_integration._get_unit_data(entity_id)
        
        assert unit_data is not None
        assert unit_data["unit_id"] == str(entity_id)
        assert unit_data["position"]["x"] == 2
        assert unit_data["position"]["y"] == 3
        assert unit_data["team"] == "player1"
        assert unit_data["is_ai"] is True
        assert "stats" in unit_data
        assert "movement" in unit_data


@pytest.mark.asyncio
async def test_full_ai_decision_workflow():
    """Integration test for full AI decision workflow"""
    # This test simulates a complete AI decision cycle
    ecs = ECSManager()
    event_bus = EventBus()
    battlefield = BattlefieldManager((10, 10))
    game_state = GameStateManager()
    
    # Mock AI client to avoid actual WebSocket connection
    with patch('src.engine.integrations.ai_integration.AIWebSocketClient') as mock_client:
        mock_ai_client = AsyncMock()
        mock_client.return_value = mock_ai_client
        
        ai_integration = AIIntegrationManager(ecs, event_bus, battlefield, game_state)
        ai_integration.ai_client = mock_ai_client
        
        # Setup session
        session_id = "test_session"
        await battlefield.initialize_for_session(session_id, (10, 10))
        await game_state.initialize_session(session_id, {})
        
        # Create AI unit
        entity_id = EntityID("ai_unit_1")
        ecs.create_entity(entity_id)
        
        from src.engine.components.position_component import PositionComponent
        from src.engine.components.stats_component import StatsComponent
        from src.engine.components.team_component import TeamComponent
        
        position = PositionComponent(x=5, y=5, z=0)
        stats = StatsComponent()
        team = TeamComponent(team="ai_team", is_ai=True)
        
        ecs.add_component(entity_id, position)
        ecs.add_component(entity_id, stats) 
        ecs.add_component(entity_id, team)
        
        # Register as AI unit
        await ai_integration._register_ai_unit(session_id, entity_id, "ai_team")
        
        # Simulate turn start event
        turn_event = GameEvent(
            type=EventType.TURN_START,
            session_id=session_id,
            data={"current_player": "ai_team"}
        )
        
        await ai_integration._on_turn_start(turn_event)
        
        # Verify AI client was called to request decision
        mock_ai_client.request_ai_decision.assert_called()
        mock_ai_client.send_game_state_update.assert_called()
        
        # Simulate AI decision response
        decision_event = GameEvent(
            type=EventType.AI_DECISION_MADE,
            session_id=session_id,
            data={
                "request_id": "test_request",
                "decision": {
                    "action_type": "move",
                    "target_position": {"x": 6, "y": 6}
                },
                "confidence": 0.9
            }
        )
        
        # Add pending decision for the request
        ai_integration.pending_decisions["test_request"] = {
            "session_id": session_id,
            "entity_id": entity_id,
            "request_time": "test_time"
        }
        
        await ai_integration._on_ai_decision_made(decision_event)
        
        # Verify unit position was updated
        updated_position = ecs.get_component(entity_id, PositionComponent)
        assert updated_position.x == 6
        assert updated_position.y == 6
        assert updated_position.has_moved is True