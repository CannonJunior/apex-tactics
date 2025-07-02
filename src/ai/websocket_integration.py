"""
WebSocket Integration for AI Services

Provides real-time communication between AI service, MCP Gateway, and Game Engine
for live tactical analysis, decision streaming, and adaptive responses.
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from enum import Enum

import structlog
import websockets
from websockets.exceptions import ConnectionClosed
from pydantic import BaseModel

logger = structlog.get_logger()


class MessageType(str, Enum):
    """WebSocket message types"""
    # AI Service messages
    AI_DECISION_REQUEST = "ai_decision_request"
    AI_DECISION_RESPONSE = "ai_decision_response"
    AI_ANALYSIS_UPDATE = "ai_analysis_update"
    AI_LEARNING_UPDATE = "ai_learning_update"
    
    # Game Engine messages
    GAME_STATE_UPDATE = "game_state_update"
    UNIT_ACTION_EXECUTED = "unit_action_executed"
    TURN_CHANGE = "turn_change"
    GAME_EVENT = "game_event"
    
    # MCP Gateway messages
    MCP_TOOL_CALL = "mcp_tool_call"
    MCP_TOOL_RESULT = "mcp_tool_result"
    MCP_ANALYSIS_REQUEST = "mcp_analysis_request"
    
    # System messages
    HEARTBEAT = "heartbeat"
    CONNECTION_STATUS = "connection_status"
    ERROR = "error"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"


class WSMessage(BaseModel):
    """Base WebSocket message structure"""
    type: MessageType
    session_id: Optional[str] = None
    source_service: str
    target_service: Optional[str] = None
    timestamp: datetime
    data: Dict[str, Any]
    correlation_id: Optional[str] = None


class ConnectionManager:
    """Manages WebSocket connections between services"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.connections: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.subscriptions: Dict[str, List[MessageType]] = {}
        self.message_handlers: Dict[MessageType, Callable] = {}
        self.outbound_connections: Dict[str, websockets.WebSocketClientProtocol] = {}
        self.connection_status: Dict[str, bool] = {}
        
    async def start_server(self, host: str = "0.0.0.0", port: int = 9000):
        """Start WebSocket server"""
        async def handle_connection(websocket, path):
            await self._handle_new_connection(websocket, path)
        
        self.server = await websockets.serve(handle_connection, host, port)
        logger.info("WebSocket server started", service=self.service_name, host=host, port=port)
    
    async def connect_to_service(self, service_name: str, uri: str):
        """Connect to another service's WebSocket"""
        try:
            connection = await websockets.connect(uri)
            self.outbound_connections[service_name] = connection
            self.connection_status[service_name] = True
            
            # Start listening for messages
            asyncio.create_task(self._listen_to_service(service_name, connection))
            
            # Send connection status
            await self._send_connection_status(service_name, True)
            
            logger.info("Connected to service", 
                       service=self.service_name, 
                       target_service=service_name, 
                       uri=uri)
            
        except Exception as e:
            self.connection_status[service_name] = False
            logger.error("Failed to connect to service", 
                        service=self.service_name,
                        target_service=service_name, 
                        error=str(e))
    
    async def _handle_new_connection(self, websocket, path):
        """Handle new incoming WebSocket connection"""
        connection_id = f"conn_{int(time.time() * 1000)}"
        self.connections[connection_id] = websocket
        
        try:
            logger.info("New WebSocket connection", 
                       service=self.service_name, 
                       connection_id=connection_id)
            
            async for message in websocket:
                await self._handle_message(connection_id, message)
                
        except ConnectionClosed:
            logger.info("WebSocket connection closed", 
                       service=self.service_name, 
                       connection_id=connection_id)
        except Exception as e:
            logger.error("WebSocket error", 
                        service=self.service_name, 
                        connection_id=connection_id, 
                        error=str(e))
        finally:
            if connection_id in self.connections:
                del self.connections[connection_id]
            if connection_id in self.subscriptions:
                del self.subscriptions[connection_id]
    
    async def _listen_to_service(self, service_name: str, connection: websockets.WebSocketClientProtocol):
        """Listen for messages from connected service"""
        try:
            async for message in connection:
                await self._handle_service_message(service_name, message)
                
        except ConnectionClosed:
            logger.warning("Service connection closed", 
                          service=self.service_name, 
                          target_service=service_name)
            self.connection_status[service_name] = False
            
        except Exception as e:
            logger.error("Service connection error", 
                        service=self.service_name, 
                        target_service=service_name, 
                        error=str(e))
            self.connection_status[service_name] = False
    
    async def _handle_message(self, connection_id: str, raw_message: str):
        """Handle incoming WebSocket message"""
        try:
            message_data = json.loads(raw_message)
            message = WSMessage(**message_data)
            
            # Handle subscription messages
            if message.type == MessageType.SUBSCRIBE:
                event_types = message.data.get("event_types", [])
                self.subscriptions[connection_id] = [MessageType(t) for t in event_types]
                logger.debug("Connection subscribed", 
                           connection_id=connection_id, 
                           event_types=event_types)
                return
            
            elif message.type == MessageType.UNSUBSCRIBE:
                if connection_id in self.subscriptions:
                    del self.subscriptions[connection_id]
                logger.debug("Connection unsubscribed", connection_id=connection_id)
                return
            
            # Route message to handler
            if message.type in self.message_handlers:
                await self.message_handlers[message.type](message, connection_id)
            else:
                logger.warning("No handler for message type", 
                             message_type=message.type, 
                             service=self.service_name)
                
        except Exception as e:
            logger.error("Failed to handle message", 
                        connection_id=connection_id, 
                        error=str(e))
    
    async def _handle_service_message(self, service_name: str, raw_message: str):
        """Handle message from connected service"""
        await self._handle_message(service_name, raw_message)
    
    def register_handler(self, message_type: MessageType, handler: Callable):
        """Register message handler"""
        self.message_handlers[message_type] = handler
        logger.debug("Handler registered", 
                    message_type=message_type, 
                    service=self.service_name)
    
    async def send_message(self, message: WSMessage, target_connection: Optional[str] = None):
        """Send message to specific connection or broadcast"""
        message_json = json.dumps(message.dict(), default=str)
        
        if target_connection and target_connection in self.connections:
            # Send to specific connection
            try:
                await self.connections[target_connection].send(message_json)
            except Exception as e:
                logger.error("Failed to send message to connection", 
                           connection_id=target_connection, 
                           error=str(e))
        else:
            # Broadcast to subscribed connections
            sent_count = 0
            for conn_id, websocket in self.connections.items():
                if self._should_send_to_connection(conn_id, message.type):
                    try:
                        await websocket.send(message_json)
                        sent_count += 1
                    except Exception as e:
                        logger.error("Failed to broadcast message", 
                                   connection_id=conn_id, 
                                   error=str(e))
            
            logger.debug("Message broadcasted", 
                        message_type=message.type, 
                        recipients=sent_count)
    
    async def send_to_service(self, service_name: str, message: WSMessage):
        """Send message to specific connected service"""
        if service_name in self.outbound_connections:
            try:
                message_json = json.dumps(message.dict(), default=str)
                await self.outbound_connections[service_name].send(message_json)
                
                logger.debug("Message sent to service", 
                           target_service=service_name, 
                           message_type=message.type)
                           
            except Exception as e:
                logger.error("Failed to send message to service", 
                           service=self.service_name, 
                           target_service=service_name, 
                           error=str(e))
        else:
            logger.warning("Service not connected", 
                          service=self.service_name, 
                          target_service=service_name)
    
    def _should_send_to_connection(self, connection_id: str, message_type: MessageType) -> bool:
        """Check if message should be sent to connection based on subscriptions"""
        if connection_id not in self.subscriptions:
            return True  # Send to unfiltered connections
        
        return message_type in self.subscriptions[connection_id]
    
    async def _send_connection_status(self, service_name: str, connected: bool):
        """Send connection status update"""
        message = WSMessage(
            type=MessageType.CONNECTION_STATUS,
            source_service=self.service_name,
            target_service=service_name,
            timestamp=datetime.now(),
            data={
                "connected": connected,
                "service": service_name
            }
        )
        
        await self.send_message(message)
    
    async def close_all_connections(self):
        """Close all WebSocket connections"""
        # Close incoming connections
        for websocket in self.connections.values():
            await websocket.close()
        
        # Close outbound connections
        for connection in self.outbound_connections.values():
            await connection.close()
        
        # Close server
        if hasattr(self, 'server'):
            self.server.close()
            await self.server.wait_closed()
        
        logger.info("All WebSocket connections closed", service=self.service_name)


