"""
Interactive Tile System

Enhanced tile system with proper click detection, visual feedback, and state management.
Based on patterns from the apex-tactics implementation.
Includes batch update optimizations for performance.
"""

from typing import Optional, Callable, Any, List, Dict, Set
from enum import Enum
from collections import defaultdict

try:
    from ursina import Entity, color, Vec3
    URSINA_AVAILABLE = True
except ImportError:
    URSINA_AVAILABLE = False

from core.math.vector import Vector2Int, Vector3


class TileState(Enum):
    """Visual states for interactive tiles"""
    NORMAL = "normal"
    HIGHLIGHTED = "highlighted"
    SELECTED = "selected"
    MOVEMENT_RANGE = "movement_range"
    ATTACK_RANGE = "attack_range"
    EFFECT_AREA = "effect_area"
    INVALID = "invalid"
    HOVERED = "hovered"


class InteractiveTile:
    """
    Enhanced tile with click detection and visual feedback.
    
    Provides proper mouse interaction, state management, and visual feedback
    for tactical grid tiles.
    """
    
    def __init__(self, grid_pos: Vector2Int, world_pos: Vector3, 
                 tile_size: float = 1.0, on_click: Optional[Callable] = None):
        if not URSINA_AVAILABLE:
            raise ImportError("Ursina is required for InteractiveTile")
        
        self.grid_pos = grid_pos
        self.world_pos = world_pos
        self.tile_size = tile_size
        self.on_click_callback = on_click
        
        # Visual state
        self.current_state = TileState.NORMAL
        self.is_hovered = False
        self.is_occupied = False
        self.occupant = None
        
        # Color configuration
        self.state_colors = {
            TileState.NORMAL: color.light_gray,
            TileState.HIGHLIGHTED: color.yellow,
            TileState.SELECTED: color.white,
            TileState.MOVEMENT_RANGE: color.green,
            TileState.ATTACK_RANGE: color.red,
            TileState.EFFECT_AREA: color.orange,
            TileState.INVALID: color.dark_gray,
            TileState.HOVERED: color.cyan
        }
        
        # Create Ursina entity
        self._create_visual_entity()
        
        # Interaction data
        self.interaction_data = {}
    
    def _create_visual_entity(self):
        """Create the visual Ursina entity for this tile"""
        self.entity = Entity(
            model='cube',
            color=self.state_colors[TileState.NORMAL],
            scale=(self.tile_size * 0.95, 0.1, self.tile_size * 0.95),
            position=(self.world_pos.x, self.world_pos.y, self.world_pos.z),
            collider='box'  # Enable click detection
        )
        
        # Set up click handling
        self.entity.on_click = self._handle_click
        self.entity.on_mouse_enter = self._handle_mouse_enter
        self.entity.on_mouse_exit = self._handle_mouse_exit
        
        # Store reference to this tile in the entity
        self.entity.tile_reference = self
    
    def _handle_click(self):
        """Handle mouse click on this tile"""
        print(f"Tile clicked at: {self.grid_pos}")
        
        if self.on_click_callback:
            self.on_click_callback(self)
    
    def _handle_mouse_enter(self):
        """Handle mouse entering tile area"""
        self.is_hovered = True
        self._update_visual_state()
    
    def _handle_mouse_exit(self):
        """Handle mouse leaving tile area"""
        self.is_hovered = False
        self._update_visual_state()
    
    def set_state(self, new_state: TileState, use_batch: bool = False):
        """
        Set the visual state of this tile.
        
        Args:
            new_state: New tile state
            use_batch: If True, use batch manager for better performance
        """
        if use_batch:
            batch_manager = get_tile_batch_manager()
            batch_manager.schedule_state_update(self, new_state)
        else:
            self.current_state = new_state
            self._update_visual_state()
    
    def _update_visual_state(self):
        """Update the visual appearance based on current state"""
        if not self.entity:
            return
        
        # Priority order for states (higher priority overrides lower)
        if self.is_hovered and self.current_state != TileState.SELECTED:
            display_color = self.state_colors[TileState.HOVERED]
        else:
            display_color = self.state_colors[self.current_state]
        
        self.entity.color = display_color
    
    def set_occupant(self, occupant: Any):
        """Set the unit/object occupying this tile"""
        self.occupant = occupant
        self.is_occupied = occupant is not None
    
    def clear_occupant(self):
        """Clear the occupant from this tile"""
        self.occupant = None
        self.is_occupied = False
    
    def set_click_callback(self, callback: Callable):
        """Set the callback function for tile clicks"""
        self.on_click_callback = callback
    
    def set_interaction_data(self, key: str, value: Any):
        """Store arbitrary interaction data"""
        self.interaction_data[key] = value
    
    def get_interaction_data(self, key: str, default: Any = None) -> Any:
        """Retrieve interaction data"""
        return self.interaction_data.get(key, default)
    
    def highlight(self, highlight_color: Any = None, use_batch: bool = False):
        """
        Temporarily highlight this tile.
        
        Args:
            highlight_color: Custom color to use, or None for default highlight
            use_batch: If True, use batch manager for better performance
        """
        if highlight_color:
            if use_batch:
                batch_manager = get_tile_batch_manager()
                batch_manager.schedule_color_update(self, highlight_color)
            else:
                self.entity.color = highlight_color
        else:
            self.set_state(TileState.HIGHLIGHTED, use_batch)
    
    def reset_to_normal(self, use_batch: bool = False):
        """
        Reset tile to normal state.
        
        Args:
            use_batch: If True, use batch manager for better performance
        """
        self.set_state(TileState.NORMAL, use_batch)
    
    @staticmethod
    def batch_set_states(tiles: List['InteractiveTile'], state: TileState):
        """
        Set the same state for multiple tiles using batch processing.
        
        Args:
            tiles: List of tiles to update
            state: State to apply to all tiles
        """
        batch_manager = get_tile_batch_manager()
        batch_manager.schedule_multiple_state_updates(tiles, state)
    
    @staticmethod
    def batch_reset_to_normal(tiles: List['InteractiveTile']):
        """
        Reset multiple tiles to normal state using batch processing.
        
        Args:
            tiles: List of tiles to reset
        """
        InteractiveTile.batch_set_states(tiles, TileState.NORMAL)
    
    @staticmethod
    def apply_pending_batch_updates():
        """Apply all pending batch updates immediately"""
        batch_manager = get_tile_batch_manager()
        batch_manager.force_immediate_update()
    
    def destroy(self):
        """Clean up and destroy this tile"""
        if self.entity:
            try:
                from ursina import destroy
                destroy(self.entity)
            except:
                pass
            self.entity = None
    
    def get_world_position(self) -> Vector3:
        """Get the world position of this tile"""
        return self.world_pos
    
    def get_grid_position(self) -> Vector2Int:
        """Get the grid position of this tile"""
        return self.grid_pos
    
    def is_valid_for_movement(self) -> bool:
        """Check if this tile is valid for unit movement"""
        return (not self.is_occupied and 
                self.current_state != TileState.INVALID)
    
    def is_valid_for_attack(self) -> bool:
        """Check if this tile is valid for attack targeting"""
        return self.current_state != TileState.INVALID
    
    def __str__(self) -> str:
        return f"InteractiveTile({self.grid_pos}, {self.current_state.value})"
    
    def __repr__(self) -> str:
        return self.__str__()


