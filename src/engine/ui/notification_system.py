"""
Notification System

Real-time notification and alert system for player feedback,
including toasts, alerts, and system messages.
"""

import asyncio
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field

import structlog

from ...core.events import EventBus, GameEvent, EventType

logger = structlog.get_logger()


class NotificationType(str, Enum):
    """Types of notifications"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    COMBAT = "combat"
    TURN = "turn"
    SYSTEM = "system"
    ACHIEVEMENT = "achievement"


class NotificationPriority(str, Enum):
    """Notification priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Notification:
    """Notification data structure"""
    notification_id: str
    type: NotificationType
    priority: NotificationPriority
    title: str
    message: str
    
    # Display properties
    duration: float = 5.0
    persistent: bool = False
    dismissible: bool = True
    show_timestamp: bool = True
    
    # Targeting
    session_id: str = ""
    player_id: Optional[str] = None  # None = broadcast to all players
    
    # State
    created_at: datetime = field(default_factory=datetime.now)
    displayed_at: Optional[datetime] = None
    dismissed_at: Optional[datetime] = None
    is_active: bool = True
    
    # Optional data
    action_data: Dict[str, Any] = field(default_factory=dict)
    icon: str = ""
    sound: str = ""


class NotificationQueue:
    """Manages notification queue for a session/player"""
    
    def __init__(self, max_notifications: int = 50):
        self.notifications: List[Notification] = []
        self.max_notifications = max_notifications
        self.dismissed_notifications: List[Notification] = []
        self.max_dismissed = 100
    
    def add_notification(self, notification: Notification):
        """Add notification to queue"""
        # Remove oldest notifications if at limit
        if len(self.notifications) >= self.max_notifications:
            old_notification = self.notifications.pop(0)
            self.dismissed_notifications.append(old_notification)
        
        self.notifications.append(notification)
        notification.displayed_at = datetime.now()
    
    def dismiss_notification(self, notification_id: str) -> bool:
        """Dismiss a specific notification"""
        for i, notification in enumerate(self.notifications):
            if notification.notification_id == notification_id:
                notification.dismissed_at = datetime.now()
                notification.is_active = False
                
                dismissed = self.notifications.pop(i)
                self.dismissed_notifications.append(dismissed)
                
                # Limit dismissed history
                if len(self.dismissed_notifications) > self.max_dismissed:
                    self.dismissed_notifications.pop(0)
                
                return True
        return False
    
    def get_active_notifications(self) -> List[Notification]:
        """Get all active notifications"""
        current_time = datetime.now()
        active = []
        expired = []
        
        for notification in self.notifications:
            if not notification.is_active:
                expired.append(notification)
                continue
            
            # Check if notification has expired
            if (not notification.persistent and 
                notification.displayed_at and
                (current_time - notification.displayed_at).total_seconds() > notification.duration):
                notification.is_active = False
                notification.dismissed_at = current_time
                expired.append(notification)
            else:
                active.append(notification)
        
        # Move expired notifications to dismissed list
        for notification in expired:
            if notification in self.notifications:
                self.notifications.remove(notification)
                self.dismissed_notifications.append(notification)
        
        return active
    
    def clear_all(self, type_filter: Optional[NotificationType] = None):
        """Clear all notifications or specific type"""
        current_time = datetime.now()
        
        if type_filter:
            # Clear specific type
            to_dismiss = [n for n in self.notifications if n.type == type_filter]
        else:
            # Clear all
            to_dismiss = self.notifications.copy()
        
        for notification in to_dismiss:
            notification.dismissed_at = current_time
            notification.is_active = False
            self.notifications.remove(notification)
            self.dismissed_notifications.append(notification)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        active_count = len(self.get_active_notifications())
        
        type_counts = {}
        for notification in self.notifications:
            type_counts[notification.type.value] = type_counts.get(notification.type.value, 0) + 1
        
        return {
            "active_notifications": active_count,
            "total_notifications": len(self.notifications),
            "dismissed_notifications": len(self.dismissed_notifications),
            "type_breakdown": type_counts
        }


