"""
WebSocket Handler for Game Engine

Handles WebSocket connections for real-time communication
between clients and the game engine.
"""

import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

import structlog
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from ...core.events import EventBus, GameEvent, EventType
from ..game_engine import GameEngine, GameConfig, GameMode

logger = structlog.get_logger()


class WebSocketManager:
    """Manages WebSocket connections for game sessions"""
    
    def __init__(self, game_engine: GameEngine):
        self.game_engine = game_engine
        self.connections: Dict[str, List[WebSocket]] = {}  # session_id -> list of websockets
        self.connection_info: Dict[str, Dict[str, Any]] = {}  # connection_id -> info
        
    async def connect(self, websocket: WebSocket, session_id: str, player_id: str = None):
        """Accept WebSocket connection"""
        await websocket.accept()
        
        connection_id = f"{session_id}_{id(websocket)}"
        
        # Add to connections
        if session_id not in self.connections:
            self.connections[session_id] = []
        self.connections[session_id].append(websocket)
        
        # Store connection info
        self.connection_info[connection_id] = {
            "session_id": session_id,
            "player_id": player_id,
            "connected_at": datetime.now(),
            "websocket": websocket
        }
        
        logger.info("WebSocket connected", 
                   session_id=session_id, 
                   player_id=player_id,
                   connection_id=connection_id)
        
        # Send initial game state and UI data
        try:
            game_state = await self.game_engine.get_session_state(session_id)
            if game_state:
                await websocket.send_json({
                    "type": "game_state",
                    "data": game_state
                })
            
            # Send initial UI data
            ui_data = await self.game_engine.get_ui_data(session_id, player_id)
            if ui_data:
                await websocket.send_json({
                    "type": "ui_data",
                    "data": ui_data
                })
        except Exception as e:
            logger.error("Failed to send initial game state", 
                        session_id=session_id, 
                        error=str(e))
    
    async def disconnect(self, websocket: WebSocket, session_id: str):
        """Handle WebSocket disconnect"""
        connection_id = f"{session_id}_{id(websocket)}"
        
        # Remove from connections
        if session_id in self.connections:
            if websocket in self.connections[session_id]:
                self.connections[session_id].remove(websocket)
            
            # Clean up empty session lists
            if not self.connections[session_id]:
                del self.connections[session_id]
        
        # Remove connection info
        self.connection_info.pop(connection_id, None)
        
        logger.info("WebSocket disconnected", 
                   session_id=session_id,
                   connection_id=connection_id)
    
    async def send_to_session(self, session_id: str, message: Dict[str, Any]):
        """Send message to all connections in a session"""
        if session_id not in self.connections:
            return
        
        disconnected = []
        for websocket in self.connections[session_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.warning("Failed to send message to websocket", 
                             session_id=session_id, 
                             error=str(e))
                disconnected.append(websocket)
        
        # Clean up disconnected websockets
        for websocket in disconnected:
            await self.disconnect(websocket, session_id)
    
    async def send_to_player(self, session_id: str, player_id: str, message: Dict[str, Any]):
        """Send message to specific player in session"""
        for conn_id, info in self.connection_info.items():
            if (info["session_id"] == session_id and 
                info["player_id"] == player_id):
                try:
                    await info["websocket"].send_json(message)
                except Exception as e:
                    logger.warning("Failed to send message to player", 
                                 session_id=session_id,
                                 player_id=player_id,
                                 error=str(e))
    
    async def handle_message(self, websocket: WebSocket, session_id: str, 
                           player_id: str, message_data: Dict[str, Any]):
        """Handle incoming WebSocket message"""
        message_type = message_data.get("type")
        data = message_data.get("data", {})
        
        logger.debug("Received WebSocket message", 
                    session_id=session_id,
                    player_id=player_id,
                    type=message_type)
        
        try:
            if message_type == "player_action":
                await self._handle_player_action(session_id, player_id, data)
            elif message_type == "request_game_state":
                await self._handle_game_state_request(websocket, session_id)
            elif message_type == "request_ui_data":
                await self._handle_ui_data_request(websocket, session_id, player_id)
            elif message_type == "select_unit":
                await self._handle_select_unit(session_id, player_id, data)
            elif message_type == "deselect_unit":
                await self._handle_deselect_unit(session_id, player_id)
            elif message_type == "dismiss_notification":
                await self._handle_dismiss_notification(session_id, player_id, data)
            elif message_type == "ping":
                await self._handle_ping(websocket)
            else:
                logger.warning("Unknown message type", type=message_type)
                
        except Exception as e:
            logger.error("Error handling WebSocket message", 
                        session_id=session_id,
                        player_id=player_id,
                        type=message_type,
                        error=str(e))
            
            # Send error response
            await websocket.send_json({
                "type": "error",
                "data": {
                    "message": str(e),
                    "original_type": message_type
                }
            })
    
    async def _handle_player_action(self, session_id: str, player_id: str, action_data: Dict[str, Any]):
        """Handle player action"""
        success = await self.game_engine.execute_player_action(session_id, player_id, action_data)
        
        # Send response to player
        await self.send_to_player(session_id, player_id, {
            "type": "action_result",
            "data": {
                "action": action_data,
                "success": success,
                "timestamp": datetime.now().isoformat()
            }
        })
    
    async def _handle_game_state_request(self, websocket: WebSocket, session_id: str):
        """Handle game state request"""
        game_state = await self.game_engine.get_session_state(session_id)
        await websocket.send_json({
            "type": "game_state",
            "data": game_state
        })
    
    async def _handle_ping(self, websocket: WebSocket):
        """Handle ping message"""
        await websocket.send_json({
            "type": "pong",
            "timestamp": datetime.now().isoformat()
        })
    
    async def _handle_ui_data_request(self, websocket: WebSocket, session_id: str, player_id: str):
        """Handle UI data request"""
        ui_data = await self.game_engine.get_ui_data(session_id, player_id)
        await websocket.send_json({
            "type": "ui_data",
            "data": ui_data
        })
    
    async def _handle_select_unit(self, session_id: str, player_id: str, data: Dict[str, Any]):
        """Handle unit selection"""
        unit_id = data.get("unit_id")
        if unit_id:
            from ...core.ecs import EntityID
            success = await self.game_engine.select_unit(session_id, EntityID(unit_id), player_id)
            
            # Send response to player
            await self.send_to_player(session_id, player_id, {
                "type": "select_unit_result",
                "data": {
                    "unit_id": unit_id,
                    "success": success
                }
            })
    
    async def _handle_deselect_unit(self, session_id: str, player_id: str):
        """Handle unit deselection"""
        success = await self.game_engine.deselect_unit(session_id, player_id)
        
        # Send response to player
        await self.send_to_player(session_id, player_id, {
            "type": "deselect_unit_result",
            "data": {
                "success": success
            }
        })
    
    async def _handle_dismiss_notification(self, session_id: str, player_id: str, data: Dict[str, Any]):
        """Handle notification dismissal"""
        notification_id = data.get("notification_id")
        if notification_id:
            success = await self.game_engine.notifications.dismiss_notification(
                session_id, notification_id, player_id
            )
            
            # Send response to player
            await self.send_to_player(session_id, player_id, {
                "type": "dismiss_notification_result",
                "data": {
                    "notification_id": notification_id,
                    "success": success
                }
            })
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        total_connections = sum(len(conns) for conns in self.connections.values())
        sessions_with_connections = len(self.connections)
        
        return {
            "total_connections": total_connections,
            "active_sessions": sessions_with_connections,
            "connections_by_session": {
                session_id: len(conns) 
                for session_id, conns in self.connections.items()
            }
        }


def create_websocket_app(game_engine: GameEngine) -> FastAPI:
    """Create FastAPI application with WebSocket support"""
    app = FastAPI(title="Apex Tactics Game Engine", version="1.0.0")
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # WebSocket manager
    ws_manager = WebSocketManager(game_engine)
    
    # Set up WebSocket callbacks for UI updates
    async def websocket_callback(session_id: str, message: Dict[str, Any], player_id: str = None):
        """Callback for sending UI updates via WebSocket"""
        if player_id:
            await ws_manager.send_to_player(session_id, player_id, message)
        else:
            await ws_manager.send_to_session(session_id, message)
    
    # TODO: Configure game engine with WebSocket callback in startup event
    # await game_engine.set_websocket_callbacks(websocket_callback)
    
    @app.websocket("/ws/{session_id}")
    async def websocket_endpoint(websocket: WebSocket, session_id: str, player_id: str = None):
        """WebSocket endpoint for game sessions"""
        await ws_manager.connect(websocket, session_id, player_id)
        
        try:
            while True:
                # Receive message
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Handle message
                await ws_manager.handle_message(websocket, session_id, player_id, message_data)
                
        except WebSocketDisconnect:
            logger.info("WebSocket disconnected normally", session_id=session_id)
        except Exception as e:
            logger.error("WebSocket error", session_id=session_id, error=str(e))
        finally:
            await ws_manager.disconnect(websocket, session_id)
    
    # HTTP API endpoints
    @app.post("/api/sessions")
    async def create_session(session_request: Dict[str, Any]):
        """Create a new game session"""
        session_id = session_request.get("session_id")
        player_ids = session_request.get("player_ids", [])
        config_data = session_request.get("config", {})
        
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required")
        
        # Create game config
        config = GameConfig(
            mode=GameMode(config_data.get("mode", "single_player")),
            battlefield_size=tuple(config_data.get("battlefield_size", [10, 10])),
            max_turns=config_data.get("max_turns", 100),
            turn_time_limit=config_data.get("turn_time_limit", 30.0),
            ai_difficulty=config_data.get("ai_difficulty", "normal"),
            enable_fog_of_war=config_data.get("enable_fog_of_war", False),
            enable_permadeath=config_data.get("enable_permadeath", True),
            victory_conditions=config_data.get("victory_conditions", ["eliminate_all"])
        )
        
        try:
            session = await game_engine.create_session(session_id, player_ids, config)
            return {"status": "success", "session": session.__dict__}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.post("/api/sessions/{session_id}/start")
    async def start_session(session_id: str):
        """Start a game session"""
        try:
            success = await game_engine.start_game(session_id)
            return {"status": "success" if success else "failed"}
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
    
    @app.get("/api/sessions/{session_id}")
    async def get_session(session_id: str):
        """Get session state"""
        session_state = await game_engine.get_session_state(session_id)
        if not session_state:
            raise HTTPException(status_code=404, detail="Session not found")
        return session_state
    
    @app.delete("/api/sessions/{session_id}")
    async def cleanup_session(session_id: str):
        """Clean up session"""
        await game_engine.cleanup_session(session_id)
        return {"status": "success"}
    
    @app.get("/api/sessions/{session_id}/ui")
    async def get_ui_data(session_id: str, player_id: str = None):
        """Get UI data for session"""
        ui_data = await game_engine.get_ui_data(session_id, player_id)
        if not ui_data:
            raise HTTPException(status_code=404, detail="Session not found")
        return ui_data
    
    @app.post("/api/sessions/{session_id}/select_unit")
    async def select_unit_api(session_id: str, request: Dict[str, Any]):
        """Select unit via API"""
        unit_id = request.get("unit_id")
        player_id = request.get("player_id")
        
        if not unit_id or not player_id:
            raise HTTPException(status_code=400, detail="unit_id and player_id required")
        
        from ...core.ecs import EntityID
        success = await game_engine.select_unit(session_id, EntityID(unit_id), player_id)
        return {"success": success}
    
    @app.post("/api/sessions/{session_id}/notifications")
    async def send_notification_api(session_id: str, request: Dict[str, Any]):
        """Send notification via API"""
        type = request.get("type", "info")
        title = request.get("title", "")
        message = request.get("message", "")
        player_id = request.get("player_id")
        
        success = await game_engine.send_notification(session_id, type, title, message, player_id)
        return {"success": success}
    
    @app.get("/api/status")
    async def get_status():
        """Get engine status"""
        return {
            "status": "running",
            "performance": game_engine.get_performance_stats(),
            "websockets": ws_manager.get_connection_stats(),
            "ui_stats": {
                "ui_manager": game_engine.ui_manager.get_ui_stats(),
                "visual_effects": game_engine.visual_effects.get_stats(),
                "notifications": game_engine.notifications.get_stats()
            }
        }
    
    @app.on_event("startup")
    async def startup_event():
        """Handle application startup"""
        logger.info("Game engine WebSocket server starting up")
        await game_engine.event_bus.start_processing()
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Handle application shutdown"""
        logger.info("Game engine WebSocket server shutting down")
        await game_engine.shutdown()
    
    return app


# CLI entry point for running the server
if __name__ == "__main__":
    import uvicorn
    
    # Create game engine with default config
    engine = GameEngine()
    
    # Create FastAPI app
    app = create_websocket_app(engine)
    
    # Run server
    logger.info("Starting Apex Tactics Game Engine server")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,
        log_level="info",
        reload=False
    )