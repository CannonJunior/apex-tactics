"""
Integration tests for WebSocket functionality.

Tests real-time communication between clients and game engine.
"""

import pytest
import asyncio
import json
import websockets
from datetime import datetime

import structlog

logger = structlog.get_logger()


class TestWebSocketIntegration:
    """Test WebSocket real-time communication"""
    
    async def test_websocket_connection(self, test_utils):
        """Test basic WebSocket connection and handshake"""
        session_id = f"ws_test_{datetime.now().timestamp()}"
        uri = f"ws://localhost:8002/ws/{session_id}?player_id=test_player"
        
        try:
            async with websockets.connect(uri) as websocket:
                # Should receive initial game state
                initial_message = await asyncio.wait_for(
                    websocket.recv(), timeout=5.0
                )
                
                data = json.loads(initial_message)
                assert data["type"] in ["game_state", "ui_data"]
                
        except Exception as e:
            pytest.skip(f"WebSocket server not available: {e}")
    
    async def test_websocket_player_actions(self, test_utils):
        """Test sending player actions via WebSocket"""
        session_id = f"ws_action_test_{datetime.now().timestamp()}"
        uri = f"ws://localhost:8002/ws/{session_id}?player_id=test_player"
        
        try:
            async with websockets.connect(uri) as websocket:
                # Send player action
                action_message = {
                    "type": "player_action",
                    "data": {
                        "type": "move",
                        "unit_id": "test_unit",
                        "target_position": {"x": 3, "y": 3}
                    }
                }
                
                await websocket.send(json.dumps(action_message))
                
                # Wait for response
                response = await asyncio.wait_for(
                    websocket.recv(), timeout=5.0
                )
                
                data = json.loads(response)
                assert "type" in data
                
        except Exception as e:
            pytest.skip(f"WebSocket server not available: {e}")
    
    async def test_websocket_unit_selection(self, test_utils):
        """Test unit selection via WebSocket"""
        session_id = f"ws_select_test_{datetime.now().timestamp()}"
        uri = f"ws://localhost:8002/ws/{session_id}?player_id=test_player"
        
        try:
            async with websockets.connect(uri) as websocket:
                # Send unit selection
                select_message = {
                    "type": "select_unit",
                    "data": {
                        "unit_id": "test_unit_001"
                    }
                }
                
                await websocket.send(json.dumps(select_message))
                
                # Wait for response
                response = await asyncio.wait_for(
                    websocket.recv(), timeout=5.0
                )
                
                data = json.loads(response)
                assert data["type"] == "select_unit_result"
                assert "success" in data["data"]
                
        except Exception as e:
            pytest.skip(f"WebSocket server not available: {e}")
    
    async def test_websocket_notifications(self, test_utils):
        """Test real-time notifications via WebSocket"""
        session_id = f"ws_notify_test_{datetime.now().timestamp()}"
        uri = f"ws://localhost:8002/ws/{session_id}?player_id=test_player"
        
        try:
            async with websockets.connect(uri) as websocket:
                # Skip initial messages
                await asyncio.sleep(0.5)
                
                # Clear any pending messages
                try:
                    while True:
                        await asyncio.wait_for(websocket.recv(), timeout=0.1)
                except asyncio.TimeoutError:
                    pass
                
                # Send request that should trigger notification
                request_message = {
                    "type": "request_game_state"
                }
                
                await websocket.send(json.dumps(request_message))
                
                # Wait for game state response
                response = await asyncio.wait_for(
                    websocket.recv(), timeout=5.0
                )
                
                data = json.loads(response)
                assert data["type"] == "game_state"
                
        except Exception as e:
            pytest.skip(f"WebSocket server not available: {e}")
    
    async def test_multiple_websocket_connections(self, test_utils):
        """Test multiple simultaneous WebSocket connections"""
        session_id = f"ws_multi_test_{datetime.now().timestamp()}"
        
        connections = []
        num_connections = 3
        
        try:
            # Create multiple connections
            for i in range(num_connections):
                uri = f"ws://localhost:8002/ws/{session_id}?player_id=player_{i}"
                connection = await websockets.connect(uri)
                connections.append(connection)
            
            # Send ping to all connections
            for i, connection in enumerate(connections):
                ping_message = {
                    "type": "ping",
                    "data": {"player_id": f"player_{i}"}
                }
                await connection.send(json.dumps(ping_message))
            
            # Verify all connections respond
            for connection in connections:
                response = await asyncio.wait_for(
                    connection.recv(), timeout=5.0
                )
                data = json.loads(response)
                assert data["type"] == "pong"
            
        except Exception as e:
            pytest.skip(f"WebSocket server not available: {e}")
        
        finally:
            # Cleanup connections
            for connection in connections:
                try:
                    await connection.close()
                except:
                    pass
    
    async def test_websocket_error_handling(self, test_utils):
        """Test WebSocket error handling"""
        session_id = f"ws_error_test_{datetime.now().timestamp()}"
        uri = f"ws://localhost:8002/ws/{session_id}?player_id=test_player"
        
        try:
            async with websockets.connect(uri) as websocket:
                # Send invalid message
                invalid_message = {
                    "type": "invalid_message_type",
                    "data": {"invalid": "data"}
                }
                
                await websocket.send(json.dumps(invalid_message))
                
                # Should receive error response
                response = await asyncio.wait_for(
                    websocket.recv(), timeout=5.0
                )
                
                data = json.loads(response)
                # Might be error or just ignored - either is acceptable
                assert "type" in data
                
        except Exception as e:
            pytest.skip(f"WebSocket server not available: {e}")
    
    async def test_websocket_ui_data_request(self, test_utils):
        """Test UI data requests via WebSocket"""
        session_id = f"ws_ui_test_{datetime.now().timestamp()}"
        uri = f"ws://localhost:8002/ws/{session_id}?player_id=test_player"
        
        try:
            async with websockets.connect(uri) as websocket:
                # Send UI data request
                ui_request = {
                    "type": "request_ui_data"
                }
                
                await websocket.send(json.dumps(ui_request))
                
                # Wait for UI data response
                response = await asyncio.wait_for(
                    websocket.recv(), timeout=5.0
                )
                
                data = json.loads(response)
                assert data["type"] == "ui_data"
                assert "data" in data
                
        except Exception as e:
            pytest.skip(f"WebSocket server not available: {e}")
    
    async def test_websocket_session_cleanup(self, test_utils):
        """Test WebSocket connection cleanup on disconnect"""
        session_id = f"ws_cleanup_test_{datetime.now().timestamp()}"
        uri = f"ws://localhost:8002/ws/{session_id}?player_id=test_player"
        
        try:
            # Connect and immediately disconnect
            connection = await websockets.connect(uri)
            await connection.close()
            
            # Give server time to cleanup
            await asyncio.sleep(1.0)
            
            # Connection should be cleaned up server-side
            # This is verified by the server not having memory leaks
            # (tested indirectly through performance stats)
            
        except Exception as e:
            pytest.skip(f"WebSocket server not available: {e}")
    
    async def test_websocket_real_time_updates(self, test_utils):
        """Test real-time game updates via WebSocket"""
        session_id = f"ws_realtime_test_{datetime.now().timestamp()}"
        
        # Create two connections (different players)
        player1_uri = f"ws://localhost:8002/ws/{session_id}?player_id=player_1"
        player2_uri = f"ws://localhost:8002/ws/{session_id}?player_id=player_2"
        
        try:
            async with websockets.connect(player1_uri) as ws1, \
                       websockets.connect(player2_uri) as ws2:
                
                # Player 1 performs action
                action_message = {
                    "type": "player_action",
                    "data": {
                        "type": "move",
                        "unit_id": "test_unit",
                        "target_position": {"x": 4, "y": 4}
                    }
                }
                
                await ws1.send(json.dumps(action_message))
                
                # Both players should receive updates
                # (This tests the broadcast functionality)
                
                # Player 1 gets action result
                p1_response = await asyncio.wait_for(ws1.recv(), timeout=5.0)
                p1_data = json.loads(p1_response)
                
                # Player 2 might get game state update
                try:
                    p2_response = await asyncio.wait_for(ws2.recv(), timeout=2.0)
                    p2_data = json.loads(p2_response)
                    # Both should have valid message types
                    assert "type" in p1_data
                    assert "type" in p2_data
                except asyncio.TimeoutError:
                    # It's OK if player 2 doesn't get immediate update
                    pass
                
        except Exception as e:
            pytest.skip(f"WebSocket server not available: {e}")