class NotificationSystem:
    """Central notification management system"""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        
        # Notification queues per session/player
        self.session_queues: Dict[str, NotificationQueue] = {}
        self.player_queues: Dict[str, NotificationQueue] = {}
        
        # WebSocket callback for sending notifications
        self.websocket_callback: Optional[callable] = None
        
        # Notification ID counter
        self.next_notification_id = 1
        
        # Performance tracking
        self.notifications_sent = 0
        self.last_cleanup_time = datetime.now()
        
        # Subscribe to game events
        self._subscribe_to_events()
        
        logger.info("Notification System initialized")
    
    def _subscribe_to_events(self):
        """Subscribe to game events for automatic notifications"""
        self.event_bus.subscribe(EventType.GAME_START, self._on_game_start)
        self.event_bus.subscribe(EventType.GAME_END, self._on_game_end)
        self.event_bus.subscribe(EventType.TURN_START, self._on_turn_start)
        self.event_bus.subscribe(EventType.TURN_END, self._on_turn_end)
        self.event_bus.subscribe(EventType.UNIT_DIED, self._on_unit_died)
        self.event_bus.subscribe(EventType.DAMAGE_DEALT, self._on_damage_dealt)
        self.event_bus.subscribe(EventType.AI_DECISION_MADE, self._on_ai_decision)
        self.event_bus.subscribe(EventType.GAME_ERROR, self._on_game_error)
    
    def set_websocket_callback(self, callback: callable):
        """Set callback for sending WebSocket notifications"""
        self.websocket_callback = callback
    
    async def send_notification(self, session_id: str, type: NotificationType,
                              title: str, message: str, player_id: Optional[str] = None,
                              priority: NotificationPriority = NotificationPriority.MEDIUM,
                              **kwargs) -> str:
        """Send a notification"""
        notification_id = f"notif_{self.next_notification_id}"
        self.next_notification_id += 1
        
        notification = Notification(
            notification_id=notification_id,
            type=type,
            priority=priority,
            title=title,
            message=message,
            session_id=session_id,
            player_id=player_id,
            **kwargs
        )
        
        # Add to appropriate queue
        if player_id:
            # Player-specific notification
            player_key = f"{session_id}_{player_id}"
            if player_key not in self.player_queues:
                self.player_queues[player_key] = NotificationQueue()
            self.player_queues[player_key].add_notification(notification)
        else:
            # Session-wide notification
            if session_id not in self.session_queues:
                self.session_queues[session_id] = NotificationQueue()
            self.session_queues[session_id].add_notification(notification)
        
        # Send via WebSocket
        await self._send_notification_websocket(notification)
        
        self.notifications_sent += 1
        
        logger.debug("Notification sent",
                    notification_id=notification_id,
                    type=type.value,
                    title=title,
                    player_id=player_id)
        
        return notification_id
    
    async def send_info(self, session_id: str, title: str, message: str, 
                       player_id: Optional[str] = None, **kwargs) -> str:
        """Send info notification"""
        return await self.send_notification(
            session_id, NotificationType.INFO, title, message, 
            player_id, NotificationPriority.LOW, icon="ℹ️", **kwargs
        )
    
    async def send_success(self, session_id: str, title: str, message: str,
                          player_id: Optional[str] = None, **kwargs) -> str:
        """Send success notification"""
        return await self.send_notification(
            session_id, NotificationType.SUCCESS, title, message,
            player_id, NotificationPriority.MEDIUM, icon="✅", **kwargs
        )
    
    async def send_warning(self, session_id: str, title: str, message: str,
                          player_id: Optional[str] = None, **kwargs) -> str:
        """Send warning notification"""
        return await self.send_notification(
            session_id, NotificationType.WARNING, title, message,
            player_id, NotificationPriority.HIGH, icon="⚠️", **kwargs
        )
    
    async def send_error(self, session_id: str, title: str, message: str,
                        player_id: Optional[str] = None, **kwargs) -> str:
        """Send error notification"""
        return await self.send_notification(
            session_id, NotificationType.ERROR, title, message,
            player_id, NotificationPriority.CRITICAL, icon="❌", **kwargs
        )
    
    async def send_combat_notification(self, session_id: str, title: str, message: str,
                                     player_id: Optional[str] = None, **kwargs) -> str:
        """Send combat-related notification"""
        return await self.send_notification(
            session_id, NotificationType.COMBAT, title, message,
            player_id, NotificationPriority.MEDIUM, icon="⚔️", **kwargs
        )
    
    async def send_turn_notification(self, session_id: str, title: str, message: str,
                                   player_id: Optional[str] = None, **kwargs) -> str:
        """Send turn-related notification"""
        return await self.send_notification(
            session_id, NotificationType.TURN, title, message,
            player_id, NotificationPriority.HIGH, icon="🔄", **kwargs
        )
    
    async def send_achievement(self, session_id: str, title: str, message: str,
                             player_id: Optional[str] = None, **kwargs) -> str:
        """Send achievement notification"""
        return await self.send_notification(
            session_id, NotificationType.ACHIEVEMENT, title, message,
            player_id, NotificationPriority.HIGH, icon="🏆", 
            persistent=True, duration=10.0, **kwargs
        )
    
    async def dismiss_notification(self, session_id: str, notification_id: str,
                                 player_id: Optional[str] = None) -> bool:
        """Dismiss a specific notification"""
        queue = None
        
        if player_id:
            player_key = f"{session_id}_{player_id}"
            queue = self.player_queues.get(player_key)
        else:
            queue = self.session_queues.get(session_id)
        
        if queue:
            return queue.dismiss_notification(notification_id)
        
        return False
    
    async def clear_notifications(self, session_id: str, player_id: Optional[str] = None,
                                type_filter: Optional[NotificationType] = None):
        """Clear notifications for session/player"""
        if player_id:
            player_key = f"{session_id}_{player_id}"
            if player_key in self.player_queues:
                self.player_queues[player_key].clear_all(type_filter)
        else:
            if session_id in self.session_queues:
                self.session_queues[session_id].clear_all(type_filter)
    
    async def get_notifications(self, session_id: str, player_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get active notifications for session/player"""
        notifications = []
        
        # Get session-wide notifications
        if session_id in self.session_queues:
            session_notifications = self.session_queues[session_id].get_active_notifications()
            notifications.extend([self._notification_to_dict(n) for n in session_notifications])
        
        # Get player-specific notifications
        if player_id:
            player_key = f"{session_id}_{player_id}"
            if player_key in self.player_queues:
                player_notifications = self.player_queues[player_key].get_active_notifications()
                notifications.extend([self._notification_to_dict(n) for n in player_notifications])
        
        # Sort by priority and timestamp
        notifications.sort(key=lambda n: (
            self._get_priority_weight(n["priority"]),
            -datetime.fromisoformat(n["created_at"]).timestamp()
        ), reverse=True)
        
        return notifications
    
    def _notification_to_dict(self, notification: Notification) -> Dict[str, Any]:
        """Convert notification to dictionary"""
        return {
            "id": notification.notification_id,
            "type": notification.type.value,
            "priority": notification.priority.value,
            "title": notification.title,
            "message": notification.message,
            "duration": notification.duration,
            "persistent": notification.persistent,
            "dismissible": notification.dismissible,
            "show_timestamp": notification.show_timestamp,
            "created_at": notification.created_at.isoformat(),
            "displayed_at": notification.displayed_at.isoformat() if notification.displayed_at else None,
            "icon": notification.icon,
            "sound": notification.sound,
            "action_data": notification.action_data
        }
    
    def _get_priority_weight(self, priority: str) -> int:
        """Get numeric weight for priority sorting"""
        weights = {
            "low": 1,
            "medium": 2,
            "high": 3,
            "critical": 4
        }
        return weights.get(priority, 2)
    
    async def _send_notification_websocket(self, notification: Notification):
        """Send notification via WebSocket"""
        if not self.websocket_callback:
            return
        
        message = {
            "type": "notification",
            "data": self._notification_to_dict(notification)
        }
        
        try:
            if notification.player_id:
                # Send to specific player
                await self.websocket_callback(notification.session_id, message, notification.player_id)
            else:
                # Broadcast to all players in session
                await self.websocket_callback(notification.session_id, message)
        except Exception as e:
            logger.error("Failed to send notification via WebSocket",
                        notification_id=notification.notification_id,
                        error=str(e))
    
    # Event handlers
    async def _on_game_start(self, event: GameEvent):
        """Handle game start event"""
        session_id = event.session_id
        
        await self.send_info(
            session_id,
            "Game Started",
            "The battle has begun! Good luck!",
            duration=3.0
        )
    
    async def _on_game_end(self, event: GameEvent):
        """Handle game end event"""
        session_id = event.session_id
        winner = event.data.get("winner")
        victory_condition = event.data.get("victory_condition")
        
        if winner:
            await self.send_success(
                session_id,
                "Victory!",
                f"Player {winner} wins by {victory_condition}!",
                persistent=True,
                duration=10.0
            )
        else:
            await self.send_info(
                session_id,
                "Game Over",
                "The battle has ended in a draw.",
                persistent=True,
                duration=10.0
            )
    
    async def _on_turn_start(self, event: GameEvent):
        """Handle turn start event"""
        session_id = event.session_id
        current_player = event.data.get("current_player")
        turn_number = event.data.get("turn_number", 1)
        
        await self.send_turn_notification(
            session_id,
            f"Turn {turn_number}",
            f"It's {current_player}'s turn",
            duration=2.0
        )
    
    async def _on_turn_end(self, event: GameEvent):
        """Handle turn end event"""
        session_id = event.session_id
        player_id = event.data.get("player")
        actions_taken = event.data.get("actions_taken", False)
        
        if not actions_taken:
            await self.send_info(
                session_id,
                "Turn Skipped",
                f"{player_id} ended their turn without taking action",
                duration=1.5
            )
    
    async def _on_unit_died(self, event: GameEvent):
        """Handle unit death event"""
        session_id = event.session_id
        unit_id = event.data.get("unit_id")
        cause = event.data.get("cause", "combat")
        
        await self.send_combat_notification(
            session_id,
            "Unit Defeated",
            f"Unit {unit_id} has been defeated by {cause}",
            duration=3.0
        )
    
    async def _on_damage_dealt(self, event: GameEvent):
        """Handle damage dealt event"""
        session_id = event.session_id
        damage = event.data.get("damage", 0)
        target_id = event.data.get("target_id")
        is_critical = event.data.get("is_critical", False)
        
        if is_critical and damage > 50:  # Only notify for significant critical hits
            await self.send_combat_notification(
                session_id,
                "Critical Hit!",
                f"Critical hit dealt {damage} damage to {target_id}!",
                duration=2.0
            )
    
    async def _on_ai_decision(self, event: GameEvent):
        """Handle AI decision event"""
        session_id = event.session_id
        unit_id = event.data.get("unit_id")
        decision = event.data.get("decision", {})
        confidence = event.data.get("confidence", 0.0)
        
        if confidence > 0.9:  # Only notify for high-confidence AI decisions
            action_type = decision.get("action_type", "unknown")
            await self.send_info(
                session_id,
                "AI Action",
                f"AI unit {unit_id} performed {action_type}",
                duration=1.5
            )
    
    async def _on_game_error(self, event: GameEvent):
        """Handle game error event"""
        session_id = event.session_id
        error_type = event.data.get("error_type", "unknown")
        error_message = event.data.get("error_message", "An error occurred")
        
        await self.send_error(
            session_id,
            f"Game Error: {error_type}",
            error_message,
            persistent=True
        )
    
    async def update(self, delta_time: float):
        """Update notification system (called from game loop)"""
        current_time = datetime.now()
        
        # Clean up old queues and expired notifications periodically
        if (current_time - self.last_cleanup_time).total_seconds() > 30.0:
            await self._cleanup_old_notifications()
            self.last_cleanup_time = current_time
    
    async def _cleanup_old_notifications(self):
        """Clean up old notifications and empty queues"""
        # Trigger expired notification cleanup by calling get_active_notifications
        for queue in self.session_queues.values():
            queue.get_active_notifications()
        
        for queue in self.player_queues.values():
            queue.get_active_notifications()
        
        # Remove empty player queues
        empty_player_keys = [
            key for key, queue in self.player_queues.items()
            if len(queue.notifications) == 0
        ]
        
        for key in empty_player_keys:
            del self.player_queues[key]
    
    async def cleanup_session(self, session_id: str):
        """Clean up notifications for a session"""
        # Remove session queue
        if session_id in self.session_queues:
            del self.session_queues[session_id]
        
        # Remove player queues for this session
        player_keys_to_remove = [
            key for key in self.player_queues.keys()
            if key.startswith(f"{session_id}_")
        ]
        
        for key in player_keys_to_remove:
            del self.player_queues[key]
        
        logger.info("Notification queues cleaned up for session", session_id=session_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get notification system statistics"""
        total_active = sum(
            len(queue.get_active_notifications())
            for queue in list(self.session_queues.values()) + list(self.player_queues.values())
        )
        
        return {
            "notifications_sent": self.notifications_sent,
            "active_session_queues": len(self.session_queues),
            "active_player_queues": len(self.player_queues),
            "total_active_notifications": total_active
        }