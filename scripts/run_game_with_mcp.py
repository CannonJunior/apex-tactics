#!/usr/bin/env python3
"""
Integrated Game Server with MCP Gateway

Runs the full game server with WebSocket support and MCP Gateway
for comprehensive external tool integration.
"""

import asyncio
import sys
import argparse
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.engine.game_engine import GameEngine, GameConfig, GameMode
from src.engine.integrations.websocket_handler import create_websocket_app
import structlog
import uvicorn

logger = structlog.get_logger()


async def main():
    """Main entry point for integrated game server"""
    parser = argparse.ArgumentParser(description="Apex Tactics Game Server with MCP Gateway")
    parser.add_argument("--websocket-port", type=int, default=8002,
                       help="Port for WebSocket game server (default: 8002)")
    parser.add_argument("--mcp-port", type=int, default=8004,
                       help="Port for MCP Gateway server (default: 8004)")
    parser.add_argument("--disable-mcp", action="store_true",
                       help="Disable MCP Gateway")
    parser.add_argument("--log-level", default="INFO",
                       choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       help="Log level (default: INFO)")
    parser.add_argument("--mode", default="single_player",
                       choices=["single_player", "multiplayer", "ai_vs_ai", "tutorial"],
                       help="Default game mode (default: single_player)")
    
    args = parser.parse_args()
    
    # Configure logging
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Create game engine
    config = GameConfig(
        mode=GameMode(args.mode),
        battlefield_size=(10, 10),
        max_turns=100,
        turn_time_limit=30.0,
        ai_difficulty="normal"
    )
    
    logger.info("Initializing game engine", config=config.__dict__)
    engine = GameEngine(config)
    
    # Enable MCP Gateway if not disabled
    if not args.disable_mcp:
        logger.info("Enabling MCP Gateway", port=args.mcp_port)
        mcp_enabled = await engine.enable_mcp_gateway(args.mcp_port)
        if mcp_enabled:
            logger.info("MCP Gateway enabled successfully")
        else:
            logger.warning("MCP Gateway could not be enabled")
    else:
        logger.info("MCP Gateway disabled by user")
    
    # Create WebSocket app
    logger.info("Creating WebSocket application")
    app = create_websocket_app(engine)
    
    # Add startup/shutdown handlers
    @app.on_event("startup")
    async def startup_event():
        """Handle application startup"""
        logger.info("Game server starting up", 
                   websocket_port=args.websocket_port,
                   mcp_port=args.mcp_port if not args.disable_mcp else None)
        await engine.event_bus.start_processing()
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Handle application shutdown"""
        logger.info("Game server shutting down")
        await engine.shutdown()
    
    # Add health check endpoint
    @app.get("/api/health")
    async def health_check():
        """Comprehensive health check"""
        return {
            "status": "healthy",
            "services": {
                "game_engine": "running",
                "websocket": "running",
                "mcp_gateway": "running" if engine.mcp_gateway else "disabled"
            },
            "performance": engine.get_performance_stats(),
            "active_sessions": len(engine.active_sessions)
        }
    
    # Add MCP tools list endpoint
    if not args.disable_mcp:
        @app.get("/api/mcp/tools")
        async def list_mcp_tools():
            """List available MCP tools"""
            if engine.mcp_gateway:
                return {
                    "tools": [
                        {"name": "get_game_sessions", "description": "Get list of all active game sessions"},
                        {"name": "get_session_state", "description": "Get detailed state for a specific game session"},
                        {"name": "get_battlefield_state", "description": "Get battlefield information for a session"},
                        {"name": "get_all_units", "description": "Get information about all units in a session"},
                        {"name": "get_unit_details", "description": "Get detailed information about a specific unit"},
                        {"name": "get_available_actions", "description": "Get available actions for a specific unit"},
                        {"name": "execute_unit_action", "description": "Execute an action for a unit"},
                        {"name": "get_turn_info", "description": "Get current turn information for a session"},
                        {"name": "analyze_tactical_situation", "description": "Analyze the current tactical situation"},
                        {"name": "get_game_statistics", "description": "Get comprehensive game statistics"},
                        {"name": "send_notification", "description": "Send a notification to players"},
                        {"name": "highlight_tiles", "description": "Highlight tiles on the battlefield"},
                        {"name": "create_test_session", "description": "Create a test game session"}
                    ]
                }
            else:
                return {"error": "MCP Gateway not enabled"}
    
    # Run server
    logger.info("Starting game server", port=args.websocket_port)
    
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=args.websocket_port,
        log_level=args.log_level.lower(),
        reload=False
    )
    
    server = uvicorn.Server(config)
    
    try:
        await server.serve()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error("Server error", error=str(e))
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))