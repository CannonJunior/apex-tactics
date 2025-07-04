"""
Event Bus System

Centralized event system for decoupling game managers and components.
Supports both synchronous and asynchronous event handling.
"""

from typing import Any, Callable, Dict, List, Optional
from collections import defaultdict
import time


class Event:
    """Represents a single event with metadata."""
    
    def __init__(self, event_type: str, data: Any = None, source: str = None):
        self.type = event_type
        self.data = data
        self.source = source
        self.timestamp = time.time()
        self.handled = False
    
    def mark_handled(self):
        """Mark event as handled."""
        self.handled = True
    
    def __repr__(self):
        return f"Event(type='{self.type}', source='{self.source}', handled={self.handled})"


class EventSubscription:
    """Represents a subscription to an event type."""
    
    def __init__(self, event_type: str, callback: Callable, priority: int = 0, once: bool = False):
        self.event_type = event_type
        self.callback = callback
        self.priority = priority  # Higher priority = called first
        self.once = once  # Remove after first call
        self.active = True
    
    def __call__(self, event: Event):
        """Execute the subscription callback."""
        if self.active:
            try:
                self.callback(event)
                if self.once:
                    self.active = False
            except Exception as e:
                print(f"❌ Error in event handler for {self.event_type}: {e}")


class EventBus:
    """
    Centralized event system for game communication.
    
    Allows managers and systems to communicate without direct dependencies.
    """
    
    def __init__(self):
        self.subscriptions: Dict[str, List[EventSubscription]] = defaultdict(list)
        self.event_history: List[Event] = []
        self.max_history = 1000  # Limit memory usage
        self.enabled = True
        
        # Statistics
        self.events_emitted = 0
        self.events_handled = 0
    
    def subscribe(self, event_type: str, callback: Callable, priority: int = 0, once: bool = False) -> EventSubscription:
        """
        Subscribe to an event type.
        
        Args:
            event_type: Type of event to subscribe to
            callback: Function to call when event occurs
            priority: Priority level (higher = called first)
            once: If True, unsubscribe after first event
            
        Returns:
            EventSubscription object for managing the subscription
        """
        subscription = EventSubscription(event_type, callback, priority, once)
        self.subscriptions[event_type].append(subscription)
        
        # Sort by priority (highest first)
        self.subscriptions[event_type].sort(key=lambda s: s.priority, reverse=True)
        
        print(f"📧 Subscribed to '{event_type}' (priority: {priority})")
        return subscription
    
    def unsubscribe(self, subscription: EventSubscription):
        """Remove a subscription."""
        event_type = subscription.event_type
        if subscription in self.subscriptions[event_type]:
            self.subscriptions[event_type].remove(subscription)
            print(f"📭 Unsubscribed from '{event_type}'")
    
    def emit(self, event_type: str, data: Any = None, source: str = None):
        """
        Emit an event to all subscribers.
        
        Args:
            event_type: Type of event to emit
            data: Event data payload
            source: Source of the event (for debugging)
        """
        if not self.enabled:
            return
        
        event = Event(event_type, data, source)
        self.events_emitted += 1
        
        # Add to history
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)
        
        # Notify subscribers
        subscribers = self.subscriptions.get(event_type, [])
        active_subscribers = [s for s in subscribers if s.active]
        
        for subscription in active_subscribers:
            subscription(event)
            self.events_handled += 1
        
        # Clean up one-time subscriptions
        self.subscriptions[event_type] = [s for s in subscribers if s.active]
        
        print(f"📡 Emitted '{event_type}' to {len(active_subscribers)} subscribers")
    
    def emit_immediate(self, event_type: str, data: Any = None, source: str = None):
        """Emit event with immediate processing (alias for emit)."""
        self.emit(event_type, data, source)
    
    def clear_subscriptions(self, event_type: Optional[str] = None):
        """Clear subscriptions for specific event type or all."""
        if event_type:
            self.subscriptions[event_type].clear()
            print(f"🧹 Cleared subscriptions for '{event_type}'")
        else:
            self.subscriptions.clear()
            print("🧹 Cleared all subscriptions")
    
    def disable(self):
        """Disable event bus (events will be ignored)."""
        self.enabled = False
        print("⏸️  Event bus disabled")
    
    def enable(self):
        """Enable event bus."""
        self.enabled = True
        print("▶️  Event bus enabled")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get event bus statistics."""
        return {
            'events_emitted': self.events_emitted,
            'events_handled': self.events_handled,
            'active_subscriptions': sum(len(subs) for subs in self.subscriptions.values()),
            'event_types': list(self.subscriptions.keys()),
            'history_size': len(self.event_history),
            'enabled': self.enabled
        }
    
    def get_recent_events(self, count: int = 10) -> List[Event]:
        """Get recent events from history."""
        return self.event_history[-count:] if self.event_history else []
    
    def debug_info(self):
        """Print debug information about the event bus."""
        stats = self.get_statistics()
        print(f"\n📊 Event Bus Debug Info:")
        print(f"  Status: {'✅ Enabled' if stats['enabled'] else '❌ Disabled'}")
        print(f"  Events Emitted: {stats['events_emitted']}")
        print(f"  Events Handled: {stats['events_handled']}")
        print(f"  Active Subscriptions: {stats['active_subscriptions']}")
        print(f"  Event Types: {len(stats['event_types'])}")
        
        if stats['event_types']:
            print(f"  Registered Types: {', '.join(stats['event_types'])}")
        
        recent = self.get_recent_events(5)
        if recent:
            print(f"  Recent Events:")
            for event in recent:
                print(f"    {event}")


# Global event bus instance
_global_event_bus = None

def get_event_bus() -> EventBus:
    """Get the global event bus instance."""
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
    return _global_event_bus