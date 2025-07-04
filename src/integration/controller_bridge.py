"""
Controller Bridge

Bridges the refactored ActionManager system with the original TacticalRPG controller
to provide seamless integration while maintaining all original functionality.
"""

from typing import Dict, List, Any, Optional, Callable
import weakref

from game.managers.action_manager import ActionManager
from game.config.feature_flags import FeatureFlags


class ControllerBridge:
    """
    Bridge between refactored ActionManager and original TacticalRPG controller.
    
    This adapter allows the new action management system to work seamlessly
    with the existing Ursina-based controller while preserving all original
    functionality and adding new features.
    """
    
    def __init__(self, original_controller):
        """
        Initialize bridge with original controller.
        
        Args:
            original_controller: Original TacticalRPG controller instance
        """
        self.original_controller = weakref.ref(original_controller)
        
        # Initialize refactored systems if enabled
        if FeatureFlags.USE_ACTION_MANAGER:
            self.action_manager = ActionManager(self)
            self.action_manager.initialize()
            print("🔗 Controller Bridge: ActionManager integrated")
        else:
            self.action_manager = None
            print("🔗 Controller Bridge: Using legacy action system")
        
        # Integration state
        self.is_bridged = False
        self.legacy_fallback = True
        
        # Cache original controller properties for compatibility
        self._cache_original_properties()
    
    def _cache_original_properties(self):
        """Cache original controller properties for delegation."""
        controller = self.original_controller()
        if controller:
            # Common properties that might be accessed
            self.units = getattr(controller, 'units', {})
            self.grid = getattr(controller, 'grid', None)
            self.turn_manager = getattr(controller, 'turn_manager', None)
            self.active_unit = getattr(controller, 'active_unit', None)
    
    def enable_bridge(self):
        """Enable bridged mode with new action system."""
        if not FeatureFlags.USE_ACTION_MANAGER:
            print("🔗 Cannot enable bridge: ActionManager disabled by feature flags")
            return False
        
        if not self.action_manager:
            print("🔗 Cannot enable bridge: ActionManager not initialized")
            return False
        
        self.is_bridged = True
        self.legacy_fallback = False
        print("🔗 Controller Bridge enabled: Using refactored action system")
        return True
    
    def disable_bridge(self):
        """Disable bridged mode, fall back to legacy system."""
        self.is_bridged = False
        self.legacy_fallback = True
        print("🔗 Controller Bridge disabled: Using legacy action system")
    
    # ActionManager Interface Implementation
    # These methods make this bridge compatible with ActionManager expectations
    
    @property
    def game_controller(self):
        """Provide game_controller property for ActionManager compatibility."""
        return self
    
    def get_unit(self, unit_id: str):
        """Get unit by ID - bridges to original controller."""
        controller = self.original_controller()
        if controller and hasattr(controller, 'units'):
            # Handle both dict and list unit storage
            if isinstance(controller.units, dict):
                return controller.units.get(unit_id)
            elif isinstance(controller.units, list):
                for unit in controller.units:
                    if getattr(unit, 'id', None) == unit_id:
                        return unit
        return None
    
    def get_all_units(self) -> List[Any]:
        """Get all units - bridges to original controller."""
        controller = self.original_controller()
        if controller and hasattr(controller, 'units'):
            if isinstance(controller.units, dict):
                return list(controller.units.values())
            elif isinstance(controller.units, list):
                return controller.units
        return []
    
    def get_units_at_position(self, x: int, y: int) -> List[Any]:
        """Get units at specific grid position."""
        units_at_pos = []
        for unit in self.get_all_units():
            if hasattr(unit, 'x') and hasattr(unit, 'y'):
                if unit.x == x and unit.y == y:
                    units_at_pos.append(unit)
        return units_at_pos
    
    def is_position_valid(self, x: int, y: int) -> bool:
        """Check if position is valid on the grid."""
        controller = self.original_controller()
        if controller and hasattr(controller, 'grid'):
            grid = controller.grid
            return (0 <= x < getattr(grid, 'width', 10) and 
                   0 <= y < getattr(grid, 'height', 10))
        return True  # Default assumption
    
    def move_unit(self, unit_id: str, target_x: int, target_y: int) -> bool:
        """Move unit to target position."""
        controller = self.original_controller()
        unit = self.get_unit(unit_id)
        
        if not unit or not controller:
            return False
        
        # Check if position is valid and not occupied
        if not self.is_position_valid(target_x, target_y):
            return False
        
        # Check for collisions with other units
        units_at_target = self.get_units_at_position(target_x, target_y)
        if units_at_target and any(u != unit for u in units_at_target):
            return False
        
        # Perform the move
        if hasattr(unit, 'x') and hasattr(unit, 'y'):
            old_x, old_y = unit.x, unit.y
            unit.x = target_x
            unit.y = target_y
            
            # Update visual representation if available
            if hasattr(controller, 'update_unit_positions'):
                controller.update_unit_positions()
            
            print(f"🔗 Moved {unit_id} from ({old_x}, {old_y}) to ({target_x}, {target_y})")
            return True
        
        return False
    
    # Bridge Methods for Action Execution
    
    def execute_action_legacy(self, action_name: str, unit_id: str, targets: List[Any]) -> bool:
        """Execute action using legacy controller methods."""
        controller = self.original_controller()
        if not controller:
            return False
        
        unit = self.get_unit(unit_id)
        if not unit:
            return False
        
        # Map new action names to legacy methods
        action_mapping = {
            'attack': 'handle_attack',
            'move': 'handle_movement',
            'magic': 'handle_magic',
            'talent': 'handle_talent'
        }
        
        legacy_method_name = action_mapping.get(action_name.lower())
        if legacy_method_name and hasattr(controller, legacy_method_name):
            legacy_method = getattr(controller, legacy_method_name)
            try:
                # Convert targets to legacy format
                legacy_targets = self._convert_targets_to_legacy(targets)
                result = legacy_method(unit, legacy_targets)
                return result is not False
            except Exception as e:
                print(f"🔗 Legacy action execution failed: {e}")
                return False
        
        print(f"🔗 Unknown legacy action: {action_name}")
        return False
    
    def execute_action_modern(self, action_id: str, unit_id: str, targets: List[Any]) -> bool:
        """Execute action using modern ActionManager."""
        if not self.action_manager:
            return False
        
        # Queue action for execution
        success = self.action_manager.queue_action(unit_id, action_id, targets)
        
        if success:
            # Process the action immediately for compatibility
            # In full implementation, this would be handled by turn manager
            print(f"🔗 Action {action_id} queued for {unit_id}")
            return True
        
        return False
    
    def _convert_targets_to_legacy(self, targets: List[Any]) -> List[Any]:
        """Convert modern target format to legacy format."""
        legacy_targets = []
        
        for target in targets:
            if isinstance(target, dict):
                # Position-based target
                if 'x' in target and 'y' in target:
                    legacy_targets.append((target['x'], target['y']))
                else:
                    legacy_targets.append(target)
            else:
                # Direct target
                legacy_targets.append(target)
        
        return legacy_targets
    
    # Main Action Execution Method
    
    def execute_action(self, action_id: str, unit_id: str, targets: List[Any]) -> bool:
        """
        Execute action using appropriate system (modern or legacy).
        
        Args:
            action_id: ID of action to execute
            unit_id: ID of unit performing action
            targets: List of targets for the action
            
        Returns:
            True if action executed successfully
        """
        if self.is_bridged and not self.legacy_fallback:
            # Use modern action system
            return self.execute_action_modern(action_id, unit_id, targets)
        else:
            # Use legacy action system
            return self.execute_action_legacy(action_id, unit_id, targets)
    
    # Queue Management Bridge
    
    def queue_action(self, unit_id: str, action_id: str, targets: List[Any]) -> bool:
        """Queue action for later execution."""
        if self.is_bridged and self.action_manager:
            return self.action_manager.queue_action(unit_id, action_id, targets)
        else:
            # Legacy mode: execute immediately
            return self.execute_action(action_id, unit_id, targets)
    
    def get_unit_queue(self, unit_id: str) -> List[Dict[str, Any]]:
        """Get queued actions for a unit."""
        if self.is_bridged and self.action_manager:
            return self.action_manager.get_unit_queue_preview(unit_id)
        else:
            # Legacy mode: no queuing
            return []
    
    def clear_unit_queue(self, unit_id: str) -> bool:
        """Clear all queued actions for a unit."""
        if self.is_bridged and self.action_manager:
            return self.action_manager.clear_unit_queue(unit_id)
        else:
            # Legacy mode: nothing to clear
            return True
    
    # Status and Information Methods
    
    def get_bridge_status(self) -> Dict[str, Any]:
        """Get current bridge status and configuration."""
        controller = self.original_controller()
        
        status = {
            'bridged': self.is_bridged,
            'legacy_fallback': self.legacy_fallback,
            'action_manager_enabled': FeatureFlags.USE_ACTION_MANAGER,
            'action_manager_available': self.action_manager is not None,
            'original_controller_available': controller is not None,
            'units_count': len(self.get_all_units())
        }
        
        if self.action_manager:
            status['action_statistics'] = self.action_manager.get_action_statistics()
        
        return status
    
    def print_bridge_status(self):
        """Print current bridge status for debugging."""
        status = self.get_bridge_status()
        
        print("🔗 CONTROLLER BRIDGE STATUS")
        print("-" * 40)
        print(f"  Bridged Mode: {'✅' if status['bridged'] else '❌'}")
        print(f"  Legacy Fallback: {'⚠️' if status['legacy_fallback'] else '✅'}")
        print(f"  ActionManager: {'✅' if status['action_manager_available'] else '❌'}")
        print(f"  Original Controller: {'✅' if status['original_controller_available'] else '❌'}")
        print(f"  Units Available: {status['units_count']}")
        
        if 'action_statistics' in status:
            stats = status['action_statistics']
            print(f"  Registered Actions: {stats.get('registered_actions', 0)}")
            print(f"  Queued Actions: {stats.get('total_queued_actions', 0)}")
    
    # Event Delegation
    
    def emit_event(self, event_type: str, data: Any):
        """Emit event through appropriate system."""
        if self.is_bridged and self.action_manager:
            # Use modern event system
            if hasattr(self.action_manager, 'event_bus') and self.action_manager.event_bus:
                self.action_manager.event_bus.emit(event_type, data)
        else:
            # Legacy mode: direct method calls
            controller = self.original_controller()
            if controller:
                # Map events to legacy method calls
                event_mapping = {
                    'unit_moved': 'update_unit_positions',
                    'unit_health_changed': 'on_unit_hp_changed',
                    'turn_ended': 'end_current_turn'
                }
                
                method_name = event_mapping.get(event_type)
                if method_name and hasattr(controller, method_name):
                    method = getattr(controller, method_name)
                    try:
                        method(data)
                    except Exception as e:
                        print(f"🔗 Legacy event handling failed: {e}")
    
    # Cleanup
    
    def shutdown(self):
        """Shutdown bridge and clean up resources."""
        if self.action_manager:
            self.action_manager.shutdown()
        
        self.is_bridged = False
        self.legacy_fallback = True
        print("🔗 Controller Bridge shut down")


def create_controller_bridge(original_controller) -> ControllerBridge:
    """
    Create and configure controller bridge for seamless integration.
    
    Args:
        original_controller: Original TacticalRPG controller instance
        
    Returns:
        Configured ControllerBridge instance
    """
    bridge = ControllerBridge(original_controller)
    
    # Enable bridge if action manager is available
    if FeatureFlags.USE_ACTION_MANAGER:
        success = bridge.enable_bridge()
        if success:
            print("🔗 Controller bridge created and enabled")
        else:
            print("🔗 Controller bridge created in legacy mode")
    else:
        print("🔗 Controller bridge created in legacy-only mode")
    
    return bridge