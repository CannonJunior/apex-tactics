#!/usr/bin/env python3
"""
MCP Gateway Launcher

Standalone launcher for the MCP Gateway server, allowing external
MCP tools to interact with the Apex Tactics game engine.
"""

import asyncio
import sys
import os
import argparse
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.engine.game_engine import GameEngine, GameConfig, GameMode
from src.engine.mcp.gateway_server import GameEngineMCPGateway
import structlog

logger = structlog.get_logger()


async def main():
    """Main entry point for MCP Gateway launcher"""
    parser = argparse.ArgumentParser(description="Apex Tactics MCP Gateway Server")
    parser.add_argument("--port", type=int, default=8004, 
                       help="Port for MCP Gateway server (default: 8004)")
    parser.add_argument("--http", action="store_true",
                       help="Run HTTP server for testing instead of stdio")
    parser.add_argument("--log-level", default="INFO",
                       choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       help="Log level (default: INFO)")
    parser.add_argument("--create-test-session", action="store_true",
                       help="Create a test session on startup")
    
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
        mode=GameMode.TUTORIAL,
        battlefield_size=(10, 10),
        max_turns=50,
        turn_time_limit=60.0,
        ai_difficulty="normal"
    )
    
    logger.info("Initializing game engine", config=config.__dict__)
    engine = GameEngine(config)
    
    # Create MCP Gateway
    logger.info("Creating MCP Gateway", port=args.port)
    gateway = GameEngineMCPGateway(engine, args.port)
    
    # Create test session if requested
    if args.create_test_session:
        logger.info("Creating test session")
        try:
            test_session = await gateway.create_test_session(
                battlefield_size=[10, 10],
                player_count=2
            )
            logger.info("Test session created", session_data=test_session)
        except Exception as e:
            logger.error("Failed to create test session", error=str(e))
    
    try:
        if args.http:
            logger.info("Starting MCP Gateway HTTP server for testing")
            await gateway.run_server_http()
        else:
            logger.info("Starting MCP Gateway stdio server")
            await gateway.start_server()
    
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error("Gateway server error", error=str(e))
        return 1
    finally:
        logger.info("Shutting down game engine")
        await engine.shutdown()
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))