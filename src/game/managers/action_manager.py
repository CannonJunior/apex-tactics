"""
Action Manager

Unified manager for all unit actions, replacing separate attack, magic, and talent managers.
Handles action registration, execution, and integration with the action queue system.
"""

from typing import Any, Dict, List, Optional, Tuple
import json

from .base_manager import BaseManager
from ..actions.action_system import Action, ActionRegistry, ActionType, get_action_registry
from ..queue.action_queue import ActionQueue, ActionPriority
from ..effects.effect_system import EffectFactory
from core.events.event_bus import get_event_bus


class ActionManager(BaseManager):
    """
    Unified manager for all unit actions.
    
    Features:
    - Unified action system replacing attack/magic/talent managers
    - Action queue integration for multiple actions per turn
    - Effect system integration for consistent behavior
    - Event-driven action feedback
    """
    
    def __init__(self, game_controller):
        super().__init__(game_controller)
        
        # Core systems
        self.action_registry = get_action_registry()
        self.action_queue = ActionQueue()
        
        # Integration points
        self.talent_data = None  # Will load existing talent data
        self.current_acting_unit = None
        
        # Action execution state
        self.action_preview_cache = {}
        self.last_action_results = []
        
        # Performance tracking
        self.actions_executed = 0
        self.average_execution_time = 0.0
    
    def _perform_initialization(self):
        """Initialize action manager."""
        # Load existing talent data and convert to actions
        self._load_and_convert_talents()
        
        # Set up event subscriptions
        if self.event_bus:
            self.event_bus.subscribe("unit_action_requested", self.on_unit_action_requested)
            self.event_bus.subscribe("turn_started", self.on_turn_started)
            self.event_bus.subscribe("turn_ended", self.on_turn_ended)
        
        print("🎯 ActionManager: Unified action system ready")
    
    def _load_and_convert_talents(self):
        """Load existing talent data and convert to Action objects."""
        try:
            # Get talent data from game controller
            if hasattr(self.game_controller, 'talent_panel'):
                talent_panel = self.game_controller.talent_panel
                if hasattr(talent_panel, 'talent_data'):
                    self.talent_data = talent_panel.talent_data
                    
                    # Convert talents to actions
                    talent_list = []
                    for category, talents in self.talent_data.items():
                        for talent in talents:
                            talent_list.append(talent)
                    
                    self.action_registry.create_from_talent_files(talent_list)
                    print(f"🔄 Converted {len(talent_list)} talents to actions")
        except Exception as e:
            print(f"⚠️  Could not load existing talents: {e}")
    
    def queue_action(self, unit_id: str, action_id: str, targets: List[Any], 
                    priority: ActionPriority = ActionPriority.NORMAL,
                    player_prediction: Optional[str] = None) -> bool:
        """
        Queue an action for execution.
        
        Args:
            unit_id: ID of unit performing action
            action_id: ID of action to perform
            targets: List of targets
            priority: Execution priority
            player_prediction: Player's prediction for bonus points
            
        Returns:
            True if action was queued successfully
        """
        # Get action from registry
        action = self.action_registry.get(action_id)
        if not action:
            print(f"❌ Action not found: {action_id}")
            return False
        
        # Get unit
        unit = self._get_unit(unit_id)
        if not unit:
            print(f"❌ Unit not found: {unit_id}")
            return False
        
        # Check if action can be executed
        can_execute, reason = action.can_execute(unit, targets, self._get_game_state())
        if not can_execute:
            print(f"❌ Cannot queue action {action_id}: {reason}")
            return False
        
        # Queue the action
        queued_action = self.action_queue.queue_action(
            unit_id, action, targets, priority, player_prediction
        )
        
        # Emit event
        self.emit_event("action_queued", {
            'unit_id': unit_id,
            'action_id': action_id,
            'action_name': action.name,
            'targets': len(targets),
            'priority': priority.name
        })
        
        return True
    
    def execute_action_immediately(self, unit_id: str, action_id: str, targets: List[Any]) -> Dict[str, Any]:
        """
        Execute an action immediately without queuing.
        
        Args:
            unit_id: ID of unit performing action
            action_id: ID of action to perform
            targets: List of targets
            
        Returns:
            Execution result
        """
        # Get action and unit
        action = self.action_registry.get(action_id)
        unit = self._get_unit(unit_id)
        
        if not action or not unit:
            return {'success': False, 'reason': 'Action or unit not found'}
        
        # Execute action
        game_state = self._get_game_state()
        result = action.execute(unit, targets, game_state)
        
        # Track statistics
        self.actions_executed += 1
        self.last_action_results.append(result)
        
        # Emit events
        if result['success']:
            self.emit_event("action_executed", result)
        else:
            self.emit_event("action_failed", result)
        
        return result
    
    def get_available_actions_for_unit(self, unit_id: str) -> List[Dict[str, Any]]:
        """
        Get all actions available to a unit.
        
        Args:
            unit_id: Unit ID
            
        Returns:
            List of available action data
        """
        unit = self._get_unit(unit_id)
        if not unit:
            return []
        
        available_actions = self.action_registry.get_available_for_unit(unit)
        
        action_data = []
        for action in available_actions:
            action_data.append({
                'id': action.id,
                'name': action.name,
                'type': action.type.value,
                'description': action.description,
                'costs': action.costs.to_dict(),
                'targeting': action.targeting.to_dict(),
                'tier': action.tier,
                'level': action.level
            })
        
        return action_data
    
    def get_action_preview(self, unit_id: str, action_id: str, targets: List[Any]) -> Dict[str, Any]:
        """
        Get preview of what an action will do.
        
        Args:
            unit_id: Unit ID
            action_id: Action ID
            targets: Potential targets
            
        Returns:
            Action preview data
        """
        # Check cache first
        cache_key = f"{unit_id}_{action_id}_{len(targets)}"
        if cache_key in self.action_preview_cache:
            return self.action_preview_cache[cache_key]
        
        action = self.action_registry.get(action_id)
        unit = self._get_unit(unit_id)
        
        if not action or not unit:
            return {'error': 'Action or unit not found'}
        
        preview = action.get_preview_data(unit, targets)
        
        # Cache result
        self.action_preview_cache[cache_key] = preview
        
        return preview
    
    def execute_queued_actions(self, unit_stats: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Execute all queued actions in order.
        
        Args:
            unit_stats: Unit statistics for timeline resolution
            
        Returns:
            List of execution results
        """
        # Resolve execution timeline
        timeline = self.action_queue.resolve_timeline(unit_stats)
        
        # Execute all actions
        game_state = self._get_game_state()
        results = self.action_queue.execute_all_queued(game_state)
        
        # Update statistics
        self.actions_executed += len(results)
        self.last_action_results.extend(results)
        
        # Emit completion event
        self.emit_event("action_queue_executed", {
            'actions_executed': len(results),
            'timeline_length': len(timeline)
        })
        
        return results
    
    def get_action_queue_preview(self, unit_stats: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get preview of queued action execution order.
        
        Args:
            unit_stats: Unit statistics for timeline resolution
            
        Returns:
            Timeline preview data
        """
        return self.action_queue.preview_timeline(unit_stats)
    
    def get_unit_queue_preview(self, unit_id: str) -> List[Dict[str, Any]]:
        """
        Get preview of queued actions for specific unit.
        
        Args:
            unit_id: Unit ID
            
        Returns:
            Unit action queue preview
        """
        return self.action_queue.get_unit_queue_preview(unit_id)
    
    def clear_unit_actions(self, unit_id: str):
        """Clear all queued actions for a unit."""
        self.action_queue.clear_unit_queue(unit_id)
        self.emit_event("unit_actions_cleared", {'unit_id': unit_id})
    
    def clear_all_actions(self):
        """Clear all queued actions."""
        self.action_queue.clear_all_queues()
        self.emit_event("all_actions_cleared", {})
    
    def reorder_unit_actions(self, unit_id: str, new_order: List[int]):
        """Reorder actions for a specific unit."""
        self.action_queue.reorder_unit_actions(unit_id, new_order)
        self.emit_event("unit_actions_reordered", {
            'unit_id': unit_id,
            'new_order': new_order
        })
    
    def remove_unit_action(self, unit_id: str, action_index: int) -> bool:
        """Remove a specific queued action."""
        success = self.action_queue.remove_action(unit_id, action_index)
        if success:
            self.emit_event("unit_action_removed", {
                'unit_id': unit_id,
                'action_index': action_index
            })
        return success
    
    def get_action_statistics(self) -> Dict[str, Any]:
        """Get action manager statistics."""
        queue_stats = self.action_queue.get_queue_statistics()
        
        return {
            'actions_executed': self.actions_executed,
            'registered_actions': len(self.action_registry.actions),
            'actions_by_type': {
                action_type.value: len(actions) 
                for action_type, actions in self.action_registry.actions_by_type.items()
                if actions
            },
            'queue_statistics': queue_stats,
            'cache_size': len(self.action_preview_cache)
        }
    
    # Event handlers
    def on_unit_action_requested(self, data):
        """Handle unit action request event."""
        unit_id = data.get('unit_id')
        action_id = data.get('action_id')
        targets = data.get('targets', [])
        immediate = data.get('immediate', False)
        
        if immediate:
            result = self.execute_action_immediately(unit_id, action_id, targets)
            self.emit_event("action_result", result)
        else:
            success = self.queue_action(unit_id, action_id, targets)
            self.emit_event("action_queue_result", {'success': success})
    
    def on_turn_started(self, data):
        """Handle turn start event."""
        turn_number = data.get('turn_number', 0)
        self.action_queue.start_turn(turn_number)
        
        # Clear preview cache
        self.action_preview_cache.clear()
    
    def on_turn_ended(self, data):
        """Handle turn end event."""
        self.action_queue.end_turn()
        
        # Limit action result history
        if len(self.last_action_results) > 100:
            self.last_action_results = self.last_action_results[-50:]
    
    # Helper methods
    def _get_unit(self, unit_id: str) -> Optional[Any]:
        """Get unit by ID from game controller."""
        # Try different ways to access units during migration
        if hasattr(self.game_controller, 'units'):
            return self.game_controller.units.get(unit_id)
        elif hasattr(self.game_controller, 'player_units'):
            for unit in self.game_controller.player_units:
                if getattr(unit, 'id', None) == unit_id:
                    return unit
        elif hasattr(self.game_controller, 'enemy_units'):
            for unit in self.game_controller.enemy_units:
                if getattr(unit, 'id', None) == unit_id:
                    return unit
        return None
    
    def _get_game_state(self) -> Dict[str, Any]:
        """Get current game state."""
        return {
            'units': getattr(self.game_controller, 'units', {}),
            'player_units': getattr(self.game_controller, 'player_units', []),
            'enemy_units': getattr(self.game_controller, 'enemy_units', []),
            'current_turn': getattr(self.game_controller, 'current_turn', 0),
            'battle_state': getattr(self.game_controller, 'battle_state', 'idle')
        }
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status and statistics."""
        total_actions = 0
        unit_queues = {}
        
        for unit_id in self.action_queue.get_all_unit_ids():
            unit_actions = self.action_queue.get_unit_queue(unit_id)
            unit_queues[unit_id] = len(unit_actions)
            total_actions += len(unit_actions)
        
        return {
            'total_queued_actions': total_actions,
            'units_with_actions': len(unit_queues),
            'unit_queue_counts': unit_queues,
            'last_execution_time': getattr(self, 'last_execution_time', 0),
            'manager_active': self.is_initialized
        }
    
    def _perform_cleanup(self):
        """Cleanup when manager shuts down."""
        self.action_queue.clear_all_queues()
        self.action_preview_cache.clear()
        self.last_action_results.clear()