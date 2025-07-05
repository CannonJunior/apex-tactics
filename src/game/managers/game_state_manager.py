"""
Game State Manager

Handles core game state management including:
- Active unit tracking and selection
- Turn management and battle flow  
- Game mode coordination (move/attack/magic/normal)
- Unit lifecycle management
- Battle setup and teardown

Extracted from monolithic TacticalRPG controller for better modularity.
"""

from typing import List, Optional, Dict, Any, Callable
from enum import Enum

from core.ecs.world import World
from core.models.unit import Unit
from core.models.unit_types import UnitType
from core.game.turn_manager import TurnManager
from core.game.battle_grid import BattleGrid
from ui.visual.unit_renderer import UnitEntity
from ui.battlefield.grid_tile import GridTile


class GameMode(Enum):
    """Game interaction modes"""
    NORMAL = "normal"
    MOVE = "move"
    ATTACK = "attack"
    MAGIC = "magic"
    TALENT = "talent"


class GameStateManager:
    """
    Manages core game state including units, turns, and battle flow.
    
    This module handles the fundamental game state that was previously
    managed by the monolithic TacticalRPG controller.
    """
    
    def __init__(self, world: World):
        """Initialize the game state manager."""
        self.world = world
        
        # Core game state
        self.active_unit: Optional[Unit] = None
        self.current_mode: GameMode = GameMode.NORMAL
        self.battle_active: bool = False
        
        # Unit management
        self.units: List[Unit] = []
        self.unit_entities: List[UnitEntity] = []
        self.tile_entities: List[GridTile] = []
        
        # Path and targeting state
        self.current_path: List[tuple] = []
        self.path_cursor: Optional[tuple] = None
        self.targeted_units: List[Unit] = []
        
        # Battle systems
        self.grid: Optional[BattleGrid] = None
        self.turn_manager: Optional[TurnManager] = None
        
        # Event callbacks
        self.on_active_unit_changed: List[Callable] = []
        self.on_mode_changed: List[Callable] = []
        self.on_turn_ended: List[Callable] = []
        self.on_battle_state_changed: List[Callable] = []
        
        print("✅ GameStateManager initialized")
    
    def setup_battle(self, grid_width: int = 10, grid_height: int = 8):
        """Initialize battle with grid and default units."""
        try:
            # Initialize battle grid
            self.grid = BattleGrid(grid_width, grid_height)
            
            # Initialize turn manager with empty units list (will add units later)
            self.turn_manager = TurnManager([])
            
            # Create visual grid tiles for mouse interaction
            self._create_grid_tiles(grid_width, grid_height)
            
            # Create default units for testing
            self._create_default_units()
            
            # Create visual unit entities
            self._create_unit_entities()
            
            # Setup battle state
            self.battle_active = True
            self._notify_battle_state_changed()
            
            print(f"✅ Battle setup complete: {len(self.units)} units on {grid_width}x{grid_height} grid")
            print(f"✅ Created {len(self.tile_entities)} grid tiles and {len(self.unit_entities)} unit entities")
            return True
            
        except Exception as e:
            print(f"❌ Battle setup failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _create_default_units(self):
        """Create default units for battle testing."""
        # Create player units
        player_units = [
            Unit("Hero", UnitType.HEROMANCER, 1, 1),
            Unit("Sage", UnitType.MAGI, 2, 1)
        ]
        
        # Create enemy units  
        enemy_units = [
            Unit("Orc", UnitType.UBERMENSCH, 6, 6),
            Unit("Spirit", UnitType.REALM_WALKER, 5, 6)
        ]
        
        # Combine all units
        self.units = player_units + enemy_units
        
        # Add units to grid and turn manager
        for unit in self.units:
            if self.grid:
                self.grid.add_unit(unit)
        
        # Reinitialize turn manager with units
        if self.turn_manager:
            self.turn_manager = TurnManager(self.units)
        
        print(f"✅ Created {len(self.units)} default units")
    
    def _create_grid_tiles(self, width: int, height: int):
        """Create visual grid tiles for mouse interaction."""
        self.tile_entities = []
        
        # We need a reference to the game controller for GridTile
        # For now, we'll pass None and update this when we have proper reference
        for x in range(width):
            for y in range(height):
                self.tile_entities.append(GridTile(x, y, None))
        
        print(f"✅ Created {len(self.tile_entities)} grid tiles")
    
    def _create_unit_entities(self):
        """Create visual unit entities for all units."""
        self.unit_entities = []
        
        for unit in self.units:
            # Set a temporary game controller reference
            unit._game_controller = None  # Will be set by the modular controller
            self.unit_entities.append(UnitEntity(unit))
        
        print(f"✅ Created {len(self.unit_entities)} unit entities")
    
    def set_game_controller_reference(self, controller):
        """Set the game controller reference for units and tiles."""
        # Update tile entities with controller reference
        for tile in self.tile_entities:
            tile.game_controller = controller
        
        # Update unit controller references
        for unit in self.units:
            unit._game_controller = controller
        
        print(f"✅ Updated controller references for {len(self.tile_entities)} tiles and {len(self.units)} units")
    
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
            # Unit selected - reset path and mode
            self.current_path = []
            self.path_cursor = (unit.x, unit.y)
            self.current_mode = GameMode.NORMAL
            
            print(f"👤 Active unit set: {unit.name} at ({unit.x}, {unit.y})")
        else:
            # Unit deselected - clear state
            self.current_path = []
            self.path_cursor = None
            self.current_mode = GameMode.NORMAL
            
            print("👤 Active unit cleared")
        
        # Notify listeners of unit change
        self._notify_active_unit_changed(old_unit, unit, context or {})
    
    def clear_active_unit(self):
        """Clear the active unit selection."""
        self.set_active_unit(None)
    
    def set_mode(self, mode: GameMode, context: Dict[str, Any] = None):
        """
        Set the current game interaction mode.
        
        Args:
            mode: New interaction mode
            context: Additional context for the mode change
        """
        old_mode = self.current_mode
        self.current_mode = mode
        
        print(f"🎮 Mode changed: {old_mode.value} → {mode.value}")
        
        # Notify listeners of mode change
        self._notify_mode_changed(old_mode, mode, context or {})
    
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
            self.current_mode = GameMode.NORMAL
            
            # Advance turn
            self.turn_manager.next_turn()
            
            # Get new current unit
            current_unit = self.turn_manager.current_unit()
            if current_unit:
                # Auto-select new current unit
                self.set_active_unit(current_unit, {"auto_selected": True})
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
    
    def get_current_mode(self) -> GameMode:
        """Get the current interaction mode."""
        return self.current_mode
    
    def get_units(self) -> List[Unit]:
        """Get all units in the battle."""
        return self.units.copy()
    
    def get_unit_at_position(self, x: int, y: int) -> Optional[Unit]:
        """Get unit at the specified grid position."""
        if self.grid:
            return self.grid.units.get((x, y))
        return None
    
    def is_battle_active(self) -> bool:
        """Check if a battle is currently active."""
        return self.battle_active
    
    def get_battle_state(self) -> Dict[str, Any]:
        """Get comprehensive battle state information."""
        return {
            "battle_active": self.battle_active,
            "active_unit": self.active_unit.name if self.active_unit else None,
            "current_mode": self.current_mode.value,
            "unit_count": len(self.units),
            "current_turn": self.turn_manager.current_turn if self.turn_manager else 0,
            "path_length": len(self.current_path),
            "targeted_units": len(self.targeted_units)
        }
    
    # Event system for module coordination
    def add_active_unit_listener(self, callback: Callable):
        """Add listener for active unit changes."""
        self.on_active_unit_changed.append(callback)
    
    def add_mode_listener(self, callback: Callable):
        """Add listener for mode changes."""
        self.on_mode_changed.append(callback)
    
    def add_turn_listener(self, callback: Callable):
        """Add listener for turn end events."""
        self.on_turn_ended.append(callback)
    
    def add_battle_state_listener(self, callback: Callable):
        """Add listener for battle state changes."""
        self.on_battle_state_changed.append(callback)
    
    def _notify_active_unit_changed(self, old_unit: Optional[Unit], new_unit: Optional[Unit], context: Dict[str, Any]):
        """Notify listeners of active unit change."""
        for callback in self.on_active_unit_changed:
            try:
                callback(old_unit, new_unit, context)
            except Exception as e:
                print(f"⚠️ Error in active unit listener: {e}")
    
    def _notify_mode_changed(self, old_mode: GameMode, new_mode: GameMode, context: Dict[str, Any]):
        """Notify listeners of mode change."""
        for callback in self.on_mode_changed:
            try:
                callback(old_mode, new_mode, context)
            except Exception as e:
                print(f"⚠️ Error in mode listener: {e}")
    
    def _notify_turn_ended(self):
        """Notify listeners of turn end."""
        for callback in self.on_turn_ended:
            try:
                callback()
            except Exception as e:
                print(f"⚠️ Error in turn listener: {e}")
    
    def _notify_battle_state_changed(self):
        """Notify listeners of battle state change."""
        for callback in self.on_battle_state_changed:
            try:
                callback(self.battle_active)
            except Exception as e:
                print(f"⚠️ Error in battle state listener: {e}")
    
    def shutdown(self):
        """Clean shutdown of the game state manager."""
        self.battle_active = False
        self.clear_active_unit()
        self.units.clear()
        self.unit_entities.clear()
        self.tile_entities.clear()
        
        # Clear event listeners
        self.on_active_unit_changed.clear()
        self.on_mode_changed.clear()
        self.on_turn_ended.clear()
        self.on_battle_state_changed.clear()
        
        print("✅ GameStateManager shutdown complete")