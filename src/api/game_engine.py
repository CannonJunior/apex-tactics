"""
FastAPI Game Engine API

Main API server for Apex Tactics game engine, providing RESTful endpoints
and WebSocket connections for real-time game state management.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import structlog
import uvicorn

from ..core.game.game_controller import GameController
from ..core.models.unit import Unit
from ..core.models.unit_types import UnitType
from ..core.assets.config_manager import get_config_manager
from .models import (
    GameState, UnitData, MoveAction, AttackAction, 
    GameSession, PlayerAction, GameEvent
)
from .websocket_manager import WebSocketManager

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Global state for active game sessions
active_sessions: Dict[str, GameController] = {}
websocket_manager = WebSocketManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("Starting Apex Tactics Game Engine API")
    
    # Initialize configuration manager
    config_manager = get_config_manager()
    logger.info("Configuration manager initialized", stats=config_manager.get_stats())
    
    # Startup tasks
    yield
    
    # Cleanup tasks
    logger.info("Shutting down Apex Tactics Game Engine API")
    await websocket_manager.disconnect_all()

# Create FastAPI application
app = FastAPI(
    title="Apex Tactics Game Engine API",
    description="RESTful API and WebSocket interface for Apex Tactics tactical RPG",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware for web client support
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration"""
    return {
        "status": "healthy",
        "service": "game-engine",
        "version": "1.0.0",
        "active_sessions": len(active_sessions)
    }

