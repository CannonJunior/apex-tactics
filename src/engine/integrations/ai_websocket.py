"""
AI WebSocket Integration

Provides WebSocket communication between the game engine and AI service
for real-time AI decision making during tactical gameplay.
"""

import asyncio
import json
import uuid
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from enum import Enum

import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException
import structlog

from ...core.events import EventBus, GameEvent, EventType

logger = structlog.get_logger()


class AIMessageType(str, Enum):
    """AI WebSocket message types"""
    # Engine to AI
    REQUEST_DECISION = "request_decision"
    GAME_STATE_UPDATE = "game_state_update"
    UNIT_SPAWN = "unit_spawn"
    UNIT_DEATH = "unit_death"
    BATTLE_START = "battle_start"
    BATTLE_END = "battle_end"
    
    # AI to Engine
    DECISION_RESPONSE = "decision_response"
    AI_READY = "ai_ready"
    AI_ERROR = "ai_error"
    AI_STATUS = "ai_status"
    
    # Bidirectional
    PING = "ping"
    PONG = "pong"
    HEARTBEAT = "heartbeat"


class AIWebSocketClient:
    """WebSocket client for AI service communication"""
    
    def __init__(self, ai_service_url: str, event_bus: EventBus):
        self.ai_service_url = ai_service_url
        self.event_bus = event_bus
        
        # Connection state
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.is_connected = False
        self.connection_task: Optional[asyncio.Task] = None
        self.heartbeat_task: Optional[asyncio.Task] = None
        
        # Message handling
        self.pending_requests: Dict[str, Dict[str, Any]] = {}
        self.message_handlers: Dict[AIMessageType, Callable] = {}
        self.request_timeout = 30.0  # 30 seconds
        
        # Connection settings
        self.reconnect_delay = 5.0
        self.max_reconnect_attempts = 5
        self.reconnect_attempts = 0
        self.heartbeat_interval = 10.0
        
        self._setup_message_handlers()
        logger.info("AI WebSocket client initialized", url=ai_service_url)
    
    def _setup_message_handlers(self):
        """Setup message type handlers"""
        self.message_handlers = {
            AIMessageType.DECISION_RESPONSE: self._handle_decision_response,
            AIMessageType.AI_READY: self._handle_ai_ready,
            AIMessageType.AI_ERROR: self._handle_ai_error,
            AIMessageType.AI_STATUS: self._handle_ai_status,
            AIMessageType.PONG: self._handle_pong,
            AIMessageType.HEARTBEAT: self._handle_heartbeat
        }
    
    async def connect(self) -> bool:
        """Connect to AI service"""
        if self.is_connected:
            return True
        
        try:
            logger.info("Connecting to AI service", url=self.ai_service_url)
            
            self.websocket = await websockets.connect(
                self.ai_service_url,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10
            )
            
            self.is_connected = True
            self.reconnect_attempts = 0
            
            # Start message handling and heartbeat
            self.connection_task = asyncio.create_task(self._handle_messages())
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            
            logger.info("Connected to AI service successfully")
            
            # Notify event bus
            await self.event_bus.emit(GameEvent(
                type=EventType.AI_ANALYSIS_COMPLETE,
                session_id="system",
                data={"event": "ai_connected", "service_url": self.ai_service_url}
            ))
            
            return True
            
        except Exception as e:
            logger.error("Failed to connect to AI service", error=str(e))
            self.is_connected = False
            await self._schedule_reconnect()
            return False
    
    async def disconnect(self):
        """Disconnect from AI service"""
        self.is_connected = False
        
        # Cancel tasks
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        
        if self.connection_task:
            self.connection_task.cancel()
        
        # Close websocket
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception as e:
                logger.warning("Error closing websocket", error=str(e))
        
        self.websocket = None
        logger.info("Disconnected from AI service")
    
    async def _handle_messages(self):
        """Handle incoming WebSocket messages"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    await self._process_message(data)
                except json.JSONDecodeError as e:
                    logger.error("Invalid JSON received from AI service", error=str(e))
                except Exception as e:
                    logger.error("Error processing AI message", error=str(e))
                    
        except ConnectionClosed:
            logger.warning("AI service connection closed")
            self.is_connected = False
            await self._schedule_reconnect()
        except WebSocketException as e:
            logger.error("WebSocket error", error=str(e))
            self.is_connected = False
            await self._schedule_reconnect()
        except Exception as e:
            logger.error("Unexpected error in message handling", error=str(e))
            self.is_connected = False
    
    async def _process_message(self, data: Dict[str, Any]):
        """Process a received message"""
        message_type = data.get("type")
        if not message_type:
            logger.warning("Received message without type field")
            return
        
        try:
            msg_type_enum = AIMessageType(message_type)
            handler = self.message_handlers.get(msg_type_enum)
            
            if handler:
                await handler(data)
            else:
                logger.warning("No handler for message type", type=message_type)
                
        except ValueError:
            logger.warning("Unknown message type received", type=message_type)
    
    async def _handle_decision_response(self, data: Dict[str, Any]):
        """Handle AI decision response"""
        request_id = data.get("request_id")
        if not request_id or request_id not in self.pending_requests:
            logger.warning("Received decision response for unknown request", request_id=request_id)
            return
        
        # Get the pending request
        request_info = self.pending_requests.pop(request_id)
        session_id = request_info["session_id"]
        
        # Extract decision data
        decision = data.get("decision", {})
        confidence = data.get("confidence", 0.0)
        reasoning = data.get("reasoning", "")
        
        logger.info("Received AI decision", 
                   request_id=request_id,
                   action_type=decision.get("action_type"),
                   confidence=confidence)
        
        # Emit decision event
        await self.event_bus.emit(GameEvent(
            type=EventType.AI_DECISION_MADE,
            session_id=session_id,
            data={
                "request_id": request_id,
                "decision": decision,
                "confidence": confidence,
                "reasoning": reasoning,
                "timestamp": datetime.now().isoformat()
            }
        ))
    
    async def _handle_ai_ready(self, data: Dict[str, Any]):
        """Handle AI ready notification"""
        logger.info("AI service ready", capabilities=data.get("capabilities", []))
        
        await self.event_bus.emit(GameEvent(
            type=EventType.AI_ANALYSIS_COMPLETE,
            session_id="system",
            data={"event": "ai_ready", "capabilities": data.get("capabilities", [])}
        ))
    
    async def _handle_ai_error(self, data: Dict[str, Any]):
        """Handle AI error notification"""
        error_type = data.get("error_type", "unknown")
        error_message = data.get("message", "")
        request_id = data.get("request_id")
        
        logger.error("AI service error", 
                    type=error_type, 
                    message=error_message,
                    request_id=request_id)
        
        # Clean up pending request if applicable
        if request_id and request_id in self.pending_requests:
            request_info = self.pending_requests.pop(request_id)
            session_id = request_info["session_id"]
            
            # Emit error event
            await self.event_bus.emit(GameEvent(
                type=EventType.GAME_ERROR,
                session_id=session_id,
                data={
                    "error_type": "ai_error",
                    "error_message": error_message,
                    "request_id": request_id
                }
            ))
    
    async def _handle_ai_status(self, data: Dict[str, Any]):
        """Handle AI status update"""
        status = data.get("status", "unknown")
        logger.debug("AI status update", status=status, data=data)
    
    async def _handle_pong(self, data: Dict[str, Any]):
        """Handle pong response"""
        logger.debug("Received pong from AI service")
    
    async def _handle_heartbeat(self, data: Dict[str, Any]):
        """Handle heartbeat from AI service"""
        # Respond with heartbeat
        await self._send_message({
            "type": AIMessageType.HEARTBEAT.value,
            "timestamp": datetime.now().isoformat()
        })
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeat to AI service"""
        while self.is_connected:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                if self.is_connected:
                    await self._send_message({
                        "type": AIMessageType.PING.value,
                        "timestamp": datetime.now().isoformat()
                    })
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Heartbeat error", error=str(e))
    
    async def _send_message(self, data: Dict[str, Any]) -> bool:
        """Send message to AI service"""
        if not self.is_connected or not self.websocket:
            logger.warning("Cannot send message: not connected to AI service")
            return False
        
        try:
            message = json.dumps(data)
            await self.websocket.send(message)
            return True
        except Exception as e:
            logger.error("Failed to send message to AI service", error=str(e))
            self.is_connected = False
            await self._schedule_reconnect()
            return False
    
    async def _schedule_reconnect(self):
        """Schedule reconnection attempt"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error("Max reconnection attempts reached, giving up")
            return
        
        self.reconnect_attempts += 1
        delay = self.reconnect_delay * (2 ** (self.reconnect_attempts - 1))  # Exponential backoff
        
        logger.info("Scheduling reconnection", 
                   attempt=self.reconnect_attempts, 
                   delay=delay)
        
        await asyncio.sleep(delay)
        await self.connect()
    
    async def request_ai_decision(self, session_id: str, game_state: Dict[str, Any], 
                                unit_id: str, available_actions: List[Dict[str, Any]]) -> str:
        """Request AI decision for a unit"""
        if not self.is_connected:
            logger.warning("Cannot request AI decision: not connected")
            return ""
        
        request_id = str(uuid.uuid4())
        
        request_data = {
            "type": AIMessageType.REQUEST_DECISION.value,
            "request_id": request_id,
            "session_id": session_id,
            "unit_id": unit_id,
            "game_state": game_state,
            "available_actions": available_actions,
            "timestamp": datetime.now().isoformat()
        }
        
        # Store pending request
        self.pending_requests[request_id] = {
            "session_id": session_id,
            "unit_id": unit_id,
            "timestamp": datetime.now()
        }
        
        success = await self._send_message(request_data)
        if not success:
            self.pending_requests.pop(request_id, None)
            return ""
        
        logger.info("Requested AI decision", 
                   request_id=request_id,
                   unit_id=unit_id,
                   session_id=session_id)
        
        # Schedule timeout cleanup
        asyncio.create_task(self._cleanup_expired_request(request_id))
        
        return request_id
    
    async def _cleanup_expired_request(self, request_id: str):
        """Clean up expired request after timeout"""
        await asyncio.sleep(self.request_timeout)
        
        if request_id in self.pending_requests:
            request_info = self.pending_requests.pop(request_id)
            logger.warning("AI request timed out", 
                         request_id=request_id,
                         unit_id=request_info.get("unit_id"))
            
            # Emit timeout event
            await self.event_bus.emit(GameEvent(
                type=EventType.GAME_ERROR,
                session_id=request_info["session_id"],
                data={
                    "error_type": "ai_timeout",
                    "request_id": request_id,
                    "unit_id": request_info.get("unit_id")
                }
            ))
    
    async def send_game_state_update(self, session_id: str, game_state: Dict[str, Any]):
        """Send game state update to AI service"""
        if not self.is_connected:
            return
        
        await self._send_message({
            "type": AIMessageType.GAME_STATE_UPDATE.value,
            "session_id": session_id,
            "game_state": game_state,
            "timestamp": datetime.now().isoformat()
        })
    
    async def send_battle_start(self, session_id: str, battle_info: Dict[str, Any]):
        """Notify AI service of battle start"""
        if not self.is_connected:
            return
        
        await self._send_message({
            "type": AIMessageType.BATTLE_START.value,
            "session_id": session_id,
            "battle_info": battle_info,
            "timestamp": datetime.now().isoformat()
        })
    
    async def send_battle_end(self, session_id: str, battle_result: Dict[str, Any]):
        """Notify AI service of battle end"""
        if not self.is_connected:
            return
        
        await self._send_message({
            "type": AIMessageType.BATTLE_END.value,
            "session_id": session_id,
            "battle_result": battle_result,
            "timestamp": datetime.now().isoformat()
        })
    
    async def send_unit_event(self, session_id: str, event_type: str, unit_data: Dict[str, Any]):
        """Send unit spawn/death event"""
        if not self.is_connected:
            return
        
        message_type = AIMessageType.UNIT_SPAWN if event_type == "spawn" else AIMessageType.UNIT_DEATH
        
        await self._send_message({
            "type": message_type.value,
            "session_id": session_id,
            "unit_data": unit_data,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get current connection status"""
        return {
            "is_connected": self.is_connected,
            "service_url": self.ai_service_url,
            "pending_requests": len(self.pending_requests),
            "reconnect_attempts": self.reconnect_attempts,
            "last_heartbeat": datetime.now().isoformat() if self.is_connected else None
        }
    
    def get_pending_requests(self) -> Dict[str, Any]:
        """Get information about pending requests"""
        return {
            request_id: {
                "session_id": info["session_id"],
                "unit_id": info["unit_id"],
                "age_seconds": (datetime.now() - info["timestamp"]).total_seconds()
            }
            for request_id, info in self.pending_requests.items()
        }
    
    async def cleanup(self):
        """Clean up resources"""
        await self.disconnect()
        self.pending_requests.clear()
        logger.info("AI WebSocket client cleaned up")