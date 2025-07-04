"""
Action Queue System

Manages queued actions for all units with timing sequences and execution order.
Supports multiple actions per character per turn with intelligent sequencing.
"""

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import heapq
from collections import defaultdict

from ..actions.action_system import Action


class ActionPriority(Enum):
    """Priority levels for action execution."""
    IMMEDIATE = 0      # Interrupts, reactions
    HIGH = 1          # Quick actions, movement
    NORMAL = 2        # Standard attacks, spells
    LOW = 3           # Slow, powerful actions
    CLEANUP = 4       # End-of-turn effects


@dataclass
class QueuedAction:
    """Represents an action queued for execution."""
    
    # Core action data
    unit_id: str
    action: Action
    targets: List[Any]
    
    # Execution timing
    priority: ActionPriority = ActionPriority.NORMAL
    initiative_bonus: int = 0  # Additional initiative from action
    cast_time: int = 0         # Time before action executes
    
    # Planning and prediction
    predicted_state: Optional[Dict[str, Any]] = None
    player_prediction: Optional[str] = None  # Player's prediction note
    
    # Execution metadata
    queue_time: float = field(default_factory=lambda: 0.0)
    execution_time: Optional[float] = None
    
    def __post_init__(self):
        """Set default values from action."""
        if self.cast_time == 0:
            self.cast_time = getattr(self.action, 'cast_time', 0)
    
    def get_execution_order(self, unit_initiative: int) -> int:
        """Calculate execution order value (lower = executes first)."""
        base_order = self.priority.value * 1000
        initiative_order = max(0, 100 - (unit_initiative + self.initiative_bonus))
        cast_time_order = self.cast_time
        
        return base_order + initiative_order + cast_time_order
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'unit_id': self.unit_id,
            'action_id': self.action.id,
            'action_name': self.action.name,
            'targets': [str(target) for target in self.targets],
            'priority': self.priority.value,
            'initiative_bonus': self.initiative_bonus,
            'cast_time': self.cast_time,
            'player_prediction': self.player_prediction,
            'queue_time': self.queue_time
        }


@dataclass
class ExecutionEvent:
    """Event in the execution timeline."""
    
    order: int  # Execution order (lower = earlier)
    queued_action: QueuedAction
    
    def __lt__(self, other):
        """For heapq ordering."""
        return self.order < other.order