# Game session management endpoints
@app.post("/sessions", response_model=GameSession)
async def create_game_session(session_id: Optional[str] = None) -> GameSession:
    """Create a new game session"""
    if session_id is None:
        import uuid
        session_id = str(uuid.uuid4())
    
    if session_id in active_sessions:
        raise HTTPException(status_code=400, detail="Session already exists")
    
    try:
        # Create new game controller
        game_controller = GameController()
        active_sessions[session_id] = game_controller
        
        logger.info("Created new game session", session_id=session_id)
        
        return GameSession(
            session_id=session_id,
            status="active",
            player_count=0,
            created_at=game_controller.game_start_time
        )
    except Exception as e:
        logger.error("Failed to create game session", session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create game session")

@app.get("/sessions/{session_id}", response_model=GameSession)
async def get_game_session(session_id: str) -> GameSession:
    """Get information about a specific game session"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    game_controller = active_sessions[session_id]
    
    return GameSession(
        session_id=session_id,
        status="active",
        player_count=len([u for u in game_controller.units if u.type in [UnitType.HEROMANCER, UnitType.MAGI]]),
        created_at=game_controller.game_start_time
    )

@app.delete("/sessions/{session_id}")
async def delete_game_session(session_id: str):
    """Delete a game session"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Cleanup session
    del active_sessions[session_id]
    await websocket_manager.disconnect_session(session_id)
    
    logger.info("Deleted game session", session_id=session_id)
    return {"message": "Session deleted successfully"}

# Game state endpoints
@app.get("/sessions/{session_id}/state", response_model=GameState)
async def get_game_state(session_id: str) -> GameState:
    """Get current game state for a session"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    game_controller = active_sessions[session_id]
    
    # Convert units to API format
    units = []
    for unit in game_controller.units:
        unit_data = UnitData(
            id=f"{unit.name}_{unit.x}_{unit.y}",
            name=unit.name,
            unit_type=unit.type.name,
            position=(unit.x, unit.y),
            hp=unit.hp,
            max_hp=unit.max_hp,
            mp=unit.mp,
            max_mp=unit.max_mp,
            ap=unit.ap,
            max_ap=unit.max_ap,
            alive=unit.alive,
            attributes={
                "strength": unit.strength,
                "fortitude": unit.fortitude,
                "finesse": unit.finesse,
                "wisdom": unit.wisdom,
                "wonder": unit.wonder,
                "worthy": unit.worthy,
                "faith": unit.faith,
                "spirit": unit.spirit,
                "speed": unit.speed
            }
        )
        units.append(unit_data)
    
    return GameState(
        session_id=session_id,
        turn_number=game_controller.turn_number,
        current_unit_index=game_controller.current_unit_index,
        units=units,
        game_over=game_controller.game_over,
        winner=getattr(game_controller, 'winner', None)
    )

# Game action endpoints
@app.post("/sessions/{session_id}/actions/move")
async def execute_move_action(session_id: str, action: MoveAction):
    """Execute a move action for a unit"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    game_controller = active_sessions[session_id]
    
    try:
        # Find the unit
        unit = next((u for u in game_controller.units 
                    if f"{u.name}_{u.x}_{u.y}" == action.unit_id), None)
        
        if not unit:
            raise HTTPException(status_code=404, detail="Unit not found")
        
        # Execute move
        success = game_controller.try_move_unit(unit, action.target_x, action.target_y)
        
        if success:
            # Broadcast game state update
            await websocket_manager.broadcast_to_session(
                session_id, 
                GameEvent(type="unit_moved", data=action.dict())
            )
            
            logger.info("Move executed", session_id=session_id, unit_id=action.unit_id, 
                       target=(action.target_x, action.target_y))
            
            return {"success": True, "message": "Move executed successfully"}
        else:
            return {"success": False, "message": "Invalid move"}
            
    except Exception as e:
        logger.error("Failed to execute move", session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to execute move")

@app.post("/sessions/{session_id}/actions/attack")
async def execute_attack_action(session_id: str, action: AttackAction):
    """Execute an attack action"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    game_controller = active_sessions[session_id]
    
    try:
        # Find attacker and target units
        attacker = next((u for u in game_controller.units 
                        if f"{u.name}_{u.x}_{u.y}" == action.attacker_id), None)
        target = next((u for u in game_controller.units 
                      if f"{u.name}_{u.x}_{u.y}" == action.target_id), None)
        
        if not attacker or not target:
            raise HTTPException(status_code=404, detail="Unit not found")
        
        # Execute attack
        success = game_controller.try_attack(attacker, target, action.attack_type)
        
        if success:
            # Broadcast game state update
            await websocket_manager.broadcast_to_session(
                session_id,
                GameEvent(type="unit_attacked", data=action.dict())
            )
            
            logger.info("Attack executed", session_id=session_id, 
                       attacker_id=action.attacker_id, target_id=action.target_id,
                       attack_type=action.attack_type)
            
            return {"success": True, "message": "Attack executed successfully"}
        else:
            return {"success": False, "message": "Invalid attack"}
            
    except Exception as e:
        logger.error("Failed to execute attack", session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to execute attack")

@app.post("/sessions/{session_id}/actions/end-turn")
async def end_turn(session_id: str):
    """End the current unit's turn"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    game_controller = active_sessions[session_id]
    
    try:
        game_controller.end_turn()
        
        # Broadcast turn end event
        await websocket_manager.broadcast_to_session(
            session_id,
            GameEvent(type="turn_ended", data={"turn_number": game_controller.turn_number})
        )
        
        logger.info("Turn ended", session_id=session_id, turn_number=game_controller.turn_number)
        
        return {"success": True, "message": "Turn ended successfully"}
        
    except Exception as e:
        logger.error("Failed to end turn", session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to end turn")

# WebSocket endpoint for real-time updates
@app.websocket("/sessions/{session_id}/ws")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket connection for real-time game updates"""
    if session_id not in active_sessions:
        await websocket.close(code=4004, reason="Session not found")
        return
    
    await websocket_manager.connect(websocket, session_id)
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                if message_type == "ping":
                    await websocket.send_json({"type": "pong"})
                elif message_type == "get_state":
                    # Send current game state
                    game_state = await get_game_state(session_id)
                    await websocket.send_json({
                        "type": "game_state",
                        "data": game_state.dict()
                    })
                
            except json.JSONDecodeError:
                logger.warning("Invalid JSON received on WebSocket", session_id=session_id)
                
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected", session_id=session_id)
    except Exception as e:
        logger.error("WebSocket error", session_id=session_id, error=str(e))
    finally:
        await websocket_manager.disconnect(websocket, session_id)

# Configuration endpoints
@app.get("/config/reload")
async def reload_configuration():
    """Reload game configuration (development only)"""
    try:
        config_manager = get_config_manager()
        config_manager.hot_reload()
        
        logger.info("Configuration reloaded")
        return {"success": True, "message": "Configuration reloaded"}
        
    except Exception as e:
        logger.error("Failed to reload configuration", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to reload configuration")

@app.get("/config/stats")
async def get_configuration_stats():
    """Get configuration manager statistics"""
    config_manager = get_config_manager()
    return config_manager.get_stats()

# Development utilities
@app.post("/sessions/{session_id}/dev/add-unit")
async def dev_add_unit(session_id: str, unit_data: dict):
    """Development endpoint to add units to a session"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    game_controller = active_sessions[session_id]
    
    try:
        unit_type = UnitType[unit_data.get("type", "HEROMANCER")]
        unit = Unit(
            name=unit_data.get("name", "TestUnit"),
            unit_type=unit_type,
            x=unit_data.get("x", 0),
            y=unit_data.get("y", 0)
        )
        
        game_controller.add_unit(unit)
        
        logger.info("Unit added (dev)", session_id=session_id, unit_name=unit.name)
        return {"success": True, "message": f"Unit {unit.name} added"}
        
    except Exception as e:
        logger.error("Failed to add unit (dev)", session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to add unit")

if __name__ == "__main__":
    uvicorn.run(
        "src.api.game_engine:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_config=None  # Use our structured logging
    )