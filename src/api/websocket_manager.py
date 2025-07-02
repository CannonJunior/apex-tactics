"""
WebSocket Connection Manager

Manages WebSocket connections for real-time game updates and communication.
"""

import asyncio
import json
import logging
from typing import Dict, List, Set, Optional
from datetime import datetime

from fastapi import WebSocket
import structlog

from .models import GameEvent, WSMessage

logger = structlog.get_logger()


class WebSocketConnection:
    """Represents a single WebSocket connection"""
    
    def __init__(self, websocket: WebSocket, session_id: str, connection_id: str):
        self.websocket = websocket
        self.session_id = session_id
        self.connection_id = connection_id
        self.connected_at = datetime.now()
        self.subscribed_events: Set[str] = set()
        self.last_ping = datetime.now()
    
    async def send_json(self, data: dict):
        """Send JSON data to the WebSocket"""
        try:
            await self.websocket.send_json(data)
        except Exception as e:
            logger.warning("Failed to send WebSocket message", 
                         connection_id=self.connection_id, error=str(e))
            raise
    
    async def send_message(self, message: WSMessage):
        """Send a structured message"""
        await self.send_json(message.dict())
    
    def is_subscribed_to(self, event_type: str) -> bool:
        """Check if connection is subscribed to an event type"""
        return event_type in self.subscribed_events or len(self.subscribed_events) == 0
    
    def subscribe_to_events(self, event_types: List[str]):
        """Subscribe to specific event types"""
        self.subscribed_events.update(event_types)
    
    def unsubscribe_from_events(self, event_types: List[str]):
        """Unsubscribe from specific event types"""
        self.subscribed_events.difference_update(event_types)