class ActionQueue:
    """
    Manages queued actions for all units with timing sequences.
    
    Features:
    - Multiple actions per unit per turn
    - Initiative-based execution order
    - Prediction and planning support
    - Timeline preview for strategic planning
    """
    
    def __init__(self):
        # Action storage
        self.unit_queues: Dict[str, List[QueuedAction]] = defaultdict(list)
        self.execution_timeline: List[ExecutionEvent] = []
        self.timeline_resolved = False
        
        # Turn management
        self.current_turn = 0
        self.turn_in_progress = False
        
        # Statistics and history
        self.executed_actions: List[QueuedAction] = []
        self.action_count = 0
        
        # Prediction engine will be added later
        self.prediction_engine = None
    
    def queue_action(self, unit_id: str, action: Action, targets: List[Any], 
                    priority: ActionPriority = ActionPriority.NORMAL,
                    player_prediction: Optional[str] = None) -> QueuedAction:
        """
        Queue an action for execution.
        
        Args:
            unit_id: ID of unit performing action
            action: Action to perform
            targets: List of targets for action
            priority: Execution priority
            player_prediction: Player's prediction note for bonuses
            
        Returns:
            QueuedAction object
        """
        queued_action = QueuedAction(
            unit_id=unit_id,
            action=action,
            targets=targets,
            priority=priority,
            player_prediction=player_prediction,
            queue_time=self.action_count
        )
        
        self.unit_queues[unit_id].append(queued_action)
        self.action_count += 1
        self.timeline_resolved = False  # Need to re-resolve timeline
        
        print(f"⏳ Queued action: {action.name} for unit {unit_id}")
        return queued_action
    
    def remove_action(self, unit_id: str, action_index: int) -> bool:
        """
        Remove an action from unit's queue.
        
        Args:
            unit_id: Unit ID
            action_index: Index of action to remove
            
        Returns:
            True if action was removed
        """
        if unit_id in self.unit_queues and 0 <= action_index < len(self.unit_queues[unit_id]):
            removed_action = self.unit_queues[unit_id].pop(action_index)
            self.timeline_resolved = False
            print(f"❌ Removed action: {removed_action.action.name} from unit {unit_id}")
            return True
        return False
    
    def reorder_unit_actions(self, unit_id: str, new_order: List[int]):
        """
        Reorder actions for a specific unit.
        
        Args:
            unit_id: Unit ID
            new_order: New order of action indices
        """
        if unit_id not in self.unit_queues:
            return
        
        current_actions = self.unit_queues[unit_id]
        if len(new_order) != len(current_actions):
            return
        
        reordered_actions = [current_actions[i] for i in new_order]
        self.unit_queues[unit_id] = reordered_actions
        self.timeline_resolved = False
        
        print(f"🔄 Reordered actions for unit {unit_id}")
    
    def clear_unit_queue(self, unit_id: str):
        """Clear all queued actions for a unit."""
        if unit_id in self.unit_queues:
            count = len(self.unit_queues[unit_id])
            self.unit_queues[unit_id].clear()
            self.timeline_resolved = False
            print(f"🧹 Cleared {count} actions for unit {unit_id}")
    
    def clear_all_queues(self):
        """Clear all queued actions."""
        total_actions = sum(len(queue) for queue in self.unit_queues.values())
        self.unit_queues.clear()
        self.execution_timeline.clear()
        self.timeline_resolved = False
        print(f"🧹 Cleared all {total_actions} queued actions")
    
    def resolve_timeline(self, unit_stats: Dict[str, Any]) -> List[ExecutionEvent]:
        """
        Convert all queued actions into execution timeline.
        
        Args:
            unit_stats: Dictionary mapping unit_id to unit stats (for initiative)
            
        Returns:
            List of ExecutionEvent objects in execution order
        """
        if self.timeline_resolved and self.execution_timeline:
            return self.execution_timeline
        
        events = []
        
        for unit_id, actions in self.unit_queues.items():
            unit_initiative = unit_stats.get(unit_id, {}).get('initiative', 50)
            
            for queued_action in actions:
                execution_order = queued_action.get_execution_order(unit_initiative)
                event = ExecutionEvent(execution_order, queued_action)
                events.append(event)
        
        # Sort events by execution order
        events.sort(key=lambda e: e.order)
        
        self.execution_timeline = events
        self.timeline_resolved = True
        
        print(f"📅 Resolved timeline: {len(events)} actions in execution order")
        return events
    
    def execute_next_action(self, game_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Execute the next action in the timeline.
        
        Args:
            game_state: Current game state
            
        Returns:
            Execution result or None if no actions
        """
        if not self.execution_timeline:
            return None
        
        # Get next action
        next_event = self.execution_timeline.pop(0)
        queued_action = next_event.queued_action
        
        # Find the actual unit object
        unit = game_state.get('units', {}).get(queued_action.unit_id)
        if not unit:
            print(f"❌ Cannot execute action: Unit {queued_action.unit_id} not found")
            return None
        
        # Execute the action
        print(f"▶️  Executing: {queued_action.action.name} by {queued_action.unit_id}")
        result = queued_action.action.execute(unit, queued_action.targets, game_state)
        
        # Record execution
        queued_action.execution_time = self.action_count
        self.executed_actions.append(queued_action)
        
        # Check for prediction bonus
        if queued_action.player_prediction:
            # TODO: Implement prediction accuracy checking and bonus calculation
            result['prediction_bonus'] = self._calculate_prediction_bonus(queued_action, result)
        
        return result
    
    def execute_all_queued(self, game_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Execute all queued actions in order.
        
        Args:
            game_state: Current game state
            
        Returns:
            List of execution results
        """
        results = []
        
        while self.execution_timeline:
            result = self.execute_next_action(game_state)
            if result:
                results.append(result)
            else:
                break
        
        print(f"✅ Executed {len(results)} actions")
        return results
    
    def preview_timeline(self, unit_stats: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get preview of execution timeline without executing actions.
        
        Args:
            unit_stats: Unit statistics for timeline resolution
            
        Returns:
            List of timeline preview data
        """
        timeline = self.resolve_timeline(unit_stats)
        
        preview = []
        for i, event in enumerate(timeline):
            queued_action = event.queued_action
            preview.append({
                'sequence': i + 1,
                'unit_id': queued_action.unit_id,
                'action_name': queued_action.action.name,
                'action_type': queued_action.action.type.value,
                'targets': len(queued_action.targets),
                'priority': queued_action.priority.name,
                'execution_order': event.order,
                'player_prediction': queued_action.player_prediction
            })
        
        return preview
    
    def get_unit_queue_preview(self, unit_id: str) -> List[Dict[str, Any]]:
        """
        Get preview of queued actions for specific unit.
        
        Args:
            unit_id: Unit ID
            
        Returns:
            List of queued action previews
        """
        if unit_id not in self.unit_queues:
            return []
        
        preview = []
        for i, queued_action in enumerate(self.unit_queues[unit_id]):
            preview.append({
                'index': i,
                'action_name': queued_action.action.name,
                'action_type': queued_action.action.type.value,
                'targets': len(queued_action.targets),
                'priority': queued_action.priority.name,
                'player_prediction': queued_action.player_prediction,
                'can_remove': True
            })
        
        return preview
    
    def get_queue_statistics(self) -> Dict[str, Any]:
        """Get statistics about the action queue."""
        total_queued = sum(len(queue) for queue in self.unit_queues.values())
        
        return {
            'total_queued_actions': total_queued,
            'units_with_actions': len([uid for uid, queue in self.unit_queues.items() if queue]),
            'timeline_resolved': self.timeline_resolved,
            'executed_actions': len(self.executed_actions),
            'current_turn': self.current_turn,
            'turn_in_progress': self.turn_in_progress
        }
    
    def _calculate_prediction_bonus(self, queued_action: QueuedAction, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate bonus for accurate predictions.
        
        Args:
            queued_action: The action that was executed
            result: Execution result
            
        Returns:
            Prediction bonus data
        """
        # TODO: Implement prediction accuracy analysis
        # Compare player's prediction with actual outcome
        # Award bonuses for accurate predictions
        
        return {
            'prediction_accurate': True,  # Placeholder
            'bonus_type': 'experience',
            'bonus_amount': 10
        }
    
    def start_turn(self, turn_number: int):
        """Start a new turn."""
        self.current_turn = turn_number
        self.turn_in_progress = True
        print(f"🎯 Started turn {turn_number}")
    
    def end_turn(self):
        """End the current turn and cleanup."""
        # Move executed actions to history
        if self.executed_actions:
            print(f"📜 Turn {self.current_turn} completed: {len(self.executed_actions)} actions executed")
        
        # Reset for next turn
        self.executed_actions.clear()
        self.execution_timeline.clear()
        self.timeline_resolved = False
        self.turn_in_progress = False