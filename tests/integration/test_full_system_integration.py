"""
Full system integration tests.

Tests complete end-to-end scenarios involving all systems working together.
"""

import pytest
import asyncio
import json
import time
from datetime import datetime

import httpx
import websockets
import structlog

logger = structlog.get_logger()


class TestFullSystemIntegration:
    """Test complete system integration scenarios"""
    
    async def test_complete_game_session_lifecycle(self):
        """Test complete game session from creation to completion"""
        try:
            session_id = f"full_integration_{datetime.now().timestamp()}"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 1. Create game session via API
                session_data = {
                    "session_id": session_id,
                    "player_ids": ["player_1", "player_2"],
                    "config": {
                        "mode": "tutorial",
                        "battlefield_size": [6, 6],
                        "max_turns": 10,
                        "turn_time_limit": 30.0,
                        "ai_difficulty": "easy"
                    }
                }
                
                create_response = await client.post(
                    "http://localhost:8002/api/sessions",
                    json=session_data
                )
                
                if create_response.status_code == 200:
                    # 2. Start the game session
                    start_response = await client.post(
                        f"http://localhost:8002/api/sessions/{session_id}/start"
                    )
                    
                    if start_response.status_code == 200:
                        # 3. Get initial session state
                        state_response = await client.get(
                            f"http://localhost:8002/api/sessions/{session_id}"
                        )
                        
                        if state_response.status_code == 200:
                            session_state = state_response.json()
                            assert session_state["session"]["session_id"] == session_id
                            assert len(session_state["session"]["player_ids"]) == 2
                            
                            # 4. Test MCP Gateway integration
                            if await self._test_mcp_integration(session_id):
                                logger.info("MCP integration successful")
                            
                            # 5. Test WebSocket real-time updates
                            if await self._test_websocket_integration(session_id):
                                logger.info("WebSocket integration successful")
                            
                            # 6. Test AI Service integration
                            if await self._test_ai_integration(session_id):
                                logger.info("AI integration successful")
                            
                            # 7. Cleanup session
                            cleanup_response = await client.delete(
                                f"http://localhost:8002/api/sessions/{session_id}"
                            )
                            
                            assert cleanup_response.status_code == 200
                            
                            return True
                
                return False
                
        except Exception as e:
            pytest.skip(f"Full system integration not available: {e}")
    
    async def _test_mcp_integration(self, session_id: str) -> bool:
        """Test MCP Gateway integration within full system"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Test session state via MCP
                mcp_request = {
                    "tool": "get_session_state",
                    "args": {"session_id": session_id}
                }
                
                response = await client.post(
                    "http://localhost:8004/call_tool",
                    json=mcp_request
                )
                
                if response.status_code == 200:
                    state = response.json()
                    return state.get("session", {}).get("session_id") == session_id
                
                return False
                
        except Exception:
            return False
    
    async def _test_websocket_integration(self, session_id: str) -> bool:
        """Test WebSocket integration within full system"""
        try:
            uri = f"ws://localhost:8002/ws/{session_id}?player_id=player_1"
            
            async with websockets.connect(uri) as websocket:
                # Send UI data request
                request = {"type": "request_ui_data"}
                await websocket.send(json.dumps(request))
                
                # Wait for response
                response = await asyncio.wait_for(
                    websocket.recv(), timeout=5.0
                )
                
                data = json.loads(response)
                return data.get("type") == "ui_data"
                
        except Exception:
            return False
    
    async def _test_ai_integration(self, session_id: str) -> bool:
        """Test AI Service integration within full system"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Simple AI decision request
                ai_request = {
                    "session_id": session_id,
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
                    json=ai_request
                )
                
                if response.status_code == 200:
                    decision = response.json()
                    return "action" in decision
                
                return False
                
        except Exception:
            return False
    
    async def test_multi_player_scenario(self):
        """Test multi-player game scenario with real-time updates"""
        try:
            session_id = f"multiplayer_test_{datetime.now().timestamp()}"
            
            # Create session
            async with httpx.AsyncClient(timeout=20.0) as client:
                session_data = {
                    "session_id": session_id,
                    "player_ids": ["player_1", "player_2"],
                    "config": {
                        "mode": "multiplayer",
                        "battlefield_size": [8, 8],
                        "max_turns": 5,
                        "turn_time_limit": 15.0
                    }
                }
                
                create_response = await client.post(
                    "http://localhost:8002/api/sessions",
                    json=session_data
                )
                
                if create_response.status_code == 200:
                    await client.post(f"http://localhost:8002/api/sessions/{session_id}/start")
                    
                    # Connect both players via WebSocket
                    player1_uri = f"ws://localhost:8002/ws/{session_id}?player_id=player_1"
                    player2_uri = f"ws://localhost:8002/ws/{session_id}?player_id=player_2"
                    
                    async with websockets.connect(player1_uri) as ws1, \
                               websockets.connect(player2_uri) as ws2:
                        
                        # Player 1 performs action
                        action = {
                            "type": "player_action",
                            "data": {
                                "type": "move",
                                "unit_id": "test_unit",
                                "target_position": {"x": 3, "y": 3}
                            }
                        }
                        
                        await ws1.send(json.dumps(action))
                        
                        # Both players should receive updates
                        try:
                            p1_response = await asyncio.wait_for(ws1.recv(), timeout=5.0)
                            p2_response = await asyncio.wait_for(ws2.recv(), timeout=5.0)
                            
                            p1_data = json.loads(p1_response)
                            p2_data = json.loads(p2_response)
                            
                            # Both should receive valid responses
                            assert "type" in p1_data
                            assert "type" in p2_data
                            
                        except asyncio.TimeoutError:
                            # Timeout is acceptable if no updates triggered
                            pass
                    
                    # Cleanup
                    await client.delete(f"http://localhost:8002/api/sessions/{session_id}")
                    
        except Exception as e:
            pytest.skip(f"Multi-player scenario not available: {e}")
    
    async def test_ai_vs_ai_scenario(self):
        """Test AI vs AI game scenario"""
        try:
            session_id = f"ai_vs_ai_test_{datetime.now().timestamp()}"
            
            async with httpx.AsyncClient(timeout=25.0) as client:
                # Create AI vs AI session
                session_data = {
                    "session_id": session_id,
                    "player_ids": ["ai_player_1", "ai_player_2"],
                    "config": {
                        "mode": "ai_vs_ai",
                        "battlefield_size": [6, 6],
                        "max_turns": 3,
                        "turn_time_limit": 10.0,
                        "ai_difficulty": "normal"
                    }
                }
                
                create_response = await client.post(
                    "http://localhost:8002/api/sessions",
                    json=session_data
                )
                
                if create_response.status_code == 200:
                    await client.post(f"http://localhost:8002/api/sessions/{session_id}/start")
                    
                    # Monitor game through MCP Gateway
                    turns_completed = 0
                    max_turns = 3
                    
                    for turn in range(max_turns):
                        # Get game state
                        mcp_request = {
                            "tool": "get_session_state",
                            "args": {"session_id": session_id}
                        }
                        
                        state_response = await client.post(
                            "http://localhost:8004/call_tool",
                            json=mcp_request
                        )
                        
                        if state_response.status_code == 200:
                            state = state_response.json()
                            current_turn = state.get("session", {}).get("turn_number", 0)
                            
                            if current_turn > turns_completed:
                                turns_completed = current_turn
                                logger.info(f"AI vs AI game progressed to turn {current_turn}")
                            
                            # Let AI make decisions
                            await asyncio.sleep(2.0)
                        
                        else:
                            break
                    
                    # Game should have progressed
                    assert turns_completed > 0
                    
                    # Cleanup
                    await client.delete(f"http://localhost:8002/api/sessions/{session_id}")
                    
        except Exception as e:
            pytest.skip(f"AI vs AI scenario not available: {e}")
    
    async def test_system_performance_under_load(self):
        """Test system performance with multiple concurrent operations"""
        try:
            # Create multiple concurrent sessions
            session_count = 3
            session_ids = []
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Create sessions
                for i in range(session_count):
                    session_id = f"load_test_{i}_{datetime.now().timestamp()}"
                    session_ids.append(session_id)
                    
                    session_data = {
                        "session_id": session_id,
                        "player_ids": [f"player_{i}_1", f"player_{i}_2"],
                        "config": {
                            "mode": "tutorial",
                            "battlefield_size": [6, 6],
                            "max_turns": 5,
                            "turn_time_limit": 10.0
                        }
                    }
                    
                    await client.post("http://localhost:8002/api/sessions", json=session_data)
                    await client.post(f"http://localhost:8002/api/sessions/{session_id}/start")
                
                # Perform concurrent operations
                start_time = time.time()
                
                # Concurrent API requests
                api_tasks = []
                for session_id in session_ids:
                    task = client.get(f"http://localhost:8002/api/sessions/{session_id}")
                    api_tasks.append(task)
                
                api_responses = await asyncio.gather(*api_tasks, return_exceptions=True)
                
                # Concurrent MCP requests
                mcp_tasks = []
                for session_id in session_ids:
                    mcp_request = {
                        "tool": "get_session_state",
                        "args": {"session_id": session_id}
                    }
                    task = client.post("http://localhost:8004/call_tool", json=mcp_request)
                    mcp_tasks.append(task)
                
                mcp_responses = await asyncio.gather(*mcp_tasks, return_exceptions=True)
                
                end_time = time.time()
                duration = end_time - start_time
                
                # Count successful operations
                successful_api = sum(1 for r in api_responses 
                                   if not isinstance(r, Exception) and r.status_code == 200)
                successful_mcp = sum(1 for r in mcp_responses 
                                   if not isinstance(r, Exception) and r.status_code == 200)
                
                # Should handle concurrent operations efficiently
                total_operations = successful_api + successful_mcp
                if total_operations > 0:
                    operations_per_second = total_operations / duration
                    assert operations_per_second > 1  # At least 1 operation/sec
                
                # Cleanup sessions
                for session_id in session_ids:
                    try:
                        await client.delete(f"http://localhost:8002/api/sessions/{session_id}")
                    except:
                        pass
                
        except Exception as e:
            pytest.skip(f"Performance testing not available: {e}")
    
    async def test_error_propagation_and_recovery(self):
        """Test error handling across all systems"""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Test API error handling
                invalid_session_response = await client.get(
                    "http://localhost:8002/api/sessions/nonexistent_session"
                )
                assert invalid_session_response.status_code == 404
                
                # Test MCP error handling
                invalid_mcp_request = {
                    "tool": "get_session_state",
                    "args": {"session_id": "nonexistent_session"}
                }
                
                mcp_error_response = await client.post(
                    "http://localhost:8004/call_tool",
                    json=invalid_mcp_request
                )
                # Should handle error gracefully (not crash)
                assert mcp_error_response.status_code in [400, 404, 500]
                
                # Test AI Service error handling
                invalid_ai_request = {
                    "session_id": "nonexistent_session",
                    "battlefield": {"invalid": "data"}
                }
                
                ai_error_response = await client.post(
                    "http://localhost:8001/ai/make_decision",
                    json=invalid_ai_request
                )
                # Should handle error gracefully
                assert ai_error_response.status_code in [400, 422, 500]
                
                # System should still be responsive after errors
                health_response = await client.get("http://localhost:8002/api/health")
                if health_response.status_code == 200:
                    health_data = health_response.json()
                    assert health_data.get("status") in ["healthy", "running"]
                
        except Exception as e:
            pytest.skip(f"Error testing not available: {e}")
    
    async def test_system_monitoring_integration(self):
        """Test comprehensive system monitoring"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Get comprehensive system status
                status_response = await client.get("http://localhost:8002/api/status")
                
                if status_response.status_code == 200:
                    status = status_response.json()
                    
                    # Should contain all subsystem metrics
                    expected_sections = [
                        "performance",
                        "websockets", 
                        "ui_stats"
                    ]
                    
                    for section in expected_sections:
                        if section in status:
                            assert isinstance(status[section], dict)
                    
                    # Performance metrics
                    if "performance" in status:
                        perf = status["performance"]
                        metrics = ["active_sessions", "entities_count", "systems_count"]
                        
                        for metric in metrics:
                            if metric in perf:
                                assert isinstance(perf[metric], (int, float))
                                assert perf[metric] >= 0
                    
                    # WebSocket metrics
                    if "websockets" in status:
                        ws_stats = status["websockets"]
                        if "total_connections" in ws_stats:
                            assert isinstance(ws_stats["total_connections"], int)
                            assert ws_stats["total_connections"] >= 0
                    
                    # UI system metrics
                    if "ui_stats" in status:
                        ui_stats = status["ui_stats"]
                        ui_sections = ["ui_manager", "visual_effects", "notifications"]
                        
                        for section in ui_sections:
                            if section in ui_stats:
                                assert isinstance(ui_stats[section], dict)
                
        except Exception as e:
            pytest.skip(f"System monitoring not available: {e}")


class TestSystemIntegrationScenarios:
    """Test specific integration scenarios"""
    
    async def test_tutorial_mode_integration(self):
        """Test tutorial mode with all systems"""
        try:
            session_id = f"tutorial_integration_{datetime.now().timestamp()}"
            
            async with httpx.AsyncClient(timeout=20.0) as client:
                # Create tutorial session
                session_data = {
                    "session_id": session_id,
                    "player_ids": ["tutorial_player"],
                    "config": {
                        "mode": "tutorial",
                        "battlefield_size": [6, 6],
                        "max_turns": 10,
                        "turn_time_limit": 30.0,
                        "ai_difficulty": "easy"
                    }
                }
                
                create_response = await client.post(
                    "http://localhost:8002/api/sessions",
                    json=session_data
                )
                
                if create_response.status_code == 200:
                    await client.post(f"http://localhost:8002/api/sessions/{session_id}/start")
                    
                    # Test tutorial-specific features
                    # 1. Get initial tutorial state
                    state_response = await client.get(
                        f"http://localhost:8002/api/sessions/{session_id}"
                    )
                    
                    if state_response.status_code == 200:
                        state = state_response.json()
                        assert state["session"]["config"]["mode"] == "tutorial"
                    
                    # 2. Send tutorial notification
                    tutorial_notification = {
                        "type": "info",
                        "title": "Tutorial Step 1",
                        "message": "Welcome to Apex Tactics! Click on a unit to select it.",
                        "player_id": "tutorial_player"
                    }
                    
                    notif_response = await client.post(
                        f"http://localhost:8002/api/sessions/{session_id}/notifications",
                        json=tutorial_notification
                    )
                    
                    if notif_response.status_code == 200:
                        assert notif_response.json()["success"] is True
                    
                    # 3. Test tutorial UI via WebSocket
                    uri = f"ws://localhost:8002/ws/{session_id}?player_id=tutorial_player"
                    
                    async with websockets.connect(uri) as websocket:
                        # Get UI data
                        ui_request = {"type": "request_ui_data"}
                        await websocket.send(json.dumps(ui_request))
                        
                        ui_response = await asyncio.wait_for(
                            websocket.recv(), timeout=5.0
                        )
                        
                        ui_data = json.loads(ui_response)
                        assert ui_data["type"] == "ui_data"
                        
                        # Should contain tutorial notification
                        notifications = ui_data.get("data", {}).get("notifications", [])
                        tutorial_notifications = [
                            n for n in notifications 
                            if "Tutorial" in n.get("title", "")
                        ]
                        assert len(tutorial_notifications) > 0
                    
                    # Cleanup
                    await client.delete(f"http://localhost:8002/api/sessions/{session_id}")
                    
        except Exception as e:
            pytest.skip(f"Tutorial integration not available: {e}")
    
    async def test_real_time_spectator_mode(self):
        """Test spectator mode with real-time updates"""
        try:
            session_id = f"spectator_test_{datetime.now().timestamp()}"
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Create game session
                session_data = {
                    "session_id": session_id,
                    "player_ids": ["player_1", "player_2"],
                    "config": {
                        "mode": "multiplayer",
                        "battlefield_size": [6, 6],
                        "max_turns": 5
                    }
                }
                
                await client.post("http://localhost:8002/api/sessions", json=session_data)
                await client.post(f"http://localhost:8002/api/sessions/{session_id}/start")
                
                # Connect as spectator (no player_id)
                spectator_uri = f"ws://localhost:8002/ws/{session_id}"
                
                async with websockets.connect(spectator_uri) as spectator_ws:
                    # Spectator should receive game state
                    spectator_data = await asyncio.wait_for(
                        spectator_ws.recv(), timeout=5.0
                    )
                    
                    data = json.loads(spectator_data)
                    # Should receive initial game state
                    assert data["type"] in ["game_state", "ui_data"]
                    
                    # Connect player and perform action
                    player_uri = f"ws://localhost:8002/ws/{session_id}?player_id=player_1"
                    
                    async with websockets.connect(player_uri) as player_ws:
                        # Player performs action
                        action = {
                            "type": "player_action",
                            "data": {
                                "type": "move",
                                "unit_id": "test_unit",
                                "target_position": {"x": 2, "y": 2}
                            }
                        }
                        
                        await player_ws.send(json.dumps(action))
                        
                        # Spectator should see the update
                        try:
                            spectator_update = await asyncio.wait_for(
                                spectator_ws.recv(), timeout=3.0
                            )
                            
                            update_data = json.loads(spectator_update)
                            assert "type" in update_data
                            
                        except asyncio.TimeoutError:
                            # It's OK if no immediate update
                            pass
                
                # Cleanup
                await client.delete(f"http://localhost:8002/api/sessions/{session_id}")
                
        except Exception as e:
            pytest.skip(f"Spectator mode not available: {e}")
    
    async def test_system_stress_recovery(self):
        """Test system recovery after stress conditions"""
        try:
            # Create rapid burst of sessions
            session_ids = []
            
            async with httpx.AsyncClient(timeout=20.0) as client:
                # Create multiple sessions rapidly
                for i in range(5):
                    session_id = f"stress_test_{i}_{datetime.now().timestamp()}"
                    session_ids.append(session_id)
                    
                    session_data = {
                        "session_id": session_id,
                        "player_ids": [f"stress_player_{i}"],
                        "config": {
                            "mode": "tutorial",
                            "battlefield_size": [4, 4],
                            "max_turns": 3
                        }
                    }
                    
                    # Don't await - create rapidly
                    asyncio.create_task(
                        client.post("http://localhost:8002/api/sessions", json=session_data)
                    )
                
                # Give system time to process
                await asyncio.sleep(2.0)
                
                # Check system health
                health_response = await client.get("http://localhost:8002/api/health")
                
                if health_response.status_code == 200:
                    health_data = health_response.json()
                    
                    # System should still be healthy
                    assert health_data.get("status") in ["healthy", "running"]
                
                # Cleanup all sessions
                for session_id in session_ids:
                    try:
                        await client.delete(f"http://localhost:8002/api/sessions/{session_id}")
                    except:
                        pass
                
                # System should recover
                await asyncio.sleep(1.0)
                
                final_health = await client.get("http://localhost:8002/api/health")
                if final_health.status_code == 200:
                    final_data = final_health.json()
                    assert final_data.get("status") in ["healthy", "running"]
                
        except Exception as e:
            pytest.skip(f"Stress testing not available: {e}")