class TileBatchManager:
    """
    Manages batch updates for multiple tiles to reduce individual state change overhead.
    
    Groups tile updates by state and applies them in batches for better performance.
    """
    
    def __init__(self):
        self.pending_updates: Dict[TileState, List[InteractiveTile]] = defaultdict(list)
        self.pending_color_updates: List[tuple] = []  # (tile, color) pairs
        self._update_scheduled = False
    
    def schedule_state_update(self, tile: InteractiveTile, new_state: TileState):
        """
        Schedule a tile state update for batch processing.
        
        Args:
            tile: Tile to update
            new_state: New state to apply
        """
        self.pending_updates[new_state].append(tile)
        self._schedule_batch_update()
    
    def schedule_color_update(self, tile: InteractiveTile, color_value: Any):
        """
        Schedule a direct color update for batch processing.
        
        Args:
            tile: Tile to update
            color_value: Color to apply
        """
        self.pending_color_updates.append((tile, color_value))
        self._schedule_batch_update()
    
    def schedule_multiple_state_updates(self, tiles: List[InteractiveTile], new_state: TileState):
        """
        Schedule multiple tiles for the same state update.
        
        Args:
            tiles: List of tiles to update
            new_state: New state to apply to all tiles
        """
        self.pending_updates[new_state].extend(tiles)
        self._schedule_batch_update()
    
    def apply_batch_updates(self):
        """Apply all pending updates in a single batch operation"""
        if not self.pending_updates and not self.pending_color_updates:
            return
        
        # Apply state updates grouped by state
        for state, tiles in self.pending_updates.items():
            self._apply_state_batch(tiles, state)
        
        # Apply direct color updates
        for tile, color_value in self.pending_color_updates:
            if tile.entity:
                tile.entity.color = color_value
        
        # Clear pending updates
        self.pending_updates.clear()
        self.pending_color_updates.clear()
        self._update_scheduled = False
    
    def _apply_state_batch(self, tiles: List[InteractiveTile], state: TileState):
        """Apply state updates to a batch of tiles"""
        for tile in tiles:
            tile.current_state = state
            # Apply visual update without triggering individual update
            if tile.entity:
                display_color = tile.state_colors[state]
                if tile.is_hovered and state != TileState.SELECTED:
                    display_color = tile.state_colors[TileState.HOVERED]
                tile.entity.color = display_color
    
    def _schedule_batch_update(self):
        """Schedule a batch update for next frame if not already scheduled"""
        if not self._update_scheduled:
            self._update_scheduled = True
            # In a real game loop, this would be scheduled for next frame
            # For now, we'll apply immediately or could use a timer
    
    def force_immediate_update(self):
        """Force immediate application of all pending updates"""
        self.apply_batch_updates()
    
    def clear_pending_updates(self):
        """Clear all pending updates without applying them"""
        self.pending_updates.clear()
        self.pending_color_updates.clear()
        self._update_scheduled = False
    
    def get_pending_count(self) -> int:
        """Get the number of pending updates"""
        state_count = sum(len(tiles) for tiles in self.pending_updates.values())
        return state_count + len(self.pending_color_updates)


# Global batch manager instance
_global_tile_batch_manager = None

def get_tile_batch_manager() -> TileBatchManager:
    """
    Get the global tile batch manager instance.
    
    Returns:
        Global TileBatchManager instance
    """
    global _global_tile_batch_manager
    if _global_tile_batch_manager is None:
        _global_tile_batch_manager = TileBatchManager()
    return _global_tile_batch_manager