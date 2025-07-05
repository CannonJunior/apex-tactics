"""
Apex Tactics Game State Manager

Extracted from apex_tactics_controller.py to manage core game state.
Handles unit selection, modes, paths, and battle state for the tactical RPG.
"""

from typing import List, Optional, Tuple, Dict, Any, Callable
from enum import Enum

from core.ecs.world import World
from core.models.unit import Unit
from core.game.battle_grid import BattleGrid
from core.game.turn_manager import TurnManager
from ui.visual.unit_renderer import UnitEntity


class GameMode(Enum):
    """Game interaction modes"""
    NORMAL = "normal"
    MOVE = "move"
    ATTACK = "attack"
    MAGIC = "magic"
    TALENT = "talent"


class ApexGameStateManager:
    """
    Manages core game state for Apex Tactics tactical RPG.
    
    Extracted from the monolithic apex_tactics_controller.py to provide
    modular game state management including:
    - Active unit selection and management
    - Game mode tracking (move, attack, magic, etc.)
    - Path selection and movement tracking
    - Target selection for attacks/magic
    - Battle state management
    """
    
    def __init__(self, world: World):
        """Initialize the game state manager."""
        self.world = world
        
        # Core game state
        self.active_unit: Optional[Unit] = None
        self.current_mode: Optional[str] = None  # Track current action mode: 'move', 'attack', etc.
        self.battle_active: bool = False
        
        # Unit management
        self.units: List[Unit] = []
        self.unit_entities: List[UnitEntity] = []
        self.tile_entities: List[Any] = []  # Grid tiles for mouse interaction
        
        # Path and targeting state
        self.current_path: List[Tuple[int, int]] = []  # Track the selected movement path
        self.path_cursor: Optional[Tuple[int, int]] = None  # Current position in path selection
        self.targeted_units: List[Unit] = []  # List of units targeted for effects
        
        # Attack targeting
        self.attack_target_tile: Optional[Tuple[int, int]] = None  # Currently targeted attack tile
        self.attack_modal_from_double_click: bool = False  # Track if attack modal was triggered by double-click
        
        # Magic targeting
        self.magic_target_tile: Optional[Tuple[int, int]] = None  # Currently targeted magic tile
        self.magic_modal_from_double_click: bool = False  # Track if magic modal was triggered by double-click
        
        # Battle systems
        self.grid: Optional[BattleGrid] = None
        self.turn_manager: Optional[TurnManager] = None
        
        # Modal references
        self.movement_modal: Optional[Any] = None  # Reference to movement confirmation modal
        self.action_modal: Optional[Any] = None  # Reference to action selection modal
        self.attack_modal: Optional[Any] = None  # Reference to attack confirmation modal
        self.magic_modal: Optional[Any] = None  # Reference to magic confirmation modal
        
        # Event callbacks
        self.on_active_unit_changed: List[Callable] = []
        self.on_mode_changed: List[Callable] = []
        self.on_path_changed: List[Callable] = []
        self.on_targeting_changed: List[Callable] = []
        self.on_battle_state_changed: List[Callable] = []
        self.on_turn_ended: List[Callable] = []
        
        print("✅ ApexGameStateManager initialized")
    
    def set_active_unit(self, unit: Optional[Unit], context: Dict[str, Any] = None):
        """
        Set the active unit with proper state management.
        
        Args:
            unit: Unit to set as active, or None to clear
            context: Additional context for the selection
        """
        old_unit = self.active_unit
        self.active_unit = unit
        
        if unit is not None:
            # Unit selected - initialize cursor and reset mode
            self.path_cursor = (unit.x, unit.y)
            self.current_mode = None
            
            # Clear any existing paths and targets
            self.current_path = []
            self.targeted_units = []
            self.attack_target_tile = None
            self.magic_target_tile = None
            
            print(f"👤 Active unit set: {unit.name} at ({unit.x}, {unit.y})")
        else:
            # Unit deselected - clear all state
            self.path_cursor = None
            self.current_mode = None
            self.current_path = []
            self.targeted_units = []
            self.attack_target_tile = None
            self.magic_target_tile = None
            
            print("👤 Active unit cleared")
        
        # Notify listeners of unit change
        self._notify_active_unit_changed(old_unit, unit, context or {})
    
    def clear_active_unit(self):
        """Clear the active unit selection."""
        self.set_active_unit(None)
    
    def set_mode(self, mode: str, context: Dict[str, Any] = None):
        """
        Set the current game interaction mode.
        
        Args:
            mode: New interaction mode ('move', 'attack', 'magic', etc.)
            context: Additional context for the mode change
        """
        old_mode = self.current_mode
        self.current_mode = mode
        
        # Clear mode-specific state when changing modes
        if old_mode != mode:
            if old_mode == "move":
                self.current_path = []
            elif old_mode == "attack":
                self.attack_target_tile = None
                self.targeted_units = []
            elif old_mode == "magic":
                self.magic_target_tile = None
                self.targeted_units = []
        
        print(f"🎮 Mode changed: {old_mode} → {mode}")
        
        # Notify listeners of mode change
        self._notify_mode_changed(old_mode, mode, context or {})
    
    def clear_mode(self):
        """Clear the current mode back to normal."""
        self.set_mode(None)
    
    def set_path_cursor(self, position: Optional[Tuple[int, int]]):
        """
        Set the current path cursor position.
        
        Args:
            position: New cursor position or None to clear
        """
        old_position = self.path_cursor
        self.path_cursor = position
        
        if position:
            print(f"🎯 Path cursor set to ({position[0]}, {position[1]})")
        else:
            print("🎯 Path cursor cleared")
        
        # Notify listeners of path change
        self._notify_path_changed(old_position, position)
    
    def add_to_path(self, position: Tuple[int, int]):
        """
        Add a position to the current movement path.
        
        Args:
            position: Position to add to path
        """
        if position not in self.current_path:
            self.current_path.append(position)
            print(f"📍 Added ({position[0]}, {position[1]}) to path. Path length: {len(self.current_path)}")
            self._notify_path_changed(None, position)
    
    def clear_path(self):
        """Clear the current movement path."""
        if self.current_path:
            self.current_path = []
            print("📍 Movement path cleared")
            self._notify_path_changed(None, None)
    
    def set_targeted_units(self, units: List[Unit]):
        """
        Set the list of units targeted for effects.
        
        Args:
            units: List of units to target
        """
        old_targets = self.targeted_units.copy()
        self.targeted_units = units
        
        if units:
            unit_names = [unit.name for unit in units]
            print(f"🎯 Targeted units: {unit_names}")
        else:
            print("🎯 Targeting cleared")
        
        # Notify listeners of targeting change
        self._notify_targeting_changed(old_targets, units)
    
    def clear_targeted_units(self):
        """Clear all targeted units."""
        self.set_targeted_units([])
    
    def add_targeted_unit(self, unit: Unit):
        """
        Add a unit to the targeted units list.
        
        Args:
            unit: Unit to add to targeting
        """
        if unit not in self.targeted_units:
            self.targeted_units.append(unit)
            print(f"🎯 Added {unit.name} to targets. Total targets: {len(self.targeted_units)}")
            self._notify_targeting_changed([], self.targeted_units)
    
    def remove_targeted_unit(self, unit: Unit):
        """
        Remove a unit from the targeted units list.
        
        Args:
            unit: Unit to remove from targeting
        """
        if unit in self.targeted_units:
            old_targets = self.targeted_units.copy()
            self.targeted_units.remove(unit)
            print(f"🎯 Removed {unit.name} from targets. Total targets: {len(self.targeted_units)}")
            self._notify_targeting_changed(old_targets, self.targeted_units)
    
    def set_attack_target(self, tile: Optional[Tuple[int, int]], from_double_click: bool = False):
        """
        Set the attack target tile.
        
        Args:
            tile: Target tile coordinates or None to clear
            from_double_click: Whether this was triggered by double-click
        """
        self.attack_target_tile = tile
        self.attack_modal_from_double_click = from_double_click
        
        if tile:
            print(f"⚔️ Attack target set to ({tile[0]}, {tile[1]})")
        else:
            print("⚔️ Attack target cleared")
    
    def clear_attack_target(self):
        """Clear the attack target."""
        self.set_attack_target(None)
    
    def set_magic_target(self, tile: Optional[Tuple[int, int]], from_double_click: bool = False):
        """
        Set the magic target tile.
        
        Args:
            tile: Target tile coordinates or None to clear
            from_double_click: Whether this was triggered by double-click
        """
        self.magic_target_tile = tile
        self.magic_modal_from_double_click = from_double_click
        
        if tile:
            print(f"✨ Magic target set to ({tile[0]}, {tile[1]})")
        else:
            print("✨ Magic target cleared")
    
    def clear_magic_target(self):
        """Clear the magic target."""
        self.set_magic_target(None)
    
    def setup_battle(self, grid: BattleGrid, units: List[Unit], turn_manager: TurnManager):
        """
        Initialize battle with provided systems.
        
        Args:
            grid: Battle grid instance
            units: List of units in battle
            turn_manager: Turn manager instance
        """
        self.grid = grid
        self.units = units
        self.turn_manager = turn_manager
        self.battle_active = True
        
        print(f"✅ Battle setup complete: {len(units)} units on grid")
        self._notify_battle_state_changed()
    
    def end_battle(self):
        """End the current battle and clear state."""
        self.battle_active = False
        self.clear_active_unit()
        self.clear_mode()
        self.clear_path()
        self.clear_targeted_units()
        self.clear_attack_target()
        self.clear_magic_target()
        
        print("✅ Battle ended, state cleared")
        self._notify_battle_state_changed()
    
    def end_current_turn(self) -> bool:
        """
        End the current unit's turn and advance to next.
        
        Returns:
            True if turn ended successfully
        """
        if not self.turn_manager:
            print("⚠️ No turn manager available")
            return False
        
        try:
            # Clear current state
            self.clear_active_unit()
            self.clear_mode()
            self.clear_path()
            self.clear_targeted_units()
            self.clear_attack_target()
            self.clear_magic_target()
            
            # Advance turn
            self.turn_manager.next_turn()
            
            # Get new current unit
            current_unit = self.turn_manager.current_unit()
            if current_unit:
                # Auto-select new current unit
                self.set_active_unit(current_unit, {"auto_selected": True, "new_turn": True})
                print(f"🔄 Turn ended. Now it's {current_unit.name}'s turn")
            
            # Notify listeners
            self._notify_turn_ended()
            return True
            
        except Exception as e:
            print(f"❌ Turn end failed: {e}")
            return False
    
    def refresh_all_ap(self):
        """Reset action points for all units."""
        for unit in self.units:
            unit.ap = unit.max_ap
            unit.current_move_points = unit.move_points
        
        print("🔄 Action points refreshed for all units")
    
    def get_active_unit(self) -> Optional[Unit]:
        """Get the currently active unit."""
        return self.active_unit
    
    def get_current_mode(self) -> Optional[str]:
        """Get the current interaction mode."""
        return self.current_mode
    
    def get_path_cursor(self) -> Optional[Tuple[int, int]]:
        """Get the current path cursor position."""
        return self.path_cursor
    
    def get_current_path(self) -> List[Tuple[int, int]]:
        """Get the current movement path."""
        return self.current_path.copy()
    
    def get_targeted_units(self) -> List[Unit]:
        """Get the list of targeted units."""
        return self.targeted_units.copy()
    
    def get_attack_target(self) -> Optional[Tuple[int, int]]:
        """Get the current attack target tile."""
        return self.attack_target_tile
    
    def get_magic_target(self) -> Optional[Tuple[int, int]]:
        """Get the current magic target tile."""
        return self.magic_target_tile
    
    def is_battle_active(self) -> bool:
        """Check if a battle is currently active."""
        return self.battle_active
    
    def is_in_mode(self, mode: str) -> bool:
        """Check if currently in the specified mode."""
        return self.current_mode == mode
    
    def has_active_unit(self) -> bool:
        """Check if there is an active unit selected."""
        return self.active_unit is not None
    
    def has_path_cursor(self) -> bool:
        """Check if there is a path cursor set."""
        return self.path_cursor is not None
    
    def has_path(self) -> bool:
        """Check if there is a movement path set."""
        return len(self.current_path) > 0
    
    def has_targeted_units(self) -> bool:
        """Check if there are units targeted."""
        return len(self.targeted_units) > 0
    
    def get_battle_state(self) -> Dict[str, Any]:
        """Get comprehensive battle state information."""
        return {
            "battle_active": self.battle_active,
            "active_unit": self.active_unit.name if self.active_unit else None,
            "current_mode": self.current_mode,
            "unit_count": len(self.units),
            "path_cursor": self.path_cursor,
            "path_length": len(self.current_path),
            "targeted_units": len(self.targeted_units),
            "attack_target": self.attack_target_tile,
            "magic_target": self.magic_target_tile,
            "has_movement_modal": self.movement_modal is not None,
            "has_attack_modal": self.attack_modal is not None,
            "has_magic_modal": self.magic_modal is not None
        }
    
    # Modal management
    def set_movement_modal(self, modal: Any):
        """Set reference to movement confirmation modal."""
        self.movement_modal = modal
    
    def clear_movement_modal(self):
        """Clear movement modal reference."""
        self.movement_modal = None
    
    def set_action_modal(self, modal: Any):
        """Set reference to action selection modal."""
        self.action_modal = modal
    
    def clear_action_modal(self):
        """Clear action modal reference."""
        self.action_modal = None
    
    def set_attack_modal(self, modal: Any):
        """Set reference to attack confirmation modal."""
        self.attack_modal = modal
    
    def clear_attack_modal(self):
        """Clear attack modal reference."""
        self.attack_modal = None
    
    def set_magic_modal(self, modal: Any):
        """Set reference to magic confirmation modal."""
        self.magic_modal = modal
    
    def clear_magic_modal(self):
        """Clear magic modal reference."""
        self.magic_modal = None
    
    # Event system for module coordination
    def add_active_unit_listener(self, callback: Callable):
        """Add listener for active unit changes."""
        self.on_active_unit_changed.append(callback)
    
    def add_mode_listener(self, callback: Callable):
        """Add listener for mode changes."""
        self.on_mode_changed.append(callback)
    
    def add_path_listener(self, callback: Callable):
        """Add listener for path changes."""
        self.on_path_changed.append(callback)
    
    def add_targeting_listener(self, callback: Callable):
        """Add listener for targeting changes."""
        self.on_targeting_changed.append(callback)
    
    def add_battle_state_listener(self, callback: Callable):
        """Add listener for battle state changes."""
        self.on_battle_state_changed.append(callback)
    
    def add_turn_listener(self, callback: Callable):
        """Add listener for turn end events."""
        self.on_turn_ended.append(callback)
    
    def _notify_active_unit_changed(self, old_unit: Optional[Unit], new_unit: Optional[Unit], context: Dict[str, Any]):
        """Notify listeners of active unit change."""
        for callback in self.on_active_unit_changed:
            try:
                callback(old_unit, new_unit, context)
            except Exception as e:
                print(f"⚠️ Error in active unit listener: {e}")
    
    def _notify_mode_changed(self, old_mode: Optional[str], new_mode: Optional[str], context: Dict[str, Any]):
        """Notify listeners of mode change."""
        for callback in self.on_mode_changed:
            try:
                callback(old_mode, new_mode, context)
            except Exception as e:
                print(f"⚠️ Error in mode listener: {e}")
    
    def _notify_path_changed(self, old_position: Optional[Tuple[int, int]], new_position: Optional[Tuple[int, int]]):
        """Notify listeners of path change."""
        for callback in self.on_path_changed:
            try:
                callback(old_position, new_position)
            except Exception as e:
                print(f"⚠️ Error in path listener: {e}")
    
    def _notify_targeting_changed(self, old_targets: List[Unit], new_targets: List[Unit]):
        """Notify listeners of targeting change."""
        for callback in self.on_targeting_changed:
            try:
                callback(old_targets, new_targets)
            except Exception as e:
                print(f"⚠️ Error in targeting listener: {e}")
    
    def _notify_battle_state_changed(self):
        """Notify listeners of battle state change."""
        for callback in self.on_battle_state_changed:
            try:
                callback(self.battle_active)
            except Exception as e:
                print(f"⚠️ Error in battle state listener: {e}")
    
    def _notify_turn_ended(self):
        """Notify listeners of turn end."""
        for callback in self.on_turn_ended:
            try:
                callback()
            except Exception as e:
                print(f"⚠️ Error in turn listener: {e}")
    
    def shutdown(self):
        """Clean shutdown of the game state manager."""
        self.end_battle()
        
        # Clear references
        self.units.clear()
        self.unit_entities.clear()
        self.tile_entities.clear()
        self.grid = None
        self.turn_manager = None
        
        # Clear modals
        self.movement_modal = None
        self.action_modal = None
        self.attack_modal = None
        self.magic_modal = None
        
        # Clear event listeners
        self.on_active_unit_changed.clear()
        self.on_mode_changed.clear()
        self.on_path_changed.clear()
        self.on_targeting_changed.clear()
        self.on_battle_state_changed.clear()
        self.on_turn_ended.clear()
        
        print("✅ ApexGameStateManager shutdown complete")