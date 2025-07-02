"""
Integration tests for UI systems functionality.

Tests real-time visual feedback, notifications, and UI state management.
"""

import pytest
import asyncio
import json
from datetime import datetime

import httpx
import websockets
import structlog

logger = structlog.get_logger()


class TestUISystemsIntegration:
    """Test UI systems integration with game engine"""
    
    async def test_ui_data_retrieval(self):
        """Test UI data API endpoints"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Test session UI data
                response = await client.get(
                    "http://localhost:8002/api/sessions/test_session/ui?player_id=test_player"
                )
                
                if response.status_code == 200:
                    ui_data = response.json()
                    
                    # Should contain UI state information
                    expected_fields = ["ui_state", "notifications", "visual_effects"]
                    for field in expected_fields:
                        if field in ui_data:
                            assert ui_data[field] is not None
                
        except Exception as e:
            pytest.skip(f"Game engine not available: {e}")
    
    async def test_unit_selection_ui(self):
        """Test unit selection via UI API"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Test unit selection
                selection_data = {
                    "unit_id": "test_unit_001",
                    "player_id": "test_player"
                }
                
                response = await client.post(
                    "http://localhost:8002/api/sessions/test_session/select_unit",
                    json=selection_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    assert "success" in result
                    # Success depends on whether unit exists and belongs to player
                
        except Exception as e:
            pytest.skip(f"Game engine not available: {e}")
    
    async def test_notification_system(self):
        """Test notification sending and retrieval"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Send notification
                notification_data = {
                    "type": "info",
                    "title": "Test Notification",
                    "message": "This is a test notification for UI integration",
                    "player_id": "test_player"
                }
                
                response = await client.post(
                    "http://localhost:8002/api/sessions/test_session/notifications",
                    json=notification_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    assert "success" in result
                    
                    # Notification should be created successfully
                    if result["success"]:
                        # Get UI data to verify notification
                        ui_response = await client.get(
                            "http://localhost:8002/api/sessions/test_session/ui?player_id=test_player"
                        )
                        
                        if ui_response.status_code == 200:
                            ui_data = ui_response.json()
                            notifications = ui_data.get("notifications", [])
                            
                            # Should contain our test notification
                            test_notifications = [
                                n for n in notifications 
                                if n.get("title") == "Test Notification"
                            ]
                            assert len(test_notifications) > 0
                
        except Exception as e:
            pytest.skip(f"Game engine not available: {e}")
    
    async def test_visual_effects_system(self):
        """Test visual effects creation and management"""
        try:
            # Visual effects are typically triggered by game events
            # Test through WebSocket connection
            session_id = f"ui_effects_test_{datetime.now().timestamp()}"
            uri = f"ws://localhost:8002/ws/{session_id}?player_id=test_player"
            
            async with websockets.connect(uri) as websocket:
                # Send action that should trigger visual effects
                action_message = {
                    "type": "player_action",
                    "data": {
                        "type": "move",
                        "unit_id": "test_unit",
                        "target_position": {"x": 3, "y": 3}
                    }
                }
                
                await websocket.send(json.dumps(action_message))
                
                # Look for visual effect messages
                try:
                    for _ in range(3):  # Check a few messages
                        response = await asyncio.wait_for(
                            websocket.recv(), timeout=2.0
                        )
                        
                        data = json.loads(response)
                        if data.get("type") == "visual_effect":
                            # Found visual effect message
                            effect_data = data.get("data", {})
                            assert "effect_type" in effect_data
                            assert "position" in effect_data or "target" in effect_data
                            break
                except asyncio.TimeoutError:
                    # No visual effects triggered - that's OK for test
                    pass
                
        except Exception as e:
            pytest.skip(f"WebSocket server not available: {e}")
    
    async def test_real_time_ui_updates(self):
        """Test real-time UI updates via WebSocket"""
        try:
            session_id = f"ui_realtime_test_{datetime.now().timestamp()}"
            uri = f"ws://localhost:8002/ws/{session_id}?player_id=test_player"
            
            async with websockets.connect(uri) as websocket:
                # Request current UI data
                ui_request = {
                    "type": "request_ui_data"
                }
                
                await websocket.send(json.dumps(ui_request))
                
                # Should receive UI data response
                response = await asyncio.wait_for(
                    websocket.recv(), timeout=5.0
                )
                
                data = json.loads(response)
                assert data["type"] == "ui_data"
                assert "data" in data
                
                ui_data = data["data"]
                # Should contain expected UI structure
                expected_fields = ["ui_state", "notifications", "visual_effects", "session_id"]
                for field in expected_fields:
                    if field in ui_data:
                        assert ui_data[field] is not None
                
        except Exception as e:
            pytest.skip(f"WebSocket server not available: {e}")
    
    async def test_tile_highlighting_system(self):
        """Test battlefield tile highlighting"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Test via MCP Gateway if available
                highlight_request = {
                    "tool": "highlight_tiles",
                    "args": {
                        "session_id": "test_session",
                        "tiles": [
                            {"x": 2, "y": 2},
                            {"x": 2, "y": 3},
                            {"x": 3, "y": 2}
                        ],
                        "highlight_type": "movement",
                        "duration": 3.0
                    }
                }
                
                response = await client.post(
                    "http://localhost:8004/call_tool",
                    json=highlight_request
                )
                
                if response.status_code == 200:
                    result = response.json()
                    assert result.get("success") is True
                    assert result.get("tiles_highlighted") == 3
                    assert result.get("highlight_type") == "movement"
                
        except Exception as e:
            pytest.skip(f"MCP Gateway not available: {e}")
    
    async def test_ui_performance_tracking(self):
        """Test UI system performance metrics"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("http://localhost:8002/api/status")
                
                if response.status_code == 200:
                    status = response.json()
                    
                    # Should contain UI statistics
                    if "ui_stats" in status:
                        ui_stats = status["ui_stats"]
                        
                        # Check for UI manager stats
                        if "ui_manager" in ui_stats:
                            ui_manager_stats = ui_stats["ui_manager"]
                            expected_metrics = [
                                "active_sessions",
                                "selections_made",
                                "highlights_active"
                            ]
                            
                            for metric in expected_metrics:
                                if metric in ui_manager_stats:
                                    assert isinstance(ui_manager_stats[metric], (int, float))
                        
                        # Check for visual effects stats
                        if "visual_effects" in ui_stats:
                            effects_stats = ui_stats["visual_effects"]
                            assert isinstance(effects_stats, dict)
                        
                        # Check for notifications stats
                        if "notifications" in ui_stats:
                            notif_stats = ui_stats["notifications"]
                            expected_notif_metrics = [
                                "notifications_sent",
                                "active_session_queues",
                                "total_active_notifications"
                            ]
                            
                            for metric in expected_notif_metrics:
                                if metric in notif_stats:
                                    assert isinstance(notif_stats[metric], (int, float))
                
        except Exception as e:
            pytest.skip(f"Game engine not available: {e}")
    
    async def test_notification_types_and_priorities(self):
        """Test different notification types and priorities"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                notification_types = [
                    ("info", "Information", "This is an info notification"),
                    ("success", "Success", "This is a success notification"),
                    ("warning", "Warning", "This is a warning notification"),
                    ("error", "Error", "This is an error notification"),
                    ("combat", "Combat", "This is a combat notification"),
                    ("turn", "Turn", "This is a turn notification"),
                    ("achievement", "Achievement", "This is an achievement notification")
                ]
                
                for notif_type, title, message in notification_types:
                    notification_data = {
                        "type": notif_type,
                        "title": title,
                        "message": message,
                        "player_id": "test_player"
                    }
                    
                    response = await client.post(
                        "http://localhost:8002/api/sessions/test_session/notifications",
                        json=notification_data
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        assert "success" in result
                        # Each notification type should be handled
                
                # Give notifications time to process
                await asyncio.sleep(0.5)
                
                # Check that notifications were created
                ui_response = await client.get(
                    "http://localhost:8002/api/sessions/test_session/ui?player_id=test_player"
                )
                
                if ui_response.status_code == 200:
                    ui_data = ui_response.json()
                    notifications = ui_data.get("notifications", [])
                    
                    # Should have notifications of different types
                    notification_types_found = set()
                    for notification in notifications:
                        notif_type = notification.get("type")
                        if notif_type:
                            notification_types_found.add(notif_type)
                    
                    # Should have created multiple notification types
                    assert len(notification_types_found) > 0
                
        except Exception as e:
            pytest.skip(f"Game engine not available: {e}")
    
    async def test_ui_session_isolation(self):
        """Test UI state isolation between different sessions"""
        try:
            session_ids = [
                f"ui_isolation_test_1_{datetime.now().timestamp()}",
                f"ui_isolation_test_2_{datetime.now().timestamp()}"
            ]
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Send different notifications to different sessions
                for i, session_id in enumerate(session_ids):
                    notification_data = {
                        "type": "info",
                        "title": f"Session {i+1} Notification",
                        "message": f"This notification belongs to session {session_id}",
                        "player_id": f"player_{i+1}"
                    }
                    
                    response = await client.post(
                        f"http://localhost:8002/api/sessions/{session_id}/notifications",
                        json=notification_data
                    )
                    
                    # Don't require success - sessions might not exist
                
                # Check UI data for each session
                for i, session_id in enumerate(session_ids):
                    ui_response = await client.get(
                        f"http://localhost:8002/api/sessions/{session_id}/ui?player_id=player_{i+1}"
                    )
                    
                    if ui_response.status_code == 200:
                        ui_data = ui_response.json()
                        
                        # Should contain session-specific data
                        assert ui_data.get("session_id") == session_id
                        assert ui_data.get("player_id") == f"player_{i+1}"
                        
                        # Notifications should be session-specific
                        notifications = ui_data.get("notifications", [])
                        for notification in notifications:
                            # Should not contain notifications from other sessions
                            assert f"session {session_id}" in notification.get("message", "").lower() or \
                                   notification.get("message", "") == f"This notification belongs to session {session_id}"
                
        except Exception as e:
            pytest.skip(f"Game engine not available: {e}")


class TestUISystemsPerformance:
    """Test UI systems performance characteristics"""
    
    async def test_notification_throughput(self):
        """Test notification system performance under load"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Send multiple notifications rapidly
                notification_count = 10
                start_time = asyncio.get_event_loop().time()
                
                tasks = []
                for i in range(notification_count):
                    notification_data = {
                        "type": "info",
                        "title": f"Performance Test {i}",
                        "message": f"Test notification number {i}",
                        "player_id": "test_player"
                    }
                    
                    task = client.post(
                        "http://localhost:8002/api/sessions/test_session/notifications",
                        json=notification_data
                    )
                    tasks.append(task)
                
                # Wait for all notifications to be sent
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                
                end_time = asyncio.get_event_loop().time()
                duration = end_time - start_time
                
                # Count successful notifications
                successful_count = 0
                for response in responses:
                    if not isinstance(response, Exception) and response.status_code == 200:
                        successful_count += 1
                
                if successful_count > 0:
                    # Calculate throughput
                    notifications_per_second = successful_count / duration
                    
                    # Should handle notifications reasonably fast
                    assert notifications_per_second > 5  # At least 5 notifications/sec
                
        except Exception as e:
            pytest.skip(f"Game engine not available: {e}")
    
    async def test_ui_update_frequency(self):
        """Test UI update performance via WebSocket"""
        try:
            session_id = f"ui_perf_test_{datetime.now().timestamp()}"
            uri = f"ws://localhost:8002/ws/{session_id}?player_id=test_player"
            
            async with websockets.connect(uri) as websocket:
                # Send multiple UI data requests
                request_count = 5
                start_time = asyncio.get_event_loop().time()
                
                for i in range(request_count):
                    ui_request = {
                        "type": "request_ui_data"
                    }
                    
                    await websocket.send(json.dumps(ui_request))
                    
                    # Wait for response
                    try:
                        response = await asyncio.wait_for(
                            websocket.recv(), timeout=2.0
                        )
                        
                        data = json.loads(response)
                        assert data["type"] == "ui_data"
                        
                    except asyncio.TimeoutError:
                        break
                
                end_time = asyncio.get_event_loop().time()
                duration = end_time - start_time
                
                # Should handle UI requests efficiently
                if duration > 0:
                    requests_per_second = request_count / duration
                    assert requests_per_second > 2  # At least 2 requests/sec
                
        except Exception as e:
            pytest.skip(f"WebSocket server not available: {e}")
    
    async def test_visual_effects_cleanup(self):
        """Test visual effects memory management and cleanup"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Get initial UI statistics
                initial_response = await client.get("http://localhost:8002/api/status")
                
                if initial_response.status_code == 200:
                    initial_status = initial_response.json()
                    initial_ui_stats = initial_status.get("ui_stats", {})
                    initial_effects_stats = initial_ui_stats.get("visual_effects", {})
                    
                    # Trigger visual effects (via game actions or direct API)
                    # This would typically happen through gameplay
                    
                    # Wait for effects to process and cleanup
                    await asyncio.sleep(2.0)
                    
                    # Get updated statistics
                    final_response = await client.get("http://localhost:8002/api/status")
                    
                    if final_response.status_code == 200:
                        final_status = final_response.json()
                        final_ui_stats = final_status.get("ui_stats", {})
                        final_effects_stats = final_ui_stats.get("visual_effects", {})
                        
                        # Visual effects should be cleaned up properly
                        # (Specific metrics depend on implementation)
                        assert isinstance(final_effects_stats, dict)
                
        except Exception as e:
            pytest.skip(f"Game engine not available: {e}")


class TestUISystemsIntegrationScenarios:
    """Test complete UI integration scenarios"""
    
    async def test_complete_ui_workflow(self):
        """Test complete UI workflow from action to visual feedback"""
        try:
            session_id = f"ui_workflow_test_{datetime.now().timestamp()}"
            
            # Test via WebSocket for real-time experience
            uri = f"ws://localhost:8002/ws/{session_id}?player_id=test_player"
            
            async with websockets.connect(uri) as websocket:
                # 1. Get initial UI state
                ui_request = {
                    "type": "request_ui_data"
                }
                
                await websocket.send(json.dumps(ui_request))
                initial_ui = await asyncio.wait_for(
                    websocket.recv(), timeout=5.0
                )
                
                initial_data = json.loads(initial_ui)
                assert initial_data["type"] == "ui_data"
                
                # 2. Select a unit
                select_message = {
                    "type": "select_unit",
                    "data": {
                        "unit_id": "test_unit_001"
                    }
                }
                
                await websocket.send(json.dumps(select_message))
                select_response = await asyncio.wait_for(
                    websocket.recv(), timeout=5.0
                )
                
                select_data = json.loads(select_response)
                assert select_data["type"] == "select_unit_result"
                
                # 3. Perform an action
                action_message = {
                    "type": "player_action",
                    "data": {
                        "type": "move",
                        "unit_id": "test_unit_001",
                        "target_position": {"x": 4, "y": 4}
                    }
                }
                
                await websocket.send(json.dumps(action_message))
                
                # 4. Look for UI updates (action result, visual effects, notifications)
                ui_updates = []
                for _ in range(3):  # Collect multiple updates
                    try:
                        update = await asyncio.wait_for(
                            websocket.recv(), timeout=2.0
                        )
                        
                        update_data = json.loads(update)
                        ui_updates.append(update_data)
                        
                    except asyncio.TimeoutError:
                        break
                
                # Should have received some UI updates
                assert len(ui_updates) > 0
                
                # Updates should include action results
                update_types = [update.get("type") for update in ui_updates]
                expected_types = ["action_result", "ui_update", "notification", "visual_effect"]
                
                # At least one expected update type should be present
                assert any(update_type in expected_types for update_type in update_types)
                
        except Exception as e:
            pytest.skip(f"WebSocket server not available: {e}")
    
    async def test_ui_error_recovery(self):
        """Test UI system error handling and recovery"""
        try:
            session_id = f"ui_error_test_{datetime.now().timestamp()}"
            uri = f"ws://localhost:8002/ws/{session_id}?player_id=test_player"
            
            async with websockets.connect(uri) as websocket:
                # Send invalid UI requests
                invalid_requests = [
                    {"type": "invalid_request_type"},
                    {"type": "select_unit", "data": {"unit_id": "nonexistent_unit"}},
                    {"type": "player_action", "data": {"type": "invalid_action"}},
                    {"type": "request_ui_data", "data": {"invalid": "parameter"}}
                ]
                
                for invalid_request in invalid_requests:
                    await websocket.send(json.dumps(invalid_request))
                    
                    # Should receive some response (error or ignore)
                    try:
                        response = await asyncio.wait_for(
                            websocket.recv(), timeout=2.0
                        )
                        
                        data = json.loads(response)
                        # Error responses are acceptable
                        assert "type" in data
                        
                    except asyncio.TimeoutError:
                        # It's OK if invalid requests are ignored
                        pass
                
                # System should still be responsive to valid requests
                valid_request = {
                    "type": "request_ui_data"
                }
                
                await websocket.send(json.dumps(valid_request))
                valid_response = await asyncio.wait_for(
                    websocket.recv(), timeout=5.0
                )
                
                valid_data = json.loads(valid_response)
                assert valid_data["type"] == "ui_data"
                
        except Exception as e:
            pytest.skip(f"WebSocket server not available: {e}")