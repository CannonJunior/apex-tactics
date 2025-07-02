"""
Event System

Provides event-driven communication between game systems
using an observer pattern for loose coupling.
"""

import asyncio
from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

import structlog

logger = structlog.get_logger()


class EventType(str, Enum):
    """Game event types"""
    # Game lifecycle
    GAME_START = "game_start"
    GAME_END = "game_end"
    GAME_PAUSE = "game_pause"
    GAME_RESUME = "game_resume"
    GAME_ERROR = "game_error"
    
    # Turn management
    TURN_START = "turn_start"
    TURN_END = "turn_end"
    TURN_CHANGE = "turn_change"
    
    # Unit actions
    UNIT_MOVED = "unit_moved"
    UNIT_ATTACKED = "unit_attacked"
    UNIT_DIED = "unit_died"
    UNIT_SPAWNED = "unit_spawned"
    UNIT_SELECTED = "unit_selected"
    
    # Combat events
    DAMAGE_DEALT = "damage_dealt"
    HEALING_APPLIED = "healing_applied"
    STATUS_EFFECT_APPLIED = "status_effect_applied"
    STATUS_EFFECT_REMOVED = "status_effect_removed"
    
    # AI events
    AI_DECISION_MADE = "ai_decision_made"
    AI_ANALYSIS_COMPLETE = "ai_analysis_complete"
    
    # System events
    SYSTEM_INITIALIZED = "system_initialized"
    SYSTEM_SHUTDOWN = "system_shutdown"


@dataclass
class GameEvent:
    """Game event data structure"""
    type: EventType
    session_id: str
    data: Dict[str, Any]
    timestamp: datetime = None
    source: str = ""
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class EventBus:
    """Central event bus for game communication"""
    
    def __init__(self):
        self.subscribers: Dict[EventType, List[Callable]] = {}
        self.event_history: List[GameEvent] = []
        self.max_history_size = 1000
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.processing_task: Optional[asyncio.Task] = None
        self.running = False
        
        logger.info("Event bus initialized")
    
    def subscribe(self, event_type: EventType, handler: Callable):
        """Subscribe to specific event type"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        
        self.subscribers[event_type].append(handler)
        
        logger.debug("Event subscriber added", 
                    event_type=event_type, 
                    handler=handler.__name__)
    
    def unsubscribe(self, event_type: EventType, handler: Callable):
        """Unsubscribe from event type"""
        if event_type in self.subscribers:
            if handler in self.subscribers[event_type]:
                self.subscribers[event_type].remove(handler)
                
                logger.debug("Event subscriber removed", 
                            event_type=event_type, 
                            handler=handler.__name__)
    
    async def emit(self, event: GameEvent):
        """Emit an event"""
        await self.event_queue.put(event)
        
        logger.debug("Event emitted", 
                    event_type=event.type, 
                    session_id=event.session_id)
    
    async def start_processing(self):
        """Start event processing loop"""
        if self.running:
            return
        
        self.running = True
        self.processing_task = asyncio.create_task(self._process_events())
        
        logger.info("Event processing started")
    
    async def stop_processing(self):
        """Stop event processing loop"""
        self.running = False
        
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Event processing stopped")
    
    async def _process_events(self):
        """Process events from queue"""
        while self.running:
            try:
                # Wait for event with timeout
                event = await asyncio.wait_for(
                    self.event_queue.get(), 
                    timeout=1.0
                )
                
                await self._handle_event(event)
                
            except asyncio.TimeoutError:
                # Timeout is normal, continue processing
                continue
            except Exception as e:
                logger.error("Event processing error", error=str(e))
    
    async def _handle_event(self, event: GameEvent):
        """Handle a single event"""
        # Add to history
        self.event_history.append(event)
        
        # Limit history size
        if len(self.event_history) > self.max_history_size:
            self.event_history = self.event_history[-self.max_history_size:]
        
        # Notify subscribers
        if event.type in self.subscribers:
            handlers = self.subscribers[event.type]
            
            # Execute handlers concurrently
            tasks = []
            for handler in handlers:
                try:
                    task = asyncio.create_task(self._call_handler(handler, event))
                    tasks.append(task)
                except Exception as e:
                    logger.error("Handler task creation failed", 
                                handler=handler.__name__, 
                                error=str(e))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _call_handler(self, handler: Callable, event: GameEvent):
        """Call event handler safely"""
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)
        except Exception as e:
            logger.error("Event handler failed", 
                        handler=handler.__name__, 
                        event_type=event.type, 
                        error=str(e))
    
    def get_event_history(self, session_id: str = None, 
                         event_type: EventType = None, 
                         limit: int = 100) -> List[GameEvent]:
        """Get event history with optional filtering"""
        events = self.event_history
        
        # Filter by session
        if session_id:
            events = [e for e in events if e.session_id == session_id]
        
        # Filter by type
        if event_type:
            events = [e for e in events if e.type == event_type]
        
        # Apply limit
        return events[-limit:] if events else []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics"""
        subscriber_counts = {
            event_type.value: len(handlers) 
            for event_type, handlers in self.subscribers.items()
        }
        
        return {
            "total_subscribers": sum(len(handlers) for handlers in self.subscribers.values()),
            "subscriber_counts": subscriber_counts,
            "events_in_history": len(self.event_history),
            "queue_size": self.event_queue.qsize(),
            "is_running": self.running
        }
    
    def clear_history(self):
        """Clear event history"""
        self.event_history.clear()
        logger.info("Event history cleared")
    
    async def shutdown(self):
        """Shutdown event bus"""
        await self.stop_processing()
        self.subscribers.clear()
        self.event_history.clear()
        
        logger.info("Event bus shutdown complete")