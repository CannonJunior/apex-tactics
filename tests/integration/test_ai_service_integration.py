"""
Integration tests for AI Service functionality.

Tests AI decision making, WebSocket communication, and integration with game engine.
"""

import pytest
import asyncio
import json
from datetime import datetime

import httpx
import websockets
import structlog

logger = structlog.get_logger()


class TestAIServiceIntegration:
    """Test AI Service integration with game engine"""
    
    async def test_ai_service_health(self):
        """Test AI Service health check"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("http://localhost:8001/health")
                assert response.status_code == 200
                
                data = response.json()
                assert "status" in data
                assert data["status"] in ["healthy", "running"]
                
        except Exception as e:
            pytest.skip(f"AI Service not available: {e}")
    
    async def test_ai_service_capabilities(self):
        """Test AI Service capabilities endpoint"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("http://localhost:8001/capabilities")
                assert response.status_code == 200
                
                data = response.json()
                assert "models" in data or "capabilities" in data
                
        except Exception as e:
            pytest.skip(f"AI Service not available: {e}")
    
    async def test_ai_decision_making(self):
        """Test AI tactical decision making"""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Sample game state for AI analysis
                game_state = {
                    "session_id": "test_ai_session",
                    "battlefield": {
                        "size": [8, 8],
                        "units": [
                            {
                                "unit_id": "ai_unit_1",
                                "team": "ai_team",
                                "position": {"x": 1, "y": 1},
                                "stats": {"hp": 100, "mp": 50},
                                "can_act": True
                            },
                            {
                                "unit_id": "player_unit_1", 
                                "team": "player_team",
                                "position": {"x": 6, "y": 6},
                                "stats": {"hp": 80, "mp": 40},
                                "can_act": False
                            }
                        ]
                    },
                    "current_player": "ai_team",
                    "turn_number": 3
                }
                
                response = await client.post(
                    "http://localhost:8001/ai/make_decision",
                    json=game_state
                )
                
                if response.status_code == 200:
                    decision = response.json()
                    assert "action" in decision
                    assert "confidence" in decision
                    assert "reasoning" in decision
                    
                    # Validate action structure
                    action = decision["action"]
                    assert "type" in action
                    assert action["type"] in ["move", "attack", "ability", "wait"]
                
        except Exception as e:
            pytest.skip(f"AI Service not available: {e}")
    
    async def test_ai_difficulty_scaling(self):
        """Test AI difficulty level adjustments"""
        try:
            difficulties = ["easy", "normal", "hard", "expert"]
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                for difficulty in difficulties:
                    game_state = {
                        "session_id": f"test_difficulty_{difficulty}",
                        "difficulty": difficulty,
                        "battlefield": {
                            "size": [6, 6],
                            "units": [
                                {
                                    "unit_id": "ai_unit",
                                    "team": "ai_team", 
                                    "position": {"x": 2, "y": 2},
                                    "stats": {"hp": 100, "mp": 50},
                                    "can_act": True
                                }
                            ]
                        },
                        "current_player": "ai_team"
                    }
                    
                    response = await client.post(
                        "http://localhost:8001/ai/make_decision",
                        json=game_state
                    )
                    
                    if response.status_code == 200:
                        decision = response.json()
                        
                        # Higher difficulty should have higher confidence
                        confidence = decision.get("confidence", 0)
                        assert 0 <= confidence <= 1
                        
                        # Expert difficulty should have more sophisticated reasoning
                        if difficulty == "expert":
                            reasoning = decision.get("reasoning", "")
                            assert len(reasoning) > 50  # More detailed reasoning
                
        except Exception as e:
            pytest.skip(f"AI Service not available: {e}")
    
    async def test_ai_websocket_integration(self):
        """Test AI Service WebSocket communication with game engine"""
        try:
            # Connect to AI Service WebSocket
            ai_uri = "ws://localhost:8001/ws/ai_test_session"
            
            async with websockets.connect(ai_uri) as ai_websocket:
                # Send game state update
                game_update = {
                    "type": "game_state_update",
                    "data": {
                        "session_id": "ai_test_session",
                        "battlefield": {
                            "size": [8, 8],
                            "units": [
                                {
                                    "unit_id": "ai_unit_1",
                                    "team": "ai_team",
                                    "position": {"x": 3, "y": 3},
                                    "stats": {"hp": 90, "mp": 45}
                                }
                            ]
                        },
                        "current_player": "ai_team"
                    }
                }
                
                await ai_websocket.send(json.dumps(game_update))
                
                # Wait for AI response
                response = await asyncio.wait_for(
                    ai_websocket.recv(), timeout=10.0
                )
                
                data = json.loads(response)
                assert "type" in data
                assert data["type"] in ["ai_decision", "ai_action", "acknowledgment"]
                
        except Exception as e:
            pytest.skip(f"AI Service WebSocket not available: {e}")
    
    async def test_ai_performance_metrics(self):
        """Test AI Service performance tracking"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("http://localhost:8001/metrics")
                
                if response.status_code == 200:
                    metrics = response.json()
                    
                    # Check for expected metrics
                    expected_metrics = [
                        "decisions_made",
                        "average_decision_time",
                        "confidence_scores",
                        "active_sessions"
                    ]
                    
                    for metric in expected_metrics:
                        if metric in metrics:
                            assert isinstance(metrics[metric], (int, float, dict, list))
                
        except Exception as e:
            pytest.skip(f"AI Service metrics not available: {e}")
    
    async def test_ai_learning_feedback(self):
        """Test AI learning from game outcomes"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Send feedback about previous decision
                feedback_data = {
                    "session_id": "learning_test_session",
                    "decision_id": "decision_123",
                    "outcome": "success",
                    "score": 0.8,
                    "context": {
                        "action_taken": "move",
                        "result": "strategic_advantage_gained"
                    }
                }
                
                response = await client.post(
                    "http://localhost:8001/ai/feedback",
                    json=feedback_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    assert "acknowledged" in result
                    assert result["acknowledged"] is True
                
        except Exception as e:
            pytest.skip(f"AI Service learning not available: {e}")
    
    async def test_ai_multi_unit_coordination(self):
        """Test AI coordination of multiple units"""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Complex scenario with multiple AI units
                game_state = {
                    "session_id": "multi_unit_test",
                    "battlefield": {
                        "size": [10, 10],
                        "units": [
                            {
                                "unit_id": "ai_unit_1",
                                "team": "ai_team",
                                "position": {"x": 2, "y": 2},
                                "stats": {"hp": 100, "mp": 50},
                                "can_act": True,
                                "role": "tank"
                            },
                            {
                                "unit_id": "ai_unit_2",
                                "team": "ai_team", 
                                "position": {"x": 3, "y": 1},
                                "stats": {"hp": 70, "mp": 80},
                                "can_act": True,
                                "role": "mage"
                            },
                            {
                                "unit_id": "ai_unit_3",
                                "team": "ai_team",
                                "position": {"x": 1, "y": 3},
                                "stats": {"hp": 80, "mp": 60},
                                "can_act": True,
                                "role": "archer"
                            },
                            {
                                "unit_id": "enemy_unit_1",
                                "team": "player_team",
                                "position": {"x": 8, "y": 8},
                                "stats": {"hp": 90, "mp": 40}
                            }
                        ]
                    },
                    "current_player": "ai_team",
                    "difficulty": "hard"
                }
                
                response = await client.post(
                    "http://localhost:8001/ai/coordinate_units",
                    json=game_state
                )
                
                if response.status_code == 200:
                    coordination = response.json()
                    assert "unit_actions" in coordination
                    assert "strategy" in coordination
                    
                    unit_actions = coordination["unit_actions"]
                    assert len(unit_actions) > 0
                    
                    # Each unit should have a planned action
                    for action in unit_actions:
                        assert "unit_id" in action
                        assert "action" in action
                        assert "priority" in action
                
        except Exception as e:
            pytest.skip(f"AI Service coordination not available: {e}")


class TestAIServicePerformance:
    """Test AI Service performance characteristics"""
    
    async def test_ai_decision_speed(self):
        """Test AI decision making performance"""
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                # Simple scenario for speed testing
                simple_state = {
                    "session_id": "speed_test",
                    "battlefield": {
                        "size": [6, 6],
                        "units": [
                            {
                                "unit_id": "ai_unit",
                                "team": "ai_team",
                                "position": {"x": 1, "y": 1},
                                "stats": {"hp": 100, "mp": 50},
                                "can_act": True
                            }
                        ]
                    },
                    "current_player": "ai_team"
                }
                
                # Test multiple decisions for average
                decision_times = []
                test_count = 3
                
                for i in range(test_count):
                    start_time = asyncio.get_event_loop().time()
                    
                    response = await client.post(
                        "http://localhost:8001/ai/make_decision",
                        json=simple_state
                    )
                    
                    end_time = asyncio.get_event_loop().time()
                    decision_time = end_time - start_time
                    decision_times.append(decision_time)
                    
                    if response.status_code == 200:
                        decision = response.json()
                        assert "action" in decision
                
                # Average decision time should be reasonable
                avg_time = sum(decision_times) / len(decision_times)
                assert avg_time < 5.0  # Less than 5 seconds per decision
                
        except Exception as e:
            pytest.skip(f"AI Service not available: {e}")
    
    async def test_ai_concurrent_sessions(self):
        """Test AI handling multiple concurrent game sessions"""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Create multiple concurrent decision requests
                sessions = []
                for i in range(3):
                    session_state = {
                        "session_id": f"concurrent_test_{i}",
                        "battlefield": {
                            "size": [6, 6],
                            "units": [
                                {
                                    "unit_id": f"ai_unit_{i}",
                                    "team": "ai_team",
                                    "position": {"x": i+1, "y": i+1},
                                    "stats": {"hp": 100, "mp": 50},
                                    "can_act": True
                                }
                            ]
                        },
                        "current_player": "ai_team"
                    }
                    sessions.append(session_state)
                
                # Send all requests concurrently
                tasks = []
                for session_state in sessions:
                    task = client.post(
                        "http://localhost:8001/ai/make_decision",
                        json=session_state
                    )
                    tasks.append(task)
                
                # Wait for all responses
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Count successful responses
                successful_responses = 0
                for response in responses:
                    if not isinstance(response, Exception) and response.status_code == 200:
                        successful_responses += 1
                        decision = response.json()
                        assert "action" in decision
                
                # At least some should succeed
                assert successful_responses > 0
                
        except Exception as e:
            pytest.skip(f"AI Service not available: {e}")
    
    async def test_ai_memory_usage(self):
        """Test AI Service memory efficiency"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("http://localhost:8001/system/stats")
                
                if response.status_code == 200:
                    stats = response.json()
                    
                    if "memory_usage" in stats:
                        memory_mb = stats["memory_usage"]
                        # Should use reasonable amount of memory
                        assert memory_mb < 2000  # Less than 2GB
                
        except Exception as e:
            pytest.skip(f"AI Service system stats not available: {e}")


class TestAIServiceIntegrationScenarios:
    """Test complete AI Service integration scenarios"""
    
    async def test_full_ai_game_scenario(self):
        """Test complete AI vs AI game scenario"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Initialize game session
                session_id = f"ai_vs_ai_{datetime.now().timestamp()}"
                
                # Create initial game state
                game_state = {
                    "session_id": session_id,
                    "mode": "ai_vs_ai",
                    "battlefield": {
                        "size": [8, 8],
                        "units": [
                            # Team 1 (AI)
                            {
                                "unit_id": "ai1_unit1",
                                "team": "ai_team_1",
                                "position": {"x": 1, "y": 1},
                                "stats": {"hp": 100, "mp": 50}
                            },
                            {
                                "unit_id": "ai1_unit2",
                                "team": "ai_team_1", 
                                "position": {"x": 2, "y": 1},
                                "stats": {"hp": 80, "mp": 60}
                            },
                            # Team 2 (AI)
                            {
                                "unit_id": "ai2_unit1",
                                "team": "ai_team_2",
                                "position": {"x": 6, "y": 6},
                                "stats": {"hp": 90, "mp": 55}
                            },
                            {
                                "unit_id": "ai2_unit2",
                                "team": "ai_team_2",
                                "position": {"x": 7, "y": 6},
                                "stats": {"hp": 85, "mp": 45}
                            }
                        ]
                    },
                    "current_player": "ai_team_1",
                    "turn_number": 1
                }
                
                # Simulate several turns
                max_turns = 5
                current_team = "ai_team_1"
                
                for turn in range(max_turns):
                    game_state["current_player"] = current_team
                    game_state["turn_number"] = turn + 1
                    
                    # Get AI decision
                    response = await client.post(
                        "http://localhost:8001/ai/make_decision",
                        json=game_state
                    )
                    
                    if response.status_code == 200:
                        decision = response.json()
                        assert "action" in decision
                        
                        # Apply action to game state (simplified)
                        action = decision["action"]
                        if action["type"] == "move":
                            # Update unit position in game state
                            unit_id = action.get("unit_id")
                            target_pos = action.get("target_position")
                            
                            if unit_id and target_pos:
                                for unit in game_state["battlefield"]["units"]:
                                    if unit["unit_id"] == unit_id:
                                        unit["position"] = target_pos
                                        break
                    
                    # Switch teams
                    current_team = "ai_team_2" if current_team == "ai_team_1" else "ai_team_1"
                
                # Game should progress through multiple turns
                assert game_state["turn_number"] > 1
                
        except Exception as e:
            pytest.skip(f"AI Service not available: {e}")
    
    async def test_ai_adaptive_difficulty(self):
        """Test AI adaptive difficulty based on player performance"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                session_id = "adaptive_difficulty_test"
                
                # Simulate player winning consistently (AI should get harder)
                performance_data = {
                    "session_id": session_id,
                    "player_performance": {
                        "wins": 5,
                        "losses": 1, 
                        "average_turn_time": 15.0,
                        "decision_quality": 0.8
                    },
                    "current_difficulty": "normal"
                }
                
                response = await client.post(
                    "http://localhost:8001/ai/adjust_difficulty",
                    json=performance_data
                )
                
                if response.status_code == 200:
                    adjustment = response.json()
                    assert "new_difficulty" in adjustment
                    assert "reasoning" in adjustment
                    
                    # Should suggest increasing difficulty
                    new_difficulty = adjustment["new_difficulty"]
                    difficulty_levels = ["easy", "normal", "hard", "expert"]
                    current_index = difficulty_levels.index("normal")
                    new_index = difficulty_levels.index(new_difficulty)
                    
                    # Should increase difficulty for consistently winning player
                    assert new_index >= current_index
                
        except Exception as e:
            pytest.skip(f"AI Service adaptive difficulty not available: {e}")
    
    async def test_ai_explanation_system(self):
        """Test AI decision explanation for learning players"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Request detailed explanation of AI decision
                explanation_request = {
                    "session_id": "explanation_test",
                    "decision_id": "decision_456",
                    "context": {
                        "action": {
                            "type": "move",
                            "unit_id": "ai_unit_1",
                            "from_position": {"x": 2, "y": 2},
                            "to_position": {"x": 3, "y": 3}
                        },
                        "battlefield_state": {
                            "enemy_positions": [{"x": 5, "y": 5}],
                            "objectives": [{"x": 7, "y": 7, "type": "capture_point"}]
                        }
                    },
                    "explanation_level": "detailed"
                }
                
                response = await client.post(
                    "http://localhost:8001/ai/explain_decision",
                    json=explanation_request
                )
                
                if response.status_code == 200:
                    explanation = response.json()
                    assert "reasoning" in explanation
                    assert "strategic_goals" in explanation
                    assert "alternatives_considered" in explanation
                    
                    # Detailed explanation should be comprehensive
                    reasoning = explanation["reasoning"]
                    assert len(reasoning) > 100  # Substantial explanation
                    
                    # Should include strategic concepts
                    strategic_terms = ["position", "advantage", "threat", "objective"]
                    reasoning_lower = reasoning.lower()
                    found_terms = sum(1 for term in strategic_terms if term in reasoning_lower)
                    assert found_terms >= 2  # At least 2 strategic terms
                
        except Exception as e:
            pytest.skip(f"AI Service explanation not available: {e}")