class WebSocketManager:
    """Manages all WebSocket connections"""
    
    def __init__(self):
        self.connections: Dict[str, WebSocketConnection] = {}
        self.session_connections: Dict[str, Set[str]] = {}
        self._connection_counter = 0
        self._ping_task: Optional[asyncio.Task] = None
        
    def _generate_connection_id(self) -> str:
        """Generate a unique connection ID"""
        self._connection_counter += 1
        return f"conn_{self._connection_counter}_{int(datetime.now().timestamp())}"
    
    async def connect(self, websocket: WebSocket, session_id: str) -> str:
        """Accept a new WebSocket connection"""
        await websocket.accept()
        
        connection_id = self._generate_connection_id()
        connection = WebSocketConnection(websocket, session_id, connection_id)
        
        # Store connection
        self.connections[connection_id] = connection
        
        # Add to session group
        if session_id not in self.session_connections:
            self.session_connections[session_id] = set()
        self.session_connections[session_id].add(connection_id)
        
        logger.info("WebSocket connected", 
                   connection_id=connection_id, 
                   session_id=session_id)
        
        # Start ping task if not already running
        if self._ping_task is None or self._ping_task.done():
            self._ping_task = asyncio.create_task(self._ping_loop())
        
        # Send welcome message
        await connection.send_json({
            "type": "connected",
            "data": {
                "connection_id": connection_id,
                "session_id": session_id,
                "server_time": datetime.now().isoformat()
            }
        })
        
        return connection_id
    
    async def disconnect(self, websocket: WebSocket, session_id: str):
        """Handle WebSocket disconnection"""
        # Find and remove connection
        connection_id = None
        for conn_id, conn in self.connections.items():
            if conn.websocket == websocket:
                connection_id = conn_id
                break
        
        if connection_id:
            await self._remove_connection(connection_id, session_id)
    
    async def disconnect_by_id(self, connection_id: str):
        """Disconnect a specific connection by ID"""
        if connection_id in self.connections:
            connection = self.connections[connection_id]
            await self._remove_connection(connection_id, connection.session_id)
    
    async def _remove_connection(self, connection_id: str, session_id: str):
        """Remove a connection from tracking"""
        if connection_id in self.connections:
            del self.connections[connection_id]
        
        if session_id in self.session_connections:
            self.session_connections[session_id].discard(connection_id)
            if not self.session_connections[session_id]:
                del self.session_connections[session_id]
        
        logger.info("WebSocket disconnected", 
                   connection_id=connection_id, 
                   session_id=session_id)
    
    async def send_to_connection(self, connection_id: str, message: dict):
        """Send message to a specific connection"""
        if connection_id in self.connections:
            connection = self.connections[connection_id]
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning("Failed to send to connection, removing", 
                             connection_id=connection_id, error=str(e))
                await self._remove_connection(connection_id, connection.session_id)
    
    async def broadcast_to_session(self, session_id: str, event: GameEvent):
        """Broadcast an event to all connections in a session"""
        if session_id not in self.session_connections:
            return
        
        message = {
            "type": "game_event",
            "data": event.dict()
        }
        
        # Get connections for this session
        connection_ids = list(self.session_connections[session_id])
        
        # Send to all connections concurrently
        tasks = []
        for connection_id in connection_ids:
            if connection_id in self.connections:
                connection = self.connections[connection_id]
                # Check if connection is subscribed to this event type
                if connection.is_subscribed_to(event.type):
                    tasks.append(self.send_to_connection(connection_id, message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def broadcast_to_all(self, message: dict):
        """Broadcast a message to all connections"""
        if not self.connections:
            return
        
        tasks = [
            self.send_to_connection(conn_id, message)
            for conn_id in self.connections.keys()
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def disconnect_session(self, session_id: str):
        """Disconnect all connections for a session"""
        if session_id not in self.session_connections:
            return
        
        connection_ids = list(self.session_connections[session_id])
        
        for connection_id in connection_ids:
            if connection_id in self.connections:
                connection = self.connections[connection_id]
                try:
                    await connection.websocket.close()
                except:
                    pass  # Connection might already be closed
                await self._remove_connection(connection_id, session_id)
    
    async def disconnect_all(self):
        """Disconnect all connections"""
        connection_ids = list(self.connections.keys())
        
        for connection_id in connection_ids:
            connection = self.connections[connection_id]
            try:
                await connection.websocket.close()
            except:
                pass  # Connection might already be closed
        
        self.connections.clear()
        self.session_connections.clear()
        
        if self._ping_task and not self._ping_task.done():
            self._ping_task.cancel()
    
    def get_session_connections(self, session_id: str) -> List[str]:
        """Get all connection IDs for a session"""
        return list(self.session_connections.get(session_id, set()))
    
    def get_connection_count(self) -> int:
        """Get total number of connections"""
        return len(self.connections)
    
    def get_session_count(self) -> int:
        """Get number of active sessions"""
        return len(self.session_connections)
    
    def get_stats(self) -> dict:
        """Get connection statistics"""
        return {
            "total_connections": len(self.connections),
            "active_sessions": len(self.session_connections),
            "connections_per_session": {
                session_id: len(conn_ids)
                for session_id, conn_ids in self.session_connections.items()
            }
        }
    
    async def handle_subscription(self, connection_id: str, event_types: List[str], subscribe: bool = True):
        """Handle event subscription/unsubscription"""
        if connection_id not in self.connections:
            return
        
        connection = self.connections[connection_id]
        
        if subscribe:
            connection.subscribe_to_events(event_types)
            logger.info("WebSocket subscribed to events", 
                       connection_id=connection_id, events=event_types)
        else:
            connection.unsubscribe_from_events(event_types)
            logger.info("WebSocket unsubscribed from events", 
                       connection_id=connection_id, events=event_types)
    
    async def _ping_loop(self):
        """Periodic ping to keep connections alive"""
        while True:
            try:
                await asyncio.sleep(30)  # Ping every 30 seconds
                
                if not self.connections:
                    continue
                
                ping_message = {
                    "type": "ping",
                    "timestamp": datetime.now().isoformat()
                }
                
                # Send ping to all connections
                tasks = [
                    self.send_to_connection(conn_id, ping_message)
                    for conn_id in list(self.connections.keys())
                ]
                
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in ping loop", error=str(e))