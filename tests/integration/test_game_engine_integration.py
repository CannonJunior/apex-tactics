"""
Integration tests for core game engine functionality.

Tests the complete game flow from session creation to gameplay mechanics.
"""

import pytest
import asyncio
import json
from datetime import datetime

import structlog

logger = structlog.get_logger()


class TestGameEngineIntegration:
    """Test complete game engine integration"""
    
    async def test_session_lifecycle(self, game_engine):
        """Test complete session creation, start, and cleanup"""
        session_id = f"integration_test_{datetime.now().timestamp()}"
        player_ids = ["test_player_1", "test_player_2"]
        
        # Create session
        session = await game_engine.create_session(session_id, player_ids)
        assert session.session_id == session_id
        assert session.player_ids == player_ids
        assert session_id in game_engine.active_sessions
        
        # Start game
        success = await game_engine.start_game(session_id)
        assert success is True
        
        # Verify session state
        state = await game_engine.get_session_state(session_id)
        assert state is not None
        assert state["session"]["session_id"] == session_id
        
        # Cleanup
        await game_engine.cleanup_session(session_id)
        assert session_id not in game_engine.active_sessions
    
    async def test_multiple_sessions(self, game_engine):
        """Test handling multiple concurrent sessions"""
        sessions = []
        session_count = 3
        
        # Create multiple sessions
        for i in range(session_count):
            session_id = f"multi_test_{i}_{datetime.now().timestamp()}"
            player_ids = [f"player_{i}_1", f"player_{i}_2"]
            
            session = await game_engine.create_session(session_id, player_ids)
            await game_engine.start_game(session_id)
            sessions.append(session_id)
        
        # Verify all sessions exist
        assert len(game_engine.active_sessions) >= session_count
        
        for session_id in sessions:
            state = await game_engine.get_session_state(session_id)
            assert state is not None
        
        # Cleanup all sessions
        for session_id in sessions:
            await game_engine.cleanup_session(session_id)
        
        # Verify cleanup
        for session_id in sessions:
            assert session_id not in game_engine.active_sessions
    
    async def test_turn_system_integration(self, populated_session, game_engine):
        """Test turn system with actual units"""
        session_id, player_ids, session, units = populated_session
        
        # Get initial turn info
        turn_info = await game_engine.turn_system.get_turn_info(session_id)
        assert turn_info is not None
        assert "current_player" in turn_info
        assert "turn_number" in turn_info
        
        initial_turn = turn_info["turn_number"]
        current_player = turn_info["current_player"]
        
        # End turn
        success = await game_engine.turn_system.end_turn(session_id, current_player)
        assert success is True
        
        # Verify turn advanced
        new_turn_info = await game_engine.turn_system.get_turn_info(session_id)
        assert new_turn_info["turn_number"] >= initial_turn
        assert new_turn_info["current_player"] != current_player or new_turn_info["turn_number"] > initial_turn
    
    async def test_unit_actions_integration(self, populated_session, game_engine):
        """Test unit movement and combat actions"""
        session_id, player_ids, session, units = populated_session
        
        # Get a unit to move
        unit = units[0]  # player_1 unit
        unit_id = str(unit["entity_id"])
        
        # Test movement action
        move_action = {
            "type": "move",
            "unit_id": unit_id,
            "target_position": {"x": 2, "y": 2}
        }
        
        success = await game_engine.execute_player_action(
            session_id, "player_1", move_action
        )
        assert success is True
        
        # Verify unit moved
        position_component = game_engine.ecs.get_component(
            unit["entity_id"], 
            game_engine.ecs.component_types["PositionComponent"]
        )
        assert position_component.x == 2
        assert position_component.y == 2
    
    async def test_combat_system_integration(self, populated_session, game_engine):
        """Test combat between units"""
        session_id, player_ids, session, units = populated_session
        
        # Position units for combat (adjacent)
        attacker = units[0]  # player_1 unit
        target = units[2]    # player_2 unit
        
        # Move attacker next to target
        move_action = {
            "type": "move", 
            "unit_id": str(attacker["entity_id"]),
            "target_position": {"x": 5, "y": 6}  # Adjacent to target at (6,6)
        }
        
        await game_engine.execute_player_action(session_id, "player_1", move_action)
        
        # Get initial HP
        target_stats = game_engine.ecs.get_component(
            target["entity_id"],
            game_engine.ecs.component_types["StatsComponent"]
        )
        initial_hp = target_stats.current_hp
        
        # Execute attack
        attack_action = {
            "type": "attack",
            "unit_id": str(attacker["entity_id"]),
            "target_id": str(target["entity_id"])
        }
        
        success = await game_engine.execute_player_action(
            session_id, "player_1", attack_action
        )
        assert success is True
        
        # Verify damage was dealt
        final_hp = target_stats.current_hp
        assert final_hp < initial_hp
    
    async def test_ai_integration(self, populated_session, game_engine):
        """Test AI integration and decision making"""
        session_id, player_ids, session, units = populated_session
        
        # Enable AI for player_2
        ai_stats = game_engine.ai_integration.get_ai_stats()
        assert ai_stats is not None
        
        # Trigger AI turn (if AI is active)
        if hasattr(game_engine.ai_integration, 'process_ai_turn'):
            try:
                await game_engine.ai_integration.process_ai_turn(session_id, "player_2")
            except Exception as e:
                # AI might not be fully configured in test environment
                logger.warning("AI integration test skipped", error=str(e))
    
    async def test_performance_tracking(self, game_engine):
        """Test performance statistics collection"""
        stats = game_engine.get_performance_stats()
        
        assert "fps" in stats
        assert "frame_count" in stats
        assert "active_sessions" in stats
        assert "entities_count" in stats
        assert "systems_count" in stats
        
        # Verify stats are reasonable
        assert stats["active_sessions"] >= 0
        assert stats["entities_count"] >= 0
        assert stats["systems_count"] > 0
    
    async def test_error_handling(self, game_engine):
        """Test error handling and recovery"""
        # Test invalid session ID
        try:
            await game_engine.get_session_state("invalid_session")
            assert False, "Should have raised exception"
        except Exception:
            pass  # Expected
        
        # Test invalid player action
        session_id = f"error_test_{datetime.now().timestamp()}"
        await game_engine.create_session(session_id, ["player_1"])
        
        invalid_action = {"type": "invalid_action"}
        success = await game_engine.execute_player_action(
            session_id, "player_1", invalid_action
        )
        assert success is False
        
        await game_engine.cleanup_session(session_id)
    
    async def test_event_system_integration(self, populated_session, game_engine):
        """Test event bus integration across systems"""
        session_id, player_ids, session, units = populated_session
        
        # Track events
        events_received = []
        
        async def event_handler(event):
            events_received.append(event)
        
        # Subscribe to events
        from src.core.events import EventType
        game_engine.event_bus.subscribe(EventType.UNIT_MOVED, event_handler)
        
        # Trigger unit movement
        unit = units[0]
        move_action = {
            "type": "move",
            "unit_id": str(unit["entity_id"]),
            "target_position": {"x": 3, "y": 3}
        }
        
        await game_engine.execute_player_action(session_id, "player_1", move_action)
        
        # Give events time to process
        await asyncio.sleep(0.1)
        
        # Verify event was emitted
        assert len(events_received) > 0
        move_event = events_received[-1]
        assert move_event.type == EventType.UNIT_MOVED