class AIServiceWebSocketHandler:
    """WebSocket handler for AI Service"""
    
    def __init__(self, ai_service):
        self.ai_service = ai_service
        self.connection_manager = ConnectionManager("ai-service")
        self._register_handlers()
    
    def _register_handlers(self):
        """Register message handlers"""
        self.connection_manager.register_handler(
            MessageType.AI_DECISION_REQUEST, 
            self._handle_decision_request
        )
        self.connection_manager.register_handler(
            MessageType.GAME_STATE_UPDATE, 
            self._handle_game_state_update
        )
        self.connection_manager.register_handler(
            MessageType.MCP_TOOL_RESULT, 
            self._handle_mcp_result
        )
        self.connection_manager.register_handler(
            MessageType.HEARTBEAT, 
            self._handle_heartbeat
        )
    
    async def start(self, host: str = "0.0.0.0", port: int = 9001):
        """Start WebSocket handler"""
        await self.connection_manager.start_server(host, port)
    
    async def connect_to_services(self):
        """Connect to other services"""
        # Connect to Game Engine
        await self.connection_manager.connect_to_service(
            "game-engine", 
            "ws://game-engine:8000/ws"
        )
        
        # Connect to MCP Gateway
        await self.connection_manager.connect_to_service(
            "mcp-gateway", 
            "ws://mcp-gateway:8002/ws"
        )
    
    async def _handle_decision_request(self, message: WSMessage, connection_id: str):
        """Handle AI decision request"""
        try:
            # Extract request data
            request_data = message.data
            
            # Make AI decision
            response = await self.ai_service.make_ai_decision(request_data)
            
            # Send response
            response_message = WSMessage(
                type=MessageType.AI_DECISION_RESPONSE,
                session_id=message.session_id,
                source_service="ai-service",
                target_service=message.source_service,
                timestamp=datetime.now(),
                data=response.dict(),
                correlation_id=message.correlation_id
            )
            
            await self.connection_manager.send_message(response_message, connection_id)
            
        except Exception as e:
            await self._send_error(message, str(e), connection_id)
    
    async def _handle_game_state_update(self, message: WSMessage, connection_id: str):
        """Handle game state update from game engine"""
        try:
            game_state = message.data
            
            # Trigger AI analysis update
            analysis = await self.ai_service.analyze_game_state(game_state)
            
            # Broadcast analysis update
            analysis_message = WSMessage(
                type=MessageType.AI_ANALYSIS_UPDATE,
                session_id=message.session_id,
                source_service="ai-service",
                timestamp=datetime.now(),
                data=analysis
            )
            
            await self.connection_manager.send_message(analysis_message)
            
        except Exception as e:
            logger.error("Failed to handle game state update", error=str(e))
    
    async def _handle_mcp_result(self, message: WSMessage, connection_id: str):
        """Handle MCP tool execution result"""
        try:
            # Process MCP result for learning
            result_data = message.data
            await self.ai_service.process_mcp_result(result_data)
            
        except Exception as e:
            logger.error("Failed to handle MCP result", error=str(e))
    
    async def _handle_heartbeat(self, message: WSMessage, connection_id: str):
        """Handle heartbeat message"""
        response_message = WSMessage(
            type=MessageType.HEARTBEAT,
            source_service="ai-service",
            timestamp=datetime.now(),
            data={"status": "alive"}
        )
        
        await self.connection_manager.send_message(response_message, connection_id)
    
    async def _send_error(self, original_message: WSMessage, error: str, connection_id: str):
        """Send error response"""
        error_message = WSMessage(
            type=MessageType.ERROR,
            session_id=original_message.session_id,
            source_service="ai-service",
            timestamp=datetime.now(),
            data={
                "error": error,
                "original_message_type": original_message.type
            },
            correlation_id=original_message.correlation_id
        )
        
        await self.connection_manager.send_message(error_message, connection_id)
    
    async def broadcast_learning_update(self, session_id: str, learning_data: Dict[str, Any]):
        """Broadcast AI learning update"""
        message = WSMessage(
            type=MessageType.AI_LEARNING_UPDATE,
            session_id=session_id,
            source_service="ai-service",
            timestamp=datetime.now(),
            data=learning_data
        )
        
        await self.connection_manager.send_message(message)
    
    async def request_mcp_analysis(self, session_id: str, analysis_request: Dict[str, Any]):
        """Request analysis from MCP Gateway"""
        message = WSMessage(
            type=MessageType.MCP_ANALYSIS_REQUEST,
            session_id=session_id,
            source_service="ai-service",
            target_service="mcp-gateway",
            timestamp=datetime.now(),
            data=analysis_request
        )
        
        await self.connection_manager.send_to_service("mcp-gateway", message)


