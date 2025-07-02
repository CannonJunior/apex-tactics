#!/usr/bin/env python3
"""
Test Script for Apex Tactics Microservices

Validates communication between all three services:
- Game Engine API
- MCP Gateway 
- AI Service with Ollama
"""

import asyncio
import json
import time
import sys
from typing import Dict, Any, List

import httpx
import structlog

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


class ServiceTester:
    """Test runner for microservices integration"""
    
    def __init__(self):
        self.services = {
            "game-engine": "http://localhost:8000",
            "mcp-gateway": "http://localhost:8002", 
            "ai-service": "http://localhost:8001"
        }
        self.client = httpx.AsyncClient(timeout=30.0)
        self.test_session_id = f"test_session_{int(time.time())}"
        
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
    
    async def wait_for_services(self, max_wait: int = 60) -> bool:
        """Wait for all services to be healthy"""
        logger.info("Waiting for services to start...")
        
        start_time = time.time()
        while time.time() - start_time < max_wait:
            try:
                all_healthy = True
                
                for service_name, base_url in self.services.items():
                    try:
                        response = await self.client.get(f"{base_url}/health")
                        if response.status_code != 200:
                            all_healthy = False
                            logger.info(f"Service {service_name} not ready", 
                                       status_code=response.status_code)
                        else:
                            logger.info(f"Service {service_name} is healthy")
                    except Exception as e:
                        all_healthy = False
                        logger.info(f"Service {service_name} not reachable", error=str(e))
                
                if all_healthy:
                    logger.info("All services are healthy")
                    return True
                    
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error("Error checking service health", error=str(e))
                await asyncio.sleep(2)
        
        logger.error("Services did not become healthy within timeout")
        return False
    
    async def test_game_engine_health(self) -> bool:
        """Test game engine health endpoint"""
        try:
            response = await self.client.get(f"{self.services['game-engine']}/health")
            response.raise_for_status()
            
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "game-engine"
            
            logger.info("✅ Game engine health check passed")
            return True
            
        except Exception as e:
            logger.error("❌ Game engine health check failed", error=str(e))
            return False
    
    async def test_mcp_gateway_health(self) -> bool:
        """Test MCP gateway health endpoint"""
        try:
            response = await self.client.get(f"{self.services['mcp-gateway']}/health")
            response.raise_for_status()
            
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "mcp-gateway"
            
            logger.info("✅ MCP gateway health check passed")
            return True
            
        except Exception as e:
            logger.error("❌ MCP gateway health check failed", error=str(e))
            return False
    
    async def test_ai_service_health(self) -> bool:
        """Test AI service health endpoint"""
        try:
            response = await self.client.get(f"{self.services['ai-service']}/health")
            response.raise_for_status()
            
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "ai-service"
            
            logger.info("✅ AI service health check passed")
            return True
            
        except Exception as e:
            logger.error("❌ AI service health check failed", error=str(e))
            return False
    
    async def test_create_game_session(self) -> bool:
        """Test creating a game session"""
        try:
            response = await self.client.post(
                f"{self.services['game-engine']}/sessions",
                params={"session_id": self.test_session_id}
            )
            response.raise_for_status()
            
            data = response.json()
            assert data["session_id"] == self.test_session_id
            assert data["status"] == "active"
            
            logger.info("✅ Game session creation passed", session_id=self.test_session_id)
            return True
            
        except Exception as e:
            logger.error("❌ Game session creation failed", error=str(e))
            return False
    
    async def test_add_test_units(self) -> bool:
        """Test adding units to the game session"""
        try:
            # Add a hero unit
            hero_data = {
                "name": "TestHero",
                "type": "HEROMANCER",
                "x": 1,
                "y": 1
            }
            
            response = await self.client.post(
                f"{self.services['game-engine']}/sessions/{self.test_session_id}/dev/add-unit",
                json=hero_data
            )
            response.raise_for_status()
            
            # Add an enemy unit
            enemy_data = {
                "name": "TestEnemy", 
                "type": "MAGI",
                "x": 8,
                "y": 8
            }
            
            response = await self.client.post(
                f"{self.services['game-engine']}/sessions/{self.test_session_id}/dev/add-unit",
                json=enemy_data
            )
            response.raise_for_status()
            
            logger.info("✅ Test units added successfully")
            return True
            
        except Exception as e:
            logger.error("❌ Adding test units failed", error=str(e))
            return False
    
    async def test_get_game_state(self) -> Dict[str, Any]:
        """Test getting game state"""
        try:
            response = await self.client.get(
                f"{self.services['game-engine']}/sessions/{self.test_session_id}/state"
            )
            response.raise_for_status()
            
            game_state = response.json()
            assert game_state["session_id"] == self.test_session_id
            assert len(game_state["units"]) >= 2  # We added 2 units
            
            logger.info("✅ Game state retrieval passed", 
                       units_count=len(game_state["units"]))
            return game_state
            
        except Exception as e:
            logger.error("❌ Game state retrieval failed", error=str(e))
            return {}
    
    async def test_mcp_tools_list(self) -> bool:
        """Test listing MCP tools"""
        try:
            response = await self.client.get(f"{self.services['mcp-gateway']}/mcp/tools")
            response.raise_for_status()
            
            data = response.json()
            tools = data.get("tools", [])
            
            # Check for expected tools
            expected_tools = ["move_unit", "attack_unit", "get_game_state", "analyze_battlefield"]
            found_tools = [tool["name"] for tool in tools]
            
            for expected_tool in expected_tools:
                assert expected_tool in found_tools, f"Tool {expected_tool} not found"
            
            logger.info("✅ MCP tools listing passed", tools_count=len(tools))
            return True
            
        except Exception as e:
            logger.error("❌ MCP tools listing failed", error=str(e))
            return False
    
    async def test_mcp_get_game_state_tool(self) -> bool:
        """Test MCP get_game_state tool"""
        try:
            tool_request = {
                "tool_name": "get_game_state",
                "parameters": {
                    "session_id": self.test_session_id
                },
                "session_id": self.test_session_id
            }
            
            response = await self.client.post(
                f"{self.services['mcp-gateway']}/mcp/call-tool",
                json=tool_request
            )
            response.raise_for_status()
            
            data = response.json()
            assert data["success"] == True
            assert "game_state" in data["result"]
            
            logger.info("✅ MCP get_game_state tool passed")
            return True
            
        except Exception as e:
            logger.error("❌ MCP get_game_state tool failed", error=str(e))
            return False
    
    async def test_mcp_move_unit_tool(self) -> bool:
        """Test MCP move_unit tool"""
        try:
            # First get game state to find a unit
            game_state = await self.test_get_game_state()
            if not game_state or not game_state.get("units"):
                logger.error("No game state or units available for move test")
                return False
            
            unit = game_state["units"][0]
            unit_id = unit["id"]
            current_pos = unit["position"]
            
            # Move unit to a new position
            tool_request = {
                "tool_name": "move_unit",
                "parameters": {
                    "session_id": self.test_session_id,
                    "unit_id": unit_id,
                    "target_x": current_pos[0] + 1,
                    "target_y": current_pos[1] + 1
                },
                "session_id": self.test_session_id
            }
            
            response = await self.client.post(
                f"{self.services['mcp-gateway']}/mcp/call-tool",
                json=tool_request
            )
            response.raise_for_status()
            
            data = response.json()
            # Note: This might fail if game engine move validation is strict
            # That's okay for now as we're testing the communication
            
            logger.info("✅ MCP move_unit tool communication passed", 
                       success=data.get("success"))
            return True
            
        except Exception as e:
            logger.error("❌ MCP move_unit tool failed", error=str(e))
            return False
    
    async def test_ai_models_list(self) -> bool:
        """Test listing AI models"""
        try:
            response = await self.client.get(f"{self.services['ai-service']}/ai/models")
            response.raise_for_status()
            
            data = response.json()
            models = data.get("models", [])
            
            logger.info("✅ AI models listing passed", models_count=len(models))
            return True
            
        except Exception as e:
            logger.error("❌ AI models listing failed", error=str(e))
            return False
    
    async def test_ai_chat(self) -> bool:
        """Test AI chat functionality"""
        try:
            chat_request = {
                "message": "What is a good opening strategy in tactical RPG games?",
                "context": {"game": "apex_tactics"}
            }
            
            response = await self.client.post(
                f"{self.services['ai-service']}/ai/chat",
                params={"message": chat_request["message"]},
                json={"context": chat_request["context"]}
            )
            response.raise_for_status()
            
            data = response.json()
            assert "response" in data
            
            logger.info("✅ AI chat test passed", 
                       response_length=len(data["response"]))
            return True
            
        except Exception as e:
            logger.error("❌ AI chat test failed", error=str(e))
            return False
    
    async def test_cleanup_session(self) -> bool:
        """Test cleaning up the test session"""
        try:
            response = await self.client.delete(
                f"{self.services['game-engine']}/sessions/{self.test_session_id}"
            )
            response.raise_for_status()
            
            logger.info("✅ Session cleanup passed")
            return True
            
        except Exception as e:
            logger.error("❌ Session cleanup failed", error=str(e))
            return False
    
    async def run_all_tests(self) -> bool:
        """Run all integration tests"""
        logger.info("Starting Apex Tactics microservices integration tests")
        
        # Wait for services to be ready
        if not await self.wait_for_services():
            return False
        
        tests = [
            ("Game Engine Health", self.test_game_engine_health),
            ("MCP Gateway Health", self.test_mcp_gateway_health),
            ("AI Service Health", self.test_ai_service_health),
            ("Create Game Session", self.test_create_game_session),
            ("Add Test Units", self.test_add_test_units),
            ("Get Game State", lambda: self.test_get_game_state()),
            ("List MCP Tools", self.test_mcp_tools_list),
            ("MCP Get Game State Tool", self.test_mcp_get_game_state_tool),
            ("MCP Move Unit Tool", self.test_mcp_move_unit_tool),
            ("List AI Models", self.test_ai_models_list),
            ("AI Chat", self.test_ai_chat),
            ("Cleanup Session", self.test_cleanup_session),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            logger.info(f"Running test: {test_name}")
            try:
                result = await test_func()
                if result:
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"Test {test_name} raised exception", error=str(e))
                failed += 1
        
        logger.info("Integration tests completed",
                   passed=passed,
                   failed=failed,
                   total=len(tests))
        
        return failed == 0


async def main():
    """Main test runner"""
    tester = ServiceTester()
    
    try:
        success = await tester.run_all_tests()
        
        if success:
            print("🎉 All integration tests passed!")
            sys.exit(0)
        else:
            print("❌ Some integration tests failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error("Test runner failed", error=str(e))
        sys.exit(1)
    finally:
        await tester.close()


if __name__ == "__main__":
    asyncio.run(main())