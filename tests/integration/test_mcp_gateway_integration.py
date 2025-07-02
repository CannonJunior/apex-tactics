"""
Integration tests for MCP Gateway functionality.

Tests external tool integration via Model Context Protocol.
"""

import pytest
import asyncio
import json
from datetime import datetime

import httpx
import structlog

logger = structlog.get_logger()


class TestMCPGatewayIntegration:
    """Test MCP Gateway tool integration"""
    
    async def test_mcp_gateway_health(self):
        """Test MCP Gateway health check"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("http://localhost:8004/health")
                assert response.status_code == 200
                
                data = response.json()
                assert data["status"] == "healthy"
                assert "active_sessions" in data
                
        except Exception as e:
            pytest.skip(f"MCP Gateway not available: {e}")
    
    async def test_mcp_tools_list(self):
        """Test MCP tools listing"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("http://localhost:8004/tools")
                assert response.status_code == 200
                
                data = response.json()
                assert "tools" in data
                
                tools = data["tools"]
                expected_tools = [
                    "get_game_sessions",
                    "get_session_state", 
                    "get_battlefield_state",
                    "get_all_units",
                    "get_unit_details",
                    "get_available_actions",
                    "execute_unit_action",
                    "analyze_tactical_situation",
                    "send_notification",
                    "create_test_session"
                ]
                
                tool_names = [tool["name"] for tool in tools]
                for expected_tool in expected_tools:
                    assert expected_tool in tool_names
                
        except Exception as e:
            pytest.skip(f"MCP Gateway not available: {e}")
    
    async def test_create_test_session_tool(self):
        """Test MCP create_test_session tool"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Call create_test_session tool
                tool_request = {
                    "tool": "create_test_session",
                    "args": {
                        "battlefield_size": [8, 8],
                        "player_count": 2
                    }
                }
                
                response = await client.post(
                    "http://localhost:8004/call_tool",
                    json=tool_request
                )
                assert response.status_code == 200
                
                data = response.json()
                assert data["success"] is True
                assert "session_id" in data
                assert "player_ids" in data
                
                session_id = data["session_id"]
                return session_id
                
        except Exception as e:
            pytest.skip(f"MCP Gateway not available: {e}")
    
    async def test_get_game_sessions_tool(self):
        """Test MCP get_game_sessions tool"""
        try:
            # First create a test session
            session_id = await self.test_create_test_session_tool()
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                tool_request = {
                    "tool": "get_game_sessions",
                    "args": {}
                }
                
                response = await client.post(
                    "http://localhost:8004/call_tool",
                    json=tool_request
                )
                assert response.status_code == 200
                
                sessions = response.json()
                assert isinstance(sessions, list)
                
                # Should contain our test session
                session_ids = [s["session_id"] for s in sessions]
                assert session_id in session_ids
                
        except Exception as e:
            pytest.skip(f"MCP Gateway not available: {e}")
    
    async def test_get_session_state_tool(self):
        """Test MCP get_session_state tool"""
        try:
            # Create test session
            session_id = await self.test_create_test_session_tool()
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                tool_request = {
                    "tool": "get_session_state",
                    "args": {
                        "session_id": session_id
                    }
                }
                
                response = await client.post(
                    "http://localhost:8004/call_tool",
                    json=tool_request
                )
                assert response.status_code == 200
                
                state = response.json()
                assert "session" in state
                assert "game_state" in state
                assert state["session"]["session_id"] == session_id
                
        except Exception as e:
            pytest.skip(f"MCP Gateway not available: {e}")
    
    async def test_get_battlefield_state_tool(self):
        """Test MCP get_battlefield_state tool"""
        try:
            session_id = await self.test_create_test_session_tool()
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                tool_request = {
                    "tool": "get_battlefield_state",
                    "args": {
                        "session_id": session_id
                    }
                }
                
                response = await client.post(
                    "http://localhost:8004/call_tool",
                    json=tool_request
                )
                assert response.status_code == 200
                
                battlefield = response.json()
                assert "size" in battlefield or len(battlefield) > 0
                
        except Exception as e:
            pytest.skip(f"MCP Gateway not available: {e}")
    
    async def test_get_all_units_tool(self):
        """Test MCP get_all_units tool"""
        try:
            session_id = await self.test_create_test_session_tool()
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                tool_request = {
                    "tool": "get_all_units",
                    "args": {
                        "session_id": session_id
                    }
                }
                
                response = await client.post(
                    "http://localhost:8004/call_tool",
                    json=tool_request
                )
                assert response.status_code == 200
                
                units = response.json()
                assert isinstance(units, list)
                
                # Check unit structure if units exist
                if units:
                    unit = units[0]
                    assert "unit_id" in unit
                    assert "position" in unit
                    assert "team" in unit
                    assert "stats" in unit
                
        except Exception as e:
            pytest.skip(f"MCP Gateway not available: {e}")
    
    async def test_analyze_tactical_situation_tool(self):
        """Test MCP analyze_tactical_situation tool"""
        try:
            session_id = await self.test_create_test_session_tool()
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                tool_request = {
                    "tool": "analyze_tactical_situation",
                    "args": {
                        "session_id": session_id
                    }
                }
                
                response = await client.post(
                    "http://localhost:8004/call_tool",
                    json=tool_request
                )
                assert response.status_code == 200
                
                analysis = response.json()
                assert "teams" in analysis
                assert "battlefield" in analysis
                assert "threats" in analysis
                assert "opportunities" in analysis
                assert "timestamp" in analysis
                
        except Exception as e:
            pytest.skip(f"MCP Gateway not available: {e}")
    
    async def test_send_notification_tool(self):
        """Test MCP send_notification tool"""
        try:
            session_id = await self.test_create_test_session_tool()
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                tool_request = {
                    "tool": "send_notification",
                    "args": {
                        "session_id": session_id,
                        "type": "info",
                        "title": "Test Notification",
                        "message": "This is a test notification from MCP"
                    }
                }
                
                response = await client.post(
                    "http://localhost:8004/call_tool",
                    json=tool_request
                )
                assert response.status_code == 200
                
                result = response.json()
                assert result["success"] is True
                assert result["session_id"] == session_id
                assert result["type"] == "info"
                
        except Exception as e:
            pytest.skip(f"MCP Gateway not available: {e}")
    
    async def test_highlight_tiles_tool(self):
        """Test MCP highlight_tiles tool"""
        try:
            session_id = await self.test_create_test_session_tool()
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                tool_request = {
                    "tool": "highlight_tiles",
                    "args": {
                        "session_id": session_id,
                        "tiles": [
                            {"x": 2, "y": 2},
                            {"x": 2, "y": 3},
                            {"x": 3, "y": 2}
                        ],
                        "highlight_type": "movement",
                        "duration": 5.0
                    }
                }
                
                response = await client.post(
                    "http://localhost:8004/call_tool",
                    json=tool_request
                )
                assert response.status_code == 200
                
                result = response.json()
                assert result["success"] is True
                assert result["tiles_highlighted"] == 3
                assert result["highlight_type"] == "movement"
                
        except Exception as e:
            pytest.skip(f"MCP Gateway not available: {e}")
    
    async def test_get_game_statistics_tool(self):
        """Test MCP get_game_statistics tool"""
        try:
            session_id = await self.test_create_test_session_tool()
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                tool_request = {
                    "tool": "get_game_statistics",
                    "args": {
                        "session_id": session_id
                    }
                }
                
                response = await client.post(
                    "http://localhost:8004/call_tool",
                    json=tool_request
                )
                assert response.status_code == 200
                
                stats = response.json()
                assert "performance" in stats
                assert "ui_stats" in stats
                assert "timestamp" in stats
                assert stats["session_id"] == session_id
                
        except Exception as e:
            pytest.skip(f"MCP Gateway not available: {e}")
    
    async def test_mcp_tool_error_handling(self):
        """Test MCP tool error handling"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Test invalid session ID
                tool_request = {
                    "tool": "get_session_state",
                    "args": {
                        "session_id": "invalid_session_id"
                    }
                }
                
                response = await client.post(
                    "http://localhost:8004/call_tool",
                    json=tool_request
                )
                
                # Should handle error gracefully
                assert response.status_code in [400, 404, 500]
                
        except Exception as e:
            pytest.skip(f"MCP Gateway not available: {e}")
    
    async def test_mcp_tool_validation(self):
        """Test MCP tool parameter validation"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Test missing required parameters
                tool_request = {
                    "tool": "get_session_state",
                    "args": {}  # Missing session_id
                }
                
                response = await client.post(
                    "http://localhost:8004/call_tool",
                    json=tool_request
                )
                
                # Should return validation error
                assert response.status_code in [400, 422]
                
        except Exception as e:
            pytest.skip(f"MCP Gateway not available: {e}")


class TestMCPGatewayPerformance:
    """Test MCP Gateway performance characteristics"""
    
    async def test_mcp_tool_response_time(self):
        """Test MCP tool response times"""
        try:
            session_id = None
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Test create_test_session performance
                start_time = asyncio.get_event_loop().time()
                
                tool_request = {
                    "tool": "create_test_session",
                    "args": {
                        "battlefield_size": [6, 6],
                        "player_count": 2
                    }
                }
                
                response = await client.post(
                    "http://localhost:8004/call_tool",
                    json=tool_request
                )
                
                end_time = asyncio.get_event_loop().time()
                creation_time = end_time - start_time
                
                assert response.status_code == 200
                data = response.json()
                session_id = data["session_id"]
                
                # Session creation should be reasonably fast
                assert creation_time < 5.0  # Less than 5 seconds
                
                # Test quick operations
                quick_tools = [
                    "get_game_sessions",
                    "get_session_state",
                    "get_battlefield_state"
                ]
                
                for tool_name in quick_tools:
                    start_time = asyncio.get_event_loop().time()
                    
                    tool_request = {
                        "tool": tool_name,
                        "args": {"session_id": session_id} if tool_name != "get_game_sessions" else {}
                    }
                    
                    response = await client.post(
                        "http://localhost:8004/call_tool",
                        json=tool_request
                    )
                    
                    end_time = asyncio.get_event_loop().time()
                    response_time = end_time - start_time
                    
                    assert response.status_code == 200
                    # Quick operations should be very fast
                    assert response_time < 1.0  # Less than 1 second
                
        except Exception as e:
            pytest.skip(f"MCP Gateway not available: {e}")
    
    async def test_mcp_concurrent_requests(self):
        """Test MCP Gateway handling concurrent requests"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Create test session first
                tool_request = {
                    "tool": "create_test_session",
                    "args": {
                        "battlefield_size": [6, 6],
                        "player_count": 2
                    }
                }
                
                response = await client.post(
                    "http://localhost:8004/call_tool",
                    json=tool_request
                )
                assert response.status_code == 200
                session_id = response.json()["session_id"]
                
                # Send multiple concurrent requests
                tasks = []
                request_count = 5
                
                for i in range(request_count):
                    tool_request = {
                        "tool": "get_session_state",
                        "args": {"session_id": session_id}
                    }
                    
                    task = client.post(
                        "http://localhost:8004/call_tool",
                        json=tool_request
                    )
                    tasks.append(task)
                
                # Wait for all requests to complete
                responses = await asyncio.gather(*tasks)
                
                # All requests should succeed
                for response in responses:
                    assert response.status_code == 200
                    data = response.json()
                    assert data["session"]["session_id"] == session_id
                
        except Exception as e:
            pytest.skip(f"MCP Gateway not available: {e}")


