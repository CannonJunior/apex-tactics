#!/usr/bin/env python3
"""
Apex Tactics Game Engine Launcher

Starts the game engine with WebSocket support and AI integration.
"""

import sys
import asyncio
import argparse
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import structlog
import uvicorn

from src.engine.game_engine import GameEngine, GameConfig, GameMode
from src.engine.integrations.websocket_handler import create_websocket_app

# Configure structured logging
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

logger = structlog.get_logger()


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Apex Tactics Game Engine")
    
    # Server configuration
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8002, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--log-level", default="info", choices=["debug", "info", "warning", "error"])
    
    # Game configuration
    parser.add_argument("--mode", default="single_player", 
                       choices=["single_player", "multiplayer", "ai_vs_ai", "tutorial"],
                       help="Default game mode")
    parser.add_argument("--battlefield-width", type=int, default=10, help="Battlefield width")
    parser.add_argument("--battlefield-height", type=int, default=10, help="Battlefield height")
    parser.add_argument("--max-turns", type=int, default=100, help="Maximum turns per game")
    parser.add_argument("--turn-time-limit", type=float, default=30.0, help="Turn time limit in seconds")
    parser.add_argument("--ai-difficulty", default="normal", 
                       choices=["easy", "normal", "hard", "expert"],
                       help="AI difficulty level")
    
    # AI service configuration
    parser.add_argument("--ai-service-url", default="ws://localhost:8003/ws",
                       help="AI service WebSocket URL")
    
    return parser.parse_args()


def create_game_config(args) -> GameConfig:
    """Create game configuration from command line arguments"""
    return GameConfig(
        mode=GameMode(args.mode),
        battlefield_size=(args.battlefield_width, args.battlefield_height),
        max_turns=args.max_turns,
        turn_time_limit=args.turn_time_limit,
        ai_difficulty=args.ai_difficulty,
        enable_fog_of_war=False,  # Can be added as argument if needed
        enable_permadeath=True,   # Can be added as argument if needed
        victory_conditions=["eliminate_all"]  # Can be made configurable
    )


async def health_check():
    """Basic health check for the engine"""
    try:
        # Create a test game engine
        config = GameConfig()
        engine = GameEngine(config)
        
        # Test basic functionality
        test_session_id = "health_check"
        session = await engine.create_session(test_session_id, ["player1"])
        
        # Clean up
        await engine.cleanup_session(test_session_id)
        await engine.shutdown()
        
        logger.info("Health check passed")
        return True
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return False


def main():
    """Main entry point"""
    args = parse_args()
    
    logger.info("Starting Apex Tactics Game Engine", 
               host=args.host, 
               port=args.port,
               ai_service_url=args.ai_service_url)
    
    # Create game configuration
    config = create_game_config(args)
    logger.info("Game configuration", config=config.__dict__)
    
    # Create game engine
    try:
        engine = GameEngine(config)
        logger.info("Game engine created successfully")
        
        # Create FastAPI application with WebSocket support
        app = create_websocket_app(engine)
        logger.info("WebSocket application created")
        
        # Run the server
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            log_level=args.log_level,
            reload=args.reload,
            access_log=True
        )
        
    except Exception as e:
        logger.error("Failed to start game engine", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()