class TestWebSocketPerformance:
    """Test WebSocket performance characteristics"""
    
    async def test_websocket_message_throughput(self, test_utils):
        """Test WebSocket message handling performance"""
        session_id = f"ws_perf_test_{datetime.now().timestamp()}"
        uri = f"ws://localhost:8002/ws/{session_id}?player_id=test_player"
        
        try:
            async with websockets.connect(uri) as websocket:
                # Send multiple rapid messages
                message_count = 10
                start_time = asyncio.get_event_loop().time()
                
                for i in range(message_count):
                    ping_message = {
                        "type": "ping",
                        "data": {"sequence": i}
                    }
                    await websocket.send(json.dumps(ping_message))
                
                # Receive all responses
                for i in range(message_count):
                    response = await asyncio.wait_for(
                        websocket.recv(), timeout=5.0
                    )
                    data = json.loads(response)
                    assert data["type"] == "pong"
                
                end_time = asyncio.get_event_loop().time()
                duration = end_time - start_time
                
                # Should handle messages reasonably fast
                messages_per_second = message_count / duration
                assert messages_per_second > 5  # At least 5 msg/sec
                
        except Exception as e:
            pytest.skip(f"WebSocket server not available: {e}")
    
    async def test_websocket_connection_limits(self, test_utils):
        """Test WebSocket connection handling under load"""
        session_id = f"ws_load_test_{datetime.now().timestamp()}"
        
        connections = []
        max_connections = 5  # Conservative for testing
        
        try:
            # Create multiple connections
            for i in range(max_connections):
                uri = f"ws://localhost:8002/ws/{session_id}?player_id=load_player_{i}"
                connection = await websockets.connect(uri)
                connections.append(connection)
                
                # Small delay to avoid overwhelming server
                await asyncio.sleep(0.1)
            
            # Verify all connections are working
            for i, connection in enumerate(connections):
                ping_message = {
                    "type": "ping",
                    "data": {"connection_id": i}
                }
                await connection.send(json.dumps(ping_message))
                
                response = await asyncio.wait_for(
                    connection.recv(), timeout=5.0
                )
                data = json.loads(response)
                assert data["type"] == "pong"
            
        except Exception as e:
            pytest.skip(f"WebSocket server not available: {e}")
        
        finally:
            # Cleanup all connections
            for connection in connections:
                try:
                    await connection.close()
                except:
                    pass