class MCPGatewayWebSocketHandler:
    """WebSocket handler for MCP Gateway"""
    
    def __init__(self, mcp_gateway):
        self.mcp_gateway = mcp_gateway
        self.connection_manager = ConnectionManager("mcp-gateway")
        self._register_handlers()
    
    def _register_handlers(self):
        """Register message handlers"""
        self.connection_manager.register_handler(
            MessageType.MCP_TOOL_CALL, 
            self._handle_tool_call
        )
        self.connection_manager.register_handler(
            MessageType.MCP_ANALYSIS_REQUEST, 
            self._handle_analysis_request
        )
        self.connection_manager.register_handler(
            MessageType.GAME_STATE_UPDATE, 
            self._handle_game_state_update
        )
        self.connection_manager.register_handler(
            MessageType.HEARTBEAT, 
            self._handle_heartbeat
        )
    
    async def start(self, host: str = "0.0.0.0", port: int = 9002):
        """Start WebSocket handler"""
        await self.connection_manager.start_server(host, port)
    
    async def connect_to_services(self):
        """Connect to other services"""
        # Connect to Game Engine
        await self.connection_manager.connect_to_service(
            "game-engine", 
            "ws://game-engine:8000/ws"
        )
        
        # Connect to AI Service
        await self.connection_manager.connect_to_service(
            "ai-service", 
            "ws://ai-service:8001/ws"
        )
    
    async def _handle_tool_call(self, message: WSMessage, connection_id: str):
        """Handle MCP tool call request"""
        try:
            tool_request = message.data
            
            # Execute tool
            result = await self.mcp_gateway.execute_tool(tool_request)
            
            # Send result
            result_message = WSMessage(
                type=MessageType.MCP_TOOL_RESULT,
                session_id=message.session_id,
                source_service="mcp-gateway",
                target_service=message.source_service,
                timestamp=datetime.now(),
                data=result,
                correlation_id=message.correlation_id
            )
            
            await self.connection_manager.send_message(result_message, connection_id)
            
        except Exception as e:
            await self._send_error(message, str(e), connection_id)
    
    async def _handle_analysis_request(self, message: WSMessage, connection_id: str):
        """Handle analysis request from AI service"""
        try:
            analysis_request = message.data
            
            # Perform analysis
            analysis_result = await self.mcp_gateway.perform_analysis(analysis_request)
            
            # Send result back to AI service
            response_message = WSMessage(
                type=MessageType.MCP_TOOL_RESULT,
                session_id=message.session_id,
                source_service="mcp-gateway",
                target_service="ai-service",
                timestamp=datetime.now(),
                data=analysis_result,
                correlation_id=message.correlation_id
            )
            
            await self.connection_manager.send_to_service("ai-service", response_message)
            
        except Exception as e:
            logger.error("Failed to handle analysis request", error=str(e))
    
    async def _handle_game_state_update(self, message: WSMessage, connection_id: str):
        """Handle game state update"""
        # Forward to AI service for real-time analysis
        await self.connection_manager.send_to_service("ai-service", message)
    
    async def _handle_heartbeat(self, message: WSMessage, connection_id: str):
        """Handle heartbeat message"""
        response_message = WSMessage(
            type=MessageType.HEARTBEAT,
            source_service="mcp-gateway",
            timestamp=datetime.now(),
            data={"status": "alive"}
        )
        
        await self.connection_manager.send_message(response_message, connection_id)
    
    async def _send_error(self, original_message: WSMessage, error: str, connection_id: str):
        """Send error response"""
        error_message = WSMessage(
            type=MessageType.ERROR,
            session_id=original_message.session_id,
            source_service="mcp-gateway",
            timestamp=datetime.now(),
            data={
                "error": error,
                "original_message_type": original_message.type
            },
            correlation_id=original_message.correlation_id
        )
        
        await self.connection_manager.send_message(error_message, connection_id)


