"""
WebSocket Game Client

Handles communication with the headless tactical RPG engine via WebSocket.
Provides async methods for game actions and state synchronization.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from enum import Enum

try:
    import websockets
    try:
        from websockets import WebSocketClientProtocol
    except ImportError:
        # Fallback for newer versions
        WebSocketClientProtocol = Any
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    WebSocketClientProtocol = Any

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """WebSocket connection states"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class GameSession:
    """Game session information"""
    session_id: str
    player_ids: List[str]
    config: Dict[str, Any]
    state: str = "active"


class WebSocketGameClient:
    """
    WebSocket client for communicating with the Apex Tactics game engine.
    
    Provides high-level methods for game actions:
    - Session management (create, join, leave)
    - Player actions (move, attack, select units)
    - State synchronization (game state, UI updates)
    - Real-time event handling (unit moves, attacks, etc.)
    """
    
    def __init__(self, server_url: str):
        """
        Initialize WebSocket client.
        
        Args:
            server_url: WebSocket server URL (e.g., "ws://localhost:8002")
        """
        if not WEBSOCKETS_AVAILABLE:
            raise ImportError("websockets library is required for WebSocket client")
        
        self.server_url = server_url
        self.ws_url = f"{server_url}/ws"
        
        # Connection state
        self.connection_state = ConnectionState.DISCONNECTED
        self.websocket: Optional[WebSocketClientProtocol] = None
        self.session_id: Optional[str] = None
        self.player_id: Optional[str] = None
        
        # Event callbacks
        self._callbacks: Dict[str, Callable] = {}
        
        # Message handling
        self._message_handlers: Dict[str, Callable] = {
            "game_state": self._handle_game_state,
            "ui_data": self._handle_ui_data,
            "action_result": self._handle_action_result,
            "unit_moved": self._handle_unit_moved,
            "unit_attacked": self._handle_unit_attacked,
            "unit_died": self._handle_unit_died,
            "game_end": self._handle_game_end,
            "error": self._handle_error,
            "pong": self._handle_pong,
            "select_unit_result": self._handle_select_unit_result,
            "deselect_unit_result": self._handle_deselect_unit_result,
        }
        
        # Connection monitoring
        self._ping_task: Optional[asyncio.Task] = None
        self._listen_task: Optional[asyncio.Task] = None
        
        logger.info(f"WebSocket client initialized for {server_url}")
    
    def set_callbacks(self, 
                     on_game_state: Optional[Callable] = None,
                     on_ui_data: Optional[Callable] = None,
                     on_unit_moved: Optional[Callable] = None,
                     on_unit_attacked: Optional[Callable] = None,
                     on_unit_died: Optional[Callable] = None,
                     on_game_end: Optional[Callable] = None,
                     on_error: Optional[Callable] = None):
        """Set event callbacks for game events"""
        if on_game_state:
            self._callbacks["game_state"] = on_game_state
        if on_ui_data:
            self._callbacks["ui_data"] = on_ui_data
        if on_unit_moved:
            self._callbacks["unit_moved"] = on_unit_moved
        if on_unit_attacked:
            self._callbacks["unit_attacked"] = on_unit_attacked
        if on_unit_died:
            self._callbacks["unit_died"] = on_unit_died
        if on_game_end:
            self._callbacks["game_end"] = on_game_end
        if on_error:
            self._callbacks["error"] = on_error
    
    async def connect(self, session_id: Optional[str] = None, player_id: Optional[str] = None) -> bool:
        """
        Connect to the WebSocket server.
        
        Args:
            session_id: Optional session ID to join
            player_id: Optional player ID
            
        Returns:
            True if connected successfully
        """
        try:
            self.connection_state = ConnectionState.CONNECTING
            
            # Build WebSocket URL with optional parameters
            ws_url = self.ws_url
            if session_id:
                ws_url += f"/{session_id}"
                self.session_id = session_id
            
            if player_id:
                ws_url += f"?player_id={player_id}"
                self.player_id = player_id
            
            logger.info(f"Connecting to {ws_url}")
            
            # Connect to WebSocket
            self.websocket = await websockets.connect(ws_url)
            self.connection_state = ConnectionState.CONNECTED
            
            # Start background tasks
            self._listen_task = asyncio.create_task(self._listen_for_messages())
            self._ping_task = asyncio.create_task(self._ping_loop())
            
            logger.info("WebSocket connected successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            self.connection_state = ConnectionState.ERROR
            return False
    
    async def disconnect(self):
        """Disconnect from the WebSocket server"""
        logger.info("Disconnecting from WebSocket server")
        
        # Cancel background tasks
        if self._ping_task:
            self._ping_task.cancel()
        if self._listen_task:
            self._listen_task.cancel()
        
        # Close WebSocket connection
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        
        self.connection_state = ConnectionState.DISCONNECTED
        self.session_id = None
        self.player_id = None
    
    async def _listen_for_messages(self):
        """Listen for incoming WebSocket messages"""
        try:
            while self.websocket:
                # Check if connection is still open
                if hasattr(self.websocket, 'closed') and self.websocket.closed:
                    break
                
                message = await self.websocket.recv()
                await self._handle_message(message)
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket connection closed")
            self.connection_state = ConnectionState.DISCONNECTED
        except Exception as e:
            logger.error(f"Error listening for messages: {e}")
            self.connection_state = ConnectionState.ERROR
    
    async def _ping_loop(self):
        """Send periodic ping messages to keep connection alive"""
        try:
            while self.websocket:
                await asyncio.sleep(30)  # Ping every 30 seconds
                
                # Check if connection is still open
                if self.websocket and (not hasattr(self.websocket, 'closed') or not self.websocket.closed):
                    await self.send_message({"type": "ping"})
                else:
                    break
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in ping loop: {e}")
    
    async def send_message(self, message: Dict[str, Any]):
        """Send a message to the server"""
        if not self.websocket:
            logger.error("Cannot send message: WebSocket not connected")
            return False
        
        # Check if websocket has closed attribute and is closed
        if hasattr(self.websocket, 'closed') and self.websocket.closed:
            logger.error("Cannot send message: WebSocket connection closed")
            return False
        
        try:
            message_json = json.dumps(message)
            await self.websocket.send(message_json)
            logger.debug(f"Sent message: {message.get('type', 'unknown')}")
            return True
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    async def _handle_message(self, message: str):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type in self._message_handlers:
                await self._message_handlers[message_type](data)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode message: {e}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    # Message handlers
    async def _handle_game_state(self, data: Dict[str, Any]):
        """Handle game state update"""
        game_state = data.get("data")
        if game_state and "game_state" in self._callbacks:
            self._callbacks["game_state"](game_state)
    
    async def _handle_ui_data(self, data: Dict[str, Any]):
        """Handle UI data update"""
        ui_data = data.get("data")
        if ui_data and "ui_data" in self._callbacks:
            self._callbacks["ui_data"](ui_data)
    
    async def _handle_action_result(self, data: Dict[str, Any]):
        """Handle action result"""
        result = data.get("data")
        logger.info(f"Action result: {result}")
    
    async def _handle_unit_moved(self, data: Dict[str, Any]):
        """Handle unit movement event"""
        move_data = data.get("data")
        if move_data and "unit_moved" in self._callbacks:
            self._callbacks["unit_moved"](move_data)
    
    async def _handle_unit_attacked(self, data: Dict[str, Any]):
        """Handle unit attack event"""
        attack_data = data.get("data")
        if attack_data and "unit_attacked" in self._callbacks:
            self._callbacks["unit_attacked"](attack_data)
    
    async def _handle_unit_died(self, data: Dict[str, Any]):
        """Handle unit death event"""
        death_data = data.get("data")
        if death_data and "unit_died" in self._callbacks:
            self._callbacks["unit_died"](death_data)
    
    async def _handle_game_end(self, data: Dict[str, Any]):
        """Handle game end event"""
        end_data = data.get("data")
        if end_data and "game_end" in self._callbacks:
            self._callbacks["game_end"](end_data)
    
    async def _handle_error(self, data: Dict[str, Any]):
        """Handle error message"""
        error_msg = data.get("data", {}).get("message", "Unknown error")
        logger.error(f"Server error: {error_msg}")
        if "error" in self._callbacks:
            self._callbacks["error"](error_msg)
    
    async def _handle_pong(self, data: Dict[str, Any]):
        """Handle pong response"""
        logger.debug("Received pong from server")
    
    async def _handle_select_unit_result(self, data: Dict[str, Any]):
        """Handle unit selection result"""
        result = data.get("data")
        logger.info(f"Unit selection result: {result}")
    
    async def _handle_deselect_unit_result(self, data: Dict[str, Any]):
        """Handle unit deselection result"""
        result = data.get("data")
        logger.info(f"Unit deselection result: {result}")
    
    # Game action methods
    async def create_session(self, session_id: str, player_ids: List[str], 
                           config: Optional[Dict[str, Any]] = None) -> bool:
        """Create a new game session"""
        session_data = {
            "session_id": session_id,
            "player_ids": player_ids,
            "config": config or {}
        }
        
        # Use HTTP API for session creation
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                url = f"{self.server_url.replace('ws://', 'http://')}/api/sessions"
                async with session.post(url, json=session_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Session created: {result}")
                        return True
                    else:
                        logger.error(f"Failed to create session: {response.status}")
                        return False
        except ImportError:
            logger.warning("aiohttp not available, using WebSocket for session creation")
            # Fallback: try via WebSocket (if server supports it)
            return False
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return False
    
    async def start_session(self, session_id: str) -> bool:
        """Start a game session"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                url = f"{self.server_url.replace('ws://', 'http://')}/api/sessions/{session_id}/start"
                async with session.post(url) as response:
                    if response.status == 200:
                        logger.info(f"Session started: {session_id}")
                        return True
                    else:
                        logger.error(f"Failed to start session: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Error starting session: {e}")
            return False
    
    async def send_player_action(self, session_id: str, player_id: str, action: Dict[str, Any]) -> bool:
        """Send a player action to the server"""
        message = {
            "type": "player_action",
            "data": action
        }
        return await self.send_message(message)
    
    async def select_unit(self, session_id: str, player_id: str, unit_id: str) -> bool:
        """Select a unit"""
        message = {
            "type": "select_unit",
            "data": {"unit_id": unit_id}
        }
        return await self.send_message(message)
    
    async def deselect_unit(self, session_id: str, player_id: str) -> bool:
        """Deselect current unit"""
        message = {
            "type": "deselect_unit",
            "data": {}
        }
        return await self.send_message(message)
    
    async def request_game_state(self) -> bool:
        """Request current game state"""
        message = {
            "type": "request_game_state",
            "data": {}
        }
        return await self.send_message(message)
    
    async def request_ui_data(self, player_id: Optional[str] = None) -> bool:
        """Request UI data"""
        message = {
            "type": "request_ui_data",
            "data": {"player_id": player_id or self.player_id}
        }
        return await self.send_message(message)
    
    async def dismiss_notification(self, notification_id: str) -> bool:
        """Dismiss a notification"""
        message = {
            "type": "dismiss_notification",
            "data": {"notification_id": notification_id}
        }
        return await self.send_message(message)
    
    # Utility methods
    def is_connected(self) -> bool:
        """Check if connected to server"""
        return (self.connection_state == ConnectionState.CONNECTED and 
                self.websocket and not self.websocket.closed)
    
    def get_connection_state(self) -> ConnectionState:
        """Get current connection state"""
        return self.connection_state
    
    def get_session_info(self) -> Optional[Dict[str, str]]:
        """Get current session information"""
        if self.session_id and self.player_id:
            return {
                "session_id": self.session_id,
                "player_id": self.player_id,
                "server_url": self.server_url
            }
        return None