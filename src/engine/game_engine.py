"""
Apex Tactics Game Engine

Core game engine implementing the main game loop, state management,
and coordination between all game systems.
"""

import asyncio
import time
import json
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field

import structlog
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from ..core.events import EventBus, GameEvent, EventType
from ..core.ecs import ECSManager, Entity, Component, System, EntityID
from ..core.math import Vector2, GridPosition
from .systems.turn_system import TurnSystem
# from .systems.movement_system import MovementSystem  # TODO: Create this file
from .systems.combat_system import CombatSystem
from .components.position_component import PositionComponent
from .components.stats_component import StatsComponent
from .components.team_component import TeamComponent
from .battlefield import BattlefieldManager
from .game_state import GameStateManager, GamePhase
from .integrations.ai_integration import AIIntegrationManager
from .ui.game_ui_manager import GameUIManager
from .ui.visual_effects import VisualEffectsManager
from .ui.notification_system import NotificationSystem

logger = structlog.get_logger()


class GameMode(str, Enum):
    """Game modes"""
    SINGLE_PLAYER = "single_player"
    MULTIPLAYER = "multiplayer"
    AI_VS_AI = "ai_vs_ai"
    TUTORIAL = "tutorial"


@dataclass
class GameConfig:
    """Game configuration"""
    mode: GameMode = GameMode.SINGLE_PLAYER
    battlefield_size: tuple = (10, 10)
    max_turns: int = 100
    turn_time_limit: float = 30.0
    ai_difficulty: str = "normal"
    enable_fog_of_war: bool = False
    enable_permadeath: bool = True
    victory_conditions: List[str] = field(default_factory=lambda: ["eliminate_all"])


@dataclass
class GameSession:
    """Active game session"""
    session_id: str
    player_ids: List[str]
    config: GameConfig
    start_time: datetime
    current_phase: GamePhase
    turn_number: int = 1
    last_activity: datetime = field(default_factory=datetime.now)


