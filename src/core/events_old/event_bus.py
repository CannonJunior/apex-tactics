"""
Event Bus for Decoupled System Communication

Implements publish-subscribe pattern for system communication.
Enables systems to communicate without direct dependencies.
Includes priority queue optimizations for performance.
"""

from typing import Dict, List, Callable, Type, Any, Optional
from collections import defaultdict
import time
import uuid
import heapq
from enum import Enum


class EventPriority(Enum):
    """Priority levels for event processing"""
    IMMEDIATE = 0      # Process immediately (UI, input)
    HIGH = 1          # High priority (combat, state changes)
    NORMAL = 2        # Normal priority (movement, animations)
    LOW = 3           # Low priority (background tasks, logging)
    DEFERRED = 4      # Process at end of frame (cleanup, stats)


class Event:
    """
    Base class for all events in the system.
    
    Events are immutable data objects that represent something that happened.
    """
    
    def __init__(self, priority: EventPriority = EventPriority.NORMAL):
        self.event_id = str(uuid.uuid4())
        self.timestamp = time.time()
        self.priority = priority
        self.handled = False
    
    def mark_handled(self):
        """Mark event as handled (for debugging/logging)"""
        self.handled = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize event to dictionary"""
        return {
            'event_type': self.__class__.__name__,
            'event_id': self.event_id,
            'timestamp': self.timestamp,
            'priority': self.priority.name,
            'handled': self.handled
        }


class PriorityEvent:
    """
    Wrapper for events in priority queue.
    
    Implements comparison operators for heapq priority queue.
    """
    
    def __init__(self, priority: int, event_id: str, event: Event):
        self.priority = priority
        self.event_id = event_id  # For stable ordering
        self.event = event
    
    def __lt__(self, other):
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.event_id < other.event_id  # Stable ordering
    
    def __eq__(self, other):
        return self.priority == other.priority and self.event_id == other.event_id

class EventBus:
    """
    Central event bus for publish-subscribe communication.
    
    Allows systems to communicate without knowing about each other.
    Events are processed with priority queues for optimal performance.
    """
    
    _instance = None
    
    def __init__(self, use_priority_queue: bool = True):
        self._subscribers: Dict[Type[Event], List[Callable]] = defaultdict(list)
        self._event_queue: List[Event] = []
        self._priority_queue: List[PriorityEvent] = []  # Priority queue for events
        self._immediate_events: List[Event] = []  # Immediate processing events
        self._batch_events: Dict[EventPriority, List[Event]] = defaultdict(list)  # Batched events
        self._processing = False
        self._use_priority_queue = use_priority_queue
        self._stats = EventBusStats()
        self._event_counter = 0  # For stable ordering
    
    @classmethod
    def get_instance(cls) -> 'EventBus':
        """Get singleton instance of event bus"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def subscribe(self, event_type: Type[Event], handler: Callable[[Event], None]):
        """
        Subscribe to events of specified type.
        
        Args:
            event_type: Type of event to listen for
            handler: Function to call when event occurs
        """
        self._subscribers[event_type].append(handler)
        self._stats.subscriber_count += 1
    
    def unsubscribe(self, event_type: Type[Event], handler: Callable[[Event], None]):
        """
        Unsubscribe from events of specified type.
        
        Args:
            event_type: Type of event to stop listening for
            handler: Handler function to remove
        """
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(handler)
                self._stats.subscriber_count -= 1
            except ValueError:
                pass  # Handler wasn't subscribed
    
    def publish(self, event: Event):
        """
        Publish event to all subscribers with priority handling.
        
        Args:
            event: Event to publish
        """
        if event.priority == EventPriority.IMMEDIATE:
            # Process immediate events right away
            self._immediate_events.append(event)
            if not self._processing:
                self._process_immediate_events()
        elif self._use_priority_queue:
            # Use priority queue for optimal ordering
            self._event_counter += 1
            priority_event = PriorityEvent(
                event.priority.value, 
                f"{self._event_counter:010d}",
                event
            )
            heapq.heappush(self._priority_queue, priority_event)
        else:
            # Fall back to simple queue
            if self._processing:
                self._event_queue.append(event)
            else:
                self._process_event(event)
    
    def publish_immediate(self, event: Event):
        """
        Publish event immediately, bypassing queue.
        
        Use with caution - can cause recursive event processing.
        
        Args:
            event: Event to publish immediately
        """
        self._process_event(event)
    
    def publish_batch(self, events: List[Event]):
        """
        Publish multiple events efficiently in a batch.
        
        Args:
            events: List of events to publish
        """
        for event in events:
            self.publish(event)
    
    def _process_immediate_events(self):
        """Process all immediate priority events"""
        while self._immediate_events:
            event = self._immediate_events.pop(0)
            self._process_event(event)
    
    def process_events(self, max_events_per_frame: int = 100):
        """
        Process all queued events with priority handling.
        
        Args:
            max_events_per_frame: Maximum events to process per frame
        """
        if self._processing:
            return  # Prevent recursive processing
        
        self._processing = True
        
        try:
            # Process immediate events first
            self._process_immediate_events()
            
            # Process priority queue events
            events_processed = 0
            if self._use_priority_queue:
                while self._priority_queue and events_processed < max_events_per_frame:
                    priority_event = heapq.heappop(self._priority_queue)
                    self._process_event(priority_event.event)
                    events_processed += 1
            else:
                # Fall back to simple queue processing
                while self._event_queue and events_processed < max_events_per_frame:
                    event = self._event_queue.pop(0)
                    self._process_event(event)
                    events_processed += 1
                    
        finally:
            self._processing = False
    
    def _process_event(self, event: Event):
        """
        Process single event by notifying all subscribers.
        
        Args:
            event: Event to process
        """
        event_type = type(event)
        
        # Get handlers for this event type
        handlers = self._subscribers.get(event_type, [])
        
        self._stats.events_published += 1
        self._stats.handlers_called += len(handlers)
        
        # Call all handlers
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                # Log error but continue with other handlers
                print(f"Error in event handler: {e}")
                self._stats.handler_errors += 1
    
    def clear_subscribers(self):
        """Clear all subscribers (useful for testing)"""
        self._subscribers.clear()
        self._stats.subscriber_count = 0
    
    def get_subscriber_count(self, event_type: Type[Event] = None) -> int:
        """
        Get number of subscribers for event type.
        
        Args:
            event_type: Event type to count, or None for total
            
        Returns:
            Number of subscribers
        """
        if event_type is None:
            return sum(len(handlers) for handlers in self._subscribers.values())
        else:
            return len(self._subscribers.get(event_type, []))
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics with queue information"""
        stats = self._stats.to_dict()
        stats.update({
            'priority_queue_size': len(self._priority_queue),
            'simple_queue_size': len(self._event_queue),
            'immediate_queue_size': len(self._immediate_events),
            'using_priority_queue': self._use_priority_queue,
            'events_in_queues': len(self._priority_queue) + len(self._event_queue) + len(self._immediate_events)
        })
        return stats
    
    def clear_all_queues(self):
        """Clear all event queues (useful for testing)"""
        self._event_queue.clear()
        self._priority_queue.clear()
        self._immediate_events.clear()
        self._batch_events.clear()
    
    def get_queue_sizes(self) -> Dict[str, int]:
        """Get sizes of all event queues"""
        return {
            'priority_queue': len(self._priority_queue),
            'simple_queue': len(self._event_queue),
            'immediate_queue': len(self._immediate_events),
            'total': len(self._priority_queue) + len(self._event_queue) + len(self._immediate_events)
        }
    
    def reset_stats(self):
        """Reset statistics counters"""
        self._stats = EventBusStats()

class EventBusStats:
    """Statistics tracking for event bus performance"""
    
    def __init__(self):
        self.events_published = 0
        self.handlers_called = 0
        self.handler_errors = 0
        self.subscriber_count = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for reporting"""
        return {
            'events_published': self.events_published,
            'handlers_called': self.handlers_called,
            'handler_errors': self.handler_errors,
            'subscriber_count': self.subscriber_count
        }

# Create singleton instance for easy access
_event_bus_singleton = None

def get_event_bus():
    """Get singleton EventBus instance"""
    global _event_bus_singleton
    if _event_bus_singleton is None:
        _event_bus_singleton = EventBus()
    return _event_bus_singleton