class GameEngineWebSocketHandler:
    """WebSocket handler for Game Engine"""
    
    def __init__(self, game_engine):
        self.game_engine = game_engine
        self.connection_manager = ConnectionManager("game-engine")
        self._register_handlers()
    
    def _register_handlers(self):
        """Register message handlers"""
        self.connection_manager.register_handler(
            MessageType.AI_DECISION_RESPONSE, 
            self._handle_ai_decision
        )
        self.connection_manager.register_handler(
            MessageType.MCP_TOOL_RESULT, 
            self._handle_mcp_result
        )
        self.connection_manager.register_handler(
            MessageType.AI_ANALYSIS_UPDATE, 
            self._handle_ai_analysis
        )
        self.connection_manager.register_handler(
            MessageType.HEARTBEAT, 
            self._handle_heartbeat
        )
    
    async def start(self, host: str = "0.0.0.0", port: int = 9000):
        """Start WebSocket handler"""
        await self.connection_manager.start_server(host, port)
    
    async def connect_to_services(self):
        """Connect to other services"""
        # Connect to AI Service
        await self.connection_manager.connect_to_service(
            "ai-service", 
            "ws://ai-service:8001/ws"
        )
        
        # Connect to MCP Gateway
        await self.connection_manager.connect_to_service(
            "mcp-gateway", 
            "ws://mcp-gateway:8002/ws"
        )
    
    async def _handle_ai_decision(self, message: WSMessage, connection_id: str):
        """Handle AI decision response"""
        try:
            decision_data = message.data
            
            # Apply AI decision to game state
            await self.game_engine.apply_ai_decision(decision_data)
            
        except Exception as e:
            logger.error("Failed to handle AI decision", error=str(e))
    
    async def _handle_mcp_result(self, message: WSMessage, connection_id: str):
        """Handle MCP tool result"""
        try:
            result_data = message.data
            
            # Process MCP result in game context
            await self.game_engine.process_mcp_result(result_data)
            
        except Exception as e:
            logger.error("Failed to handle MCP result", error=str(e))
    
    async def _handle_ai_analysis(self, message: WSMessage, connection_id: str):
        """Handle AI analysis update"""
        # Store analysis data for UI display
        analysis_data = message.data
        await self.game_engine.update_ai_analysis(analysis_data)
    
    async def _handle_heartbeat(self, message: WSMessage, connection_id: str):
        """Handle heartbeat message"""
        response_message = WSMessage(
            type=MessageType.HEARTBEAT,
            source_service="game-engine",
            timestamp=datetime.now(),
            data={"status": "alive"}
        )
        
        await self.connection_manager.send_message(response_message, connection_id)
    
    async def broadcast_game_state_update(self, session_id: str, game_state: Dict[str, Any]):
        """Broadcast game state update to all services"""
        message = WSMessage(
            type=MessageType.GAME_STATE_UPDATE,
            session_id=session_id,
            source_service="game-engine",
            timestamp=datetime.now(),
            data=game_state
        )
        
        await self.connection_manager.send_message(message)
    
    async def broadcast_game_event(self, session_id: str, event_data: Dict[str, Any]):
        """Broadcast game event to all services"""
        message = WSMessage(
            type=MessageType.GAME_EVENT,
            session_id=session_id,
            source_service="game-engine",
            timestamp=datetime.now(),
            data=event_data
        )
        
        await self.connection_manager.send_message(message)
    
    async def request_ai_decision(self, session_id: str, decision_request: Dict[str, Any]):
        """Request AI decision"""
        message = WSMessage(
            type=MessageType.AI_DECISION_REQUEST,
            session_id=session_id,
            source_service="game-engine",
            target_service="ai-service",
            timestamp=datetime.now(),
            data=decision_request,
            correlation_id=f"ai_req_{int(time.time() * 1000)}"
        )
        
        await self.connection_manager.send_to_service("ai-service", message)
    
    async def call_mcp_tool(self, session_id: str, tool_request: Dict[str, Any]):
        """Call MCP tool"""
        message = WSMessage(
            type=MessageType.MCP_TOOL_CALL,
            session_id=session_id,
            source_service="game-engine",
            target_service="mcp-gateway",
            timestamp=datetime.now(),
            data=tool_request,
            correlation_id=f"mcp_req_{int(time.time() * 1000)}"
        )
        
        await self.connection_manager.send_to_service("mcp-gateway", message)