class GameEngine:
    """Main game engine"""
    
    def __init__(self, config: Optional[GameConfig] = None):
        self.config = config or GameConfig()
        
        # Core systems
        self.event_bus = EventBus()
        self.ecs = ECSManager()
        self.battlefield = BattlefieldManager(self.config.battlefield_size)
        self.game_state = GameStateManager()
        
        # Game systems
        self.turn_system = TurnSystem(self.ecs, self.event_bus)
        # self.movement_system = MovementSystem(self.ecs, self.event_bus, self.battlefield)  # TODO: Create this file
        self.combat_system = CombatSystem(self.ecs, self.event_bus)
        self.ai_integration = AIIntegrationManager(
            self.ecs, 
            self.event_bus, 
            self.battlefield, 
            self.game_state
        )
        
        # UI systems
        self.ui_manager = GameUIManager(self.ecs, self.event_bus)
        self.visual_effects = VisualEffectsManager(self.event_bus)
        self.notifications = NotificationSystem(self.event_bus)
        
        # MCP Gateway (optional)
        self.mcp_gateway = None
        
        # Session management
        self.active_sessions: Dict[str, GameSession] = {}
        self.websocket_connections: Dict[str, WebSocket] = {}
        
        # Performance tracking
        self.frame_count = 0
        self.last_frame_time = time.time()
        self.target_fps = 60
        self.frame_time_budget = 1.0 / self.target_fps
        
        # Register systems
        self._register_systems()
        self._setup_event_handlers()
        
        logger.info("Game engine initialized", config=self.config.__dict__)
    
    def _register_systems(self):
        """Register all game systems with ECS"""
        self.ecs.add_system(self.turn_system)
        # self.ecs.add_system(self.movement_system)  # TODO: Create this file
        self.ecs.add_system(self.combat_system)
        # Note: AI integration manager is not an ECS system, it coordinates with systems
        
        logger.info("Game systems registered", system_count=len(self.ecs.system_manager._systems))
    
    def _setup_event_handlers(self):
        """Setup event handlers"""
        self.event_bus.subscribe(EventType.GAME_START, self._handle_game_start)
        self.event_bus.subscribe(EventType.GAME_END, self._handle_game_end)
        self.event_bus.subscribe(EventType.TURN_START, self._handle_turn_start)
        self.event_bus.subscribe(EventType.TURN_END, self._handle_turn_end)
        self.event_bus.subscribe(EventType.UNIT_MOVED, self._handle_unit_moved)
        self.event_bus.subscribe(EventType.UNIT_ATTACKED, self._handle_unit_attacked)
        self.event_bus.subscribe(EventType.UNIT_DIED, self._handle_unit_died)
    
    async def create_session(self, session_id: str, player_ids: List[str], 
                           config: Optional[GameConfig] = None) -> GameSession:
        """Create a new game session"""
        if session_id in self.active_sessions:
            raise ValueError(f"Session {session_id} already exists")
        
        session_config = config or self.config
        session = GameSession(
            session_id=session_id,
            player_ids=player_ids,
            config=session_config,
            start_time=datetime.now(),
            current_phase=GamePhase.SETUP
        )
        
        self.active_sessions[session_id] = session
        
        # Initialize game state for session
        await self.game_state.initialize_session(session_id, session_config)
        
        # Setup battlefield
        await self.battlefield.initialize_for_session(session_id, session_config.battlefield_size)
        
        # Initialize UI systems
        await self.ui_manager.initialize_session(session_id, session_config.battlefield_size)
        
        logger.info("Game session created", 
                   session_id=session_id, 
                   players=len(player_ids))
        
        return session
    
    async def start_game(self, session_id: str) -> bool:
        """Start a game session"""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        
        # Transition to game start
        await self.game_state.set_phase(session_id, GamePhase.ACTIVE)
        session.current_phase = GamePhase.ACTIVE
        
        # Emit game start event
        await self.event_bus.emit(GameEvent(
            type=EventType.GAME_START,
            session_id=session_id,
            data={
                "session": session.__dict__,
                "battlefield_size": session.config.battlefield_size
            }
        ))
        
        # Start main game loop for this session
        asyncio.create_task(self._game_loop(session_id))
        
        logger.info("Game started", session_id=session_id)
        return True
    
    async def _game_loop(self, session_id: str):
        """Main game loop for a session"""
        session = self.active_sessions.get(session_id)
        if not session:
            return
        
        logger.info("Starting game loop", session_id=session_id)
        
        try:
            while session.current_phase == GamePhase.ACTIVE:
                frame_start = time.time()
                
                # Update all systems
                await self._update_systems(session_id)
                
                # Check victory conditions
                if await self._check_victory_conditions(session_id):
                    break
                
                # Check turn limits
                if session.turn_number >= session.config.max_turns:
                    await self._handle_turn_limit_reached(session_id)
                    break
                
                # Frame timing
                frame_time = time.time() - frame_start
                if frame_time < self.frame_time_budget:
                    await asyncio.sleep(self.frame_time_budget - frame_time)
                
                self.frame_count += 1
                
        except Exception as e:
            logger.error("Game loop error", session_id=session_id, error=str(e))
            await self._handle_game_error(session_id, e)
        
        logger.info("Game loop ended", session_id=session_id)
    
    async def _update_systems(self, session_id: str):
        """Update all game systems"""
        # Update ECS systems
        await self.ecs.update(session_id)
        
        # Update battlefield state
        await self.battlefield.update(session_id)
        
        # Update game state
        await self.game_state.update(session_id)
        
        # Calculate delta time for UI updates
        current_time = time.time()
        delta_time = current_time - getattr(self, '_last_ui_update', current_time)
        self._last_ui_update = current_time
        
        # Update UI systems
        await self.ui_manager.update(delta_time)
        await self.visual_effects.update(delta_time)
        await self.notifications.update(delta_time)
    
    async def _check_victory_conditions(self, session_id: str) -> bool:
        """Check if victory conditions are met"""
        session = self.active_sessions.get(session_id)
        if not session:
            return False
        
        for condition in session.config.victory_conditions:
            if await self._evaluate_victory_condition(session_id, condition):
                await self._handle_victory(session_id, condition)
                return True
        
        return False
    
    async def _evaluate_victory_condition(self, session_id: str, condition: str) -> bool:
        """Evaluate a specific victory condition"""
        if condition == "eliminate_all":
            # Check if only one team remains
            teams_alive = await self.battlefield.get_teams_with_living_units(session_id)
            return len(teams_alive) <= 1
        
        elif condition == "capture_objectives":
            # Check if objectives are captured
            return await self.battlefield.check_objective_capture(session_id)
        
        elif condition == "time_limit":
            # Check time limit
            session = self.active_sessions.get(session_id)
            if session:
                elapsed = (datetime.now() - session.start_time).total_seconds()
                return elapsed > 1800  # 30 minutes
        
        return False
    
    async def _handle_victory(self, session_id: str, condition: str):
        """Handle game victory"""
        winning_team = await self.battlefield.get_winning_team(session_id)
        
        await self.event_bus.emit(GameEvent(
            type=EventType.GAME_END,
            session_id=session_id,
            data={
                "victory_condition": condition,
                "winning_team": winning_team,
                "game_duration": (datetime.now() - self.active_sessions[session_id].start_time).total_seconds()
            }
        ))
        
        # Update session state
        session = self.active_sessions[session_id]
        session.current_phase = GamePhase.ENDED
        
        logger.info("Game victory", 
                   session_id=session_id, 
                   winner=winning_team, 
                   condition=condition)
    
    async def _handle_turn_limit_reached(self, session_id: str):
        """Handle turn limit reached"""
        await self.event_bus.emit(GameEvent(
            type=EventType.GAME_END,
            session_id=session_id,
            data={
                "victory_condition": "turn_limit",
                "result": "draw"
            }
        ))
        
        session = self.active_sessions[session_id]
        session.current_phase = GamePhase.ENDED
    
    async def _handle_game_error(self, session_id: str, error: Exception):
        """Handle game errors"""
        logger.error("Game error occurred", session_id=session_id, error=str(error))
        
        session = self.active_sessions.get(session_id)
        if session:
            session.current_phase = GamePhase.ERROR
        
        await self.event_bus.emit(GameEvent(
            type=EventType.GAME_ERROR,
            session_id=session_id,
            data={"error": str(error)}
        ))
    
    # Event handlers
    async def _handle_game_start(self, event: GameEvent):
        """Handle game start event"""
        logger.info("Game start event", session_id=event.session_id)
        
        # Initialize AI integration
        await self.ai_integration.initialize()
        
        # Start first turn
        await self.turn_system.start_turn(event.session_id)
    
    async def _handle_game_end(self, event: GameEvent):
        """Handle game end event"""
        logger.info("Game end event", session_id=event.session_id)
        
        # Broadcast to connected clients
        await self._broadcast_to_session(event.session_id, {
            "type": "game_end",
            "data": event.data
        })
    
    async def _handle_turn_start(self, event: GameEvent):
        """Handle turn start event"""
        session_id = event.session_id
        session = self.active_sessions.get(session_id)
        
        if session:
            session.turn_number = event.data.get("turn_number", session.turn_number)
            session.last_activity = datetime.now()
        
        logger.debug("Turn start", session_id=session_id, turn=session.turn_number if session else None)
    
    async def _handle_turn_end(self, event: GameEvent):
        """Handle turn end event"""
        logger.debug("Turn end", session_id=event.session_id)
        
        # Update session activity
        session = self.active_sessions.get(event.session_id)
        if session:
            session.last_activity = datetime.now()
    
    async def _handle_unit_moved(self, event: GameEvent):
        """Handle unit movement event"""
        await self._broadcast_to_session(event.session_id, {
            "type": "unit_moved",
            "data": event.data
        })
    
    async def _handle_unit_attacked(self, event: GameEvent):
        """Handle unit attack event"""
        await self._broadcast_to_session(event.session_id, {
            "type": "unit_attacked",
            "data": event.data
        })
    
    async def _handle_unit_died(self, event: GameEvent):
        """Handle unit death event"""
        await self._broadcast_to_session(event.session_id, {
            "type": "unit_died",
            "data": event.data
        })
        
        # Check if this death triggers victory
        await self._check_victory_conditions(event.session_id)
    
    # WebSocket management
    async def connect_websocket(self, websocket: WebSocket, session_id: str):
        """Connect WebSocket client to session"""
        await websocket.accept()
        self.websocket_connections[f"{session_id}_{id(websocket)}"] = websocket
        
        logger.info("WebSocket connected", session_id=session_id)
        
        # Send current game state
        game_state = await self.game_state.get_state(session_id)
        await websocket.send_json({
            "type": "game_state",
            "data": game_state
        })
    
    async def disconnect_websocket(self, websocket: WebSocket, session_id: str):
        """Disconnect WebSocket client"""
        connection_key = f"{session_id}_{id(websocket)}"
        if connection_key in self.websocket_connections:
            del self.websocket_connections[connection_key]
        
        logger.info("WebSocket disconnected", session_id=session_id)
    
    async def _broadcast_to_session(self, session_id: str, message: Dict[str, Any]):
        """Broadcast message to all clients in session"""
        disconnected = []
        
        for conn_key, websocket in self.websocket_connections.items():
            if conn_key.startswith(f"{session_id}_"):
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.warning("Failed to send to WebSocket", error=str(e))
                    disconnected.append(conn_key)
        
        # Clean up disconnected websockets
        for conn_key in disconnected:
            del self.websocket_connections[conn_key]
    
    # Public API methods
    async def execute_player_action(self, session_id: str, player_id: str, action: Dict[str, Any]) -> bool:
        """Execute a player action"""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        if player_id not in session.player_ids:
            raise ValueError(f"Player {player_id} not in session")
        
        # Validate action
        if not await self._validate_action(session_id, player_id, action):
            return False
        
        # Execute action through appropriate system
        action_type = action.get("type")
        if action_type == "move":
            return await self.movement_system.execute_move(session_id, action)
        elif action_type == "attack":
            return await self.combat_system.execute_attack(session_id, action)
        elif action_type == "end_turn":
            return await self.turn_system.end_turn(session_id, player_id)
        
        return False
    
    async def _validate_action(self, session_id: str, player_id: str, action: Dict[str, Any]) -> bool:
        """Validate player action"""
        # Check if it's player's turn
        current_player = await self.turn_system.get_current_player(session_id)
        if current_player != player_id:
            return False
        
        # Validate action type
        action_type = action.get("type")
        if action_type not in ["move", "attack", "ability", "end_turn"]:
            return False
        
        # Additional validation per action type
        if action_type == "move":
            return await self.movement_system.validate_move(session_id, action)
        elif action_type == "attack":
            return await self.combat_system.validate_attack(session_id, action)
        
        return True
    
    async def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current session state"""
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        game_state = await self.game_state.get_state(session_id)
        battlefield_state = await self.battlefield.get_state(session_id)
        
        return {
            "session": session.__dict__,
            "game_state": game_state,
            "battlefield": battlefield_state,
            "current_turn": await self.turn_system.get_turn_info(session_id)
        }
    
    async def cleanup_session(self, session_id: str):
        """Clean up a game session"""
        if session_id in self.active_sessions:
            # Cleanup systems
            await self.battlefield.cleanup_session(session_id)
            await self.game_state.cleanup_session(session_id)
            await self.ui_manager.cleanup_session(session_id)
            await self.notifications.cleanup_session(session_id)
            self.turn_system.cleanup_session(session_id)
            
            # Remove session
            del self.active_sessions[session_id]
            
            # Clean up websocket connections
            disconnected = []
            for conn_key in self.websocket_connections.keys():
                if conn_key.startswith(f"{session_id}_"):
                    disconnected.append(conn_key)
            
            for conn_key in disconnected:
                del self.websocket_connections[conn_key]
            
            logger.info("Session cleaned up", session_id=session_id)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get engine performance statistics"""
        current_time = time.time()
        elapsed = current_time - self.last_frame_time
        fps = self.frame_count / elapsed if elapsed > 0 else 0
        
        stats = {
            "fps": fps,
            "frame_count": self.frame_count,
            "active_sessions": len(self.active_sessions),
            "websocket_connections": len(self.websocket_connections),
            "systems_count": len(self.ecs.systems),
            "entities_count": len(self.ecs.entities),
            "uptime_seconds": elapsed
        }
        
        # Add AI integration stats
        try:
            stats["ai_integration"] = self.ai_integration.get_ai_stats()
        except Exception as e:
            logger.warning("Failed to get AI stats", error=str(e))
            stats["ai_integration"] = {"error": "unavailable"}
        
        return stats
    
    # UI-related methods
    async def select_unit(self, session_id: str, entity_id: EntityID, player_id: str) -> bool:
        """Select a unit for a player"""
        if session_id not in self.active_sessions:
            return False
        
        # Validate that the entity exists and belongs to the player
        team_component = self.ecs.get_component(entity_id, TeamComponent)
        if not team_component or team_component.team != player_id:
            return False
        
        # Update UI
        await self.ui_manager.select_unit(session_id, entity_id, player_id)
        
        return True
    
    async def deselect_unit(self, session_id: str, player_id: str) -> bool:
        """Deselect current unit for a player"""
        if session_id not in self.active_sessions:
            return False
        
        await self.ui_manager.deselect_unit(session_id)
        return True
    
    async def highlight_tiles(self, session_id: str, tiles: List[Dict[str, Any]], 
                            highlight_type: str, duration: Optional[float] = None) -> bool:
        """Highlight tiles for visual feedback"""
        if session_id not in self.active_sessions:
            return False
        
        from .ui.game_ui_manager import HighlightType
        try:
            highlight_enum = HighlightType(highlight_type)
            await self.ui_manager.highlight_tiles(session_id, tiles, highlight_enum, duration)
            return True
        except ValueError:
            return False
    
    async def send_notification(self, session_id: str, type: str, title: str, 
                              message: str, player_id: Optional[str] = None) -> bool:
        """Send notification to players"""
        if session_id not in self.active_sessions:
            return False
        
        from .ui.notification_system import NotificationType
        try:
            notification_type = NotificationType(type)
            await self.notifications.send_notification(
                session_id, notification_type, title, message, player_id
            )
            return True
        except ValueError:
            return False
    
    async def set_websocket_callbacks(self, websocket_callback: callable):
        """Set WebSocket callback for UI updates"""
        self.ui_manager.set_websocket_callback(websocket_callback)
        self.notifications.set_websocket_callback(websocket_callback)
    
    async def get_ui_data(self, session_id: str, player_id: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive UI data for a session"""
        if session_id not in self.active_sessions:
            return {}
        
        ui_state = await self.ui_manager.get_session_ui_state(session_id)
        notifications = await self.notifications.get_notifications(session_id, player_id)
        visual_effects = self.visual_effects.get_effect_data_for_ui()
        
        return {
            "ui_state": ui_state,
            "notifications": notifications,
            "visual_effects": visual_effects,
            "session_id": session_id,
            "player_id": player_id
        }
    
    async def enable_mcp_gateway(self, port: int = 8004):
        """Enable MCP Gateway for external tool integration"""
        try:
            from .mcp.gateway_server import GameEngineMCPGateway
            
            self.mcp_gateway = GameEngineMCPGateway(self, port)
            
            # Start MCP server in background task
            asyncio.create_task(self.mcp_gateway.start_server())
            
            logger.info("MCP Gateway enabled", port=port)
            return True
        except ImportError as e:
            logger.warning("MCP Gateway unavailable", error=str(e))
            return False
        except Exception as e:
            logger.error("Failed to enable MCP Gateway", error=str(e))
            return False
    
    async def shutdown(self):
        """Shutdown the game engine"""
        logger.info("Shutting down game engine")
        
        # End all active sessions
        for session_id in list(self.active_sessions.keys()):
            await self.cleanup_session(session_id)
        
        # Shutdown MCP Gateway if enabled
        if self.mcp_gateway:
            logger.info("Shutting down MCP Gateway")
            # MCP Gateway will be shut down with the event loop
        
        # Shutdown systems
        await self.ecs.shutdown()
        await self.ai_integration.shutdown()
        await self.event_bus.shutdown()
        
        logger.info("Game engine shutdown complete")