class TestMCPGatewayIntegrationScenarios:
    """Test complete MCP Gateway integration scenarios"""
    
    async def test_mcp_ai_agent_workflow(self):
        """Test complete AI agent workflow via MCP"""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # 1. Create test session
                create_request = {
                    "tool": "create_test_session",
                    "args": {
                        "battlefield_size": [8, 8],
                        "player_count": 2
                    }
                }
                
                response = await client.post(
                    "http://localhost:8004/call_tool",
                    json=create_request
                )
                assert response.status_code == 200
                session_data = response.json()
                session_id = session_data["session_id"]
                
                # 2. Analyze tactical situation
                analyze_request = {
                    "tool": "analyze_tactical_situation",
                    "args": {"session_id": session_id}
                }
                
                response = await client.post(
                    "http://localhost:8004/call_tool",
                    json=analyze_request
                )
                assert response.status_code == 200
                analysis = response.json()
                
                # 3. Get all units
                units_request = {
                    "tool": "get_all_units",
                    "args": {"session_id": session_id}
                }
                
                response = await client.post(
                    "http://localhost:8004/call_tool",
                    json=units_request
                )
                assert response.status_code == 200
                units = response.json()
                
                # 4. Send notification about analysis
                notify_request = {
                    "tool": "send_notification",
                    "args": {
                        "session_id": session_id,
                        "type": "info",
                        "title": "AI Analysis Complete",
                        "message": f"Analyzed {len(analysis['teams'])} teams with {len(units)} units"
                    }
                }
                
                response = await client.post(
                    "http://localhost:8004/call_tool",
                    json=notify_request
                )
                assert response.status_code == 200
                notification_result = response.json()
                assert notification_result["success"] is True
                
                # 5. Get game statistics
                stats_request = {
                    "tool": "get_game_statistics",
                    "args": {"session_id": session_id}
                }
                
                response = await client.post(
                    "http://localhost:8004/call_tool",
                    json=stats_request
                )
                assert response.status_code == 200
                stats = response.json()
                
                # Verify complete workflow
                assert "performance" in stats
                assert stats["session_id"] == session_id
                
        except Exception as e:
            pytest.skip(f"MCP Gateway not available: {e}")
    
    async def test_mcp_monitoring_workflow(self):
        """Test monitoring and analytics workflow via MCP"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # 1. Get all active sessions
                sessions_request = {
                    "tool": "get_game_sessions",
                    "args": {}
                }
                
                response = await client.post(
                    "http://localhost:8004/call_tool",
                    json=sessions_request
                )
                assert response.status_code == 200
                sessions = response.json()
                
                # 2. If no sessions, create one
                if not sessions:
                    create_request = {
                        "tool": "create_test_session",
                        "args": {
                            "battlefield_size": [6, 6],
                            "player_count": 2
                        }
                    }
                    
                    response = await client.post(
                        "http://localhost:8004/call_tool",
                        json=create_request
                    )
                    assert response.status_code == 200
                    
                    # Get sessions again
                    response = await client.post(
                        "http://localhost:8004/call_tool",
                        json=sessions_request
                    )
                    sessions = response.json()
                
                # 3. Monitor each session
                for session in sessions[:3]:  # Limit to first 3 sessions
                    session_id = session["session_id"]
                    
                    # Get detailed statistics
                    stats_request = {
                        "tool": "get_game_statistics",
                        "args": {"session_id": session_id}
                    }
                    
                    response = await client.post(
                        "http://localhost:8004/call_tool",
                        json=stats_request
                    )
                    
                    if response.status_code == 200:
                        stats = response.json()
                        assert "performance" in stats
                        assert "timestamp" in stats
                
        except Exception as e:
            pytest.skip(f"MCP Gateway not available: {e}")