class WebSocketIntegrationManager:
    """Manages WebSocket integration for all services"""
    
    def __init__(self):
        self.handlers: Dict[str, Any] = {}
        self.health_check_interval = 30  # seconds
        self.health_check_task: Optional[asyncio.Task] = None
    
    def register_handler(self, service_name: str, handler):
        """Register WebSocket handler for service"""
        self.handlers[service_name] = handler
        logger.info("WebSocket handler registered", service=service_name)
    
    async def start_all_handlers(self):
        """Start all registered WebSocket handlers"""
        start_tasks = []
        
        for service_name, handler in self.handlers.items():
            if hasattr(handler, 'start'):
                start_tasks.append(handler.start())
        
        if start_tasks:
            await asyncio.gather(*start_tasks)
            logger.info("All WebSocket handlers started")
    
    async def connect_all_services(self):
        """Connect all services to each other"""
        connection_tasks = []
        
        for service_name, handler in self.handlers.items():
            if hasattr(handler, 'connect_to_services'):
                connection_tasks.append(handler.connect_to_services())
        
        if connection_tasks:
            await asyncio.gather(*connection_tasks)
            logger.info("All services connected")
    
    async def start_health_monitoring(self):
        """Start health monitoring for all connections"""
        self.health_check_task = asyncio.create_task(self._health_check_loop())
    
    async def _health_check_loop(self):
        """Periodic health check loop"""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                
                for service_name, handler in self.handlers.items():
                    if hasattr(handler, 'connection_manager'):
                        # Send heartbeat to all connections
                        heartbeat_message = WSMessage(
                            type=MessageType.HEARTBEAT,
                            source_service=service_name,
                            timestamp=datetime.now(),
                            data={"health_check": True}
                        )
                        
                        await handler.connection_manager.send_message(heartbeat_message)
                
            except Exception as e:
                logger.error("Health check failed", error=str(e))
    
    async def shutdown_all(self):
        """Shutdown all WebSocket connections"""
        # Cancel health check
        if self.health_check_task:
            self.health_check_task.cancel()
        
        # Close all handler connections
        shutdown_tasks = []
        for handler in self.handlers.values():
            if hasattr(handler, 'connection_manager'):
                shutdown_tasks.append(handler.connection_manager.close_all_connections())
        
        if shutdown_tasks:
            await asyncio.gather(*shutdown_tasks)
            logger.info("All WebSocket connections closed")
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics for all services"""
        stats = {}
        
        for service_name, handler in self.handlers.items():
            if hasattr(handler, 'connection_manager'):
                cm = handler.connection_manager
                stats[service_name] = {
                    "incoming_connections": len(cm.connections),
                    "outbound_connections": len(cm.outbound_connections),
                    "connection_status": cm.connection_status.copy(),
                    "subscriptions": len(cm.subscriptions)
                }
        
        return stats