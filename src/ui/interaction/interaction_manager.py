"""
Interaction Manager

Central system for managing user interactions, tile selection, and UI state.
Coordinates between tiles, units, modals, and visual feedback systems.
"""

from typing import Dict, List, Optional, Set, Callable, Any
from enum import Enum

try:
    from ursina import Entity, color, held_keys, mouse
    URSINA_AVAILABLE = True
except ImportError:
    URSINA_AVAILABLE = False

from core.ecs.entity import Entity as GameEntity
from core.math.vector import Vector2Int, Vector3
from core.math.grid import TacticalGrid
from core.math.pathfinding import AStarPathfinder

from .interactive_tile import InteractiveTile, TileState
from .action_modal import ActionModal, ActionModalManager, ActionOption
from ui.visual.grid_visualizer import GridVisualizer, HighlightType


class InteractionMode(Enum):
    """Different modes for user interaction"""
    NORMAL = "normal"
    UNIT_SELECTED = "unit_selected"
    MOVEMENT_PLANNING = "movement_planning"
    ATTACK_TARGETING = "attack_targeting"
    ABILITY_TARGETING = "ability_targeting"
    AREA_SELECTION = "area_selection"


class InteractionManager:
    """
    Central manager for all user interactions in the tactical game.
    
    Handles tile selection, unit interactions, visual feedback, and modal management.
    Provides a clean interface for game logic to interact with the UI.
    """
    
    def __init__(self, grid_system: TacticalGrid, pathfinder: AStarPathfinder,
                 grid_visualizer: GridVisualizer):
        if not URSINA_AVAILABLE:
            raise ImportError("Ursina is required for InteractionManager")
        
        self.grid_system = grid_system
        self.pathfinder = pathfinder
        self.grid_visualizer = grid_visualizer
        
        # Interaction state
        self.current_mode = InteractionMode.NORMAL
        self.selected_unit: Optional[GameEntity] = None
        self.selected_tile: Optional[InteractiveTile] = None
        self.hovered_tile: Optional[InteractiveTile] = None
        
        # Tile management
        self.tiles: Dict[Vector2Int, InteractiveTile] = {}
        self.unit_positions: Dict[GameEntity, Vector2Int] = {}
        
        # Modal management
        self.modal_manager = ActionModalManager()
        
        # Path planning
        self.current_path: List[Vector2Int] = []
        self.path_cursor: Optional[Vector2Int] = None
        
        # Event callbacks
        self.event_callbacks: Dict[str, List[Callable]] = {
            'unit_selected': [],
            'tile_clicked': [],
            'unit_moved': [],
            'action_executed': [],
            'mode_changed': []
        }
        
        # Input state
        self.input_enabled = True
        
        # Initialize tiles
        self._create_interactive_tiles()
    
    def _create_interactive_tiles(self):
        """Create interactive tiles for the entire grid"""
        for x in range(self.grid_system.width):
            for y in range(self.grid_system.height):
                grid_pos = Vector2Int(x, y)
                world_pos = self.grid_system.grid_to_world(grid_pos)
                
                tile = InteractiveTile(
                    grid_pos=grid_pos,
                    world_pos=world_pos,
                    tile_size=self.grid_system.cell_size,
                    on_click=self._handle_tile_click
                )
                
                self.tiles[grid_pos] = tile
    
    def _handle_tile_click(self, tile: InteractiveTile):
        """Handle clicks on interactive tiles"""
        if not self.input_enabled:
            return
        
        print(f"Tile clicked: {tile.grid_pos} (Mode: {self.current_mode.value})")
        
        # Update selected tile
        if self.selected_tile:
            self.selected_tile.set_state(TileState.NORMAL)
        
        self.selected_tile = tile
        
        # Handle click based on current mode
        if self.current_mode == InteractionMode.NORMAL:
            self._handle_normal_tile_click(tile)
        elif self.current_mode == InteractionMode.UNIT_SELECTED:
            self._handle_unit_selected_tile_click(tile)
        elif self.current_mode == InteractionMode.MOVEMENT_PLANNING:
            self._handle_movement_planning_click(tile)
        elif self.current_mode == InteractionMode.ATTACK_TARGETING:
            self._handle_attack_targeting_click(tile)
        elif self.current_mode == InteractionMode.ABILITY_TARGETING:
            self._handle_ability_targeting_click(tile)
        
        # Fire tile clicked event
        self._fire_event('tile_clicked', tile)
    
    def _handle_normal_tile_click(self, tile: InteractiveTile):
        """Handle tile clicks in normal mode"""
        # Check if there's a unit on this tile
        unit = self._get_unit_at_tile(tile)
        
        if unit:
            self._select_unit(unit, tile)
        else:
            # Clear any existing selection
            self._clear_selection()
    
    def _handle_unit_selected_tile_click(self, tile: InteractiveTile):
        """Handle tile clicks when a unit is selected"""
        unit = self._get_unit_at_tile(tile)
        
        if unit and unit != self.selected_unit:
            # Select different unit
            self._select_unit(unit, tile)
        elif not unit:
            # Clicked empty tile - show movement options
            self._start_movement_planning(tile)
        else:
            # Clicked same unit - show action modal
            self._show_unit_action_modal(self.selected_unit)
    
    def _handle_movement_planning_click(self, tile: InteractiveTile):
        """Handle tile clicks during movement planning"""
        if self._is_valid_movement_tile(tile):
            self._plan_movement_to_tile(tile)
        else:
            # Invalid tile - cancel movement planning
            self._cancel_movement_planning()
    
    def _handle_attack_targeting_click(self, tile: InteractiveTile):
        """Handle tile clicks during attack targeting"""
        if self._is_valid_attack_target(tile):
            self._show_attack_confirmation(tile)
        else:
            self._cancel_attack_targeting()
    
    def _handle_ability_targeting_click(self, tile: InteractiveTile):
        """Handle tile clicks during ability targeting"""
        if self._is_valid_ability_target(tile):
            self._show_ability_confirmation(tile)
        else:
            self._cancel_ability_targeting()
    
    def _select_unit(self, unit: GameEntity, tile: InteractiveTile):
        """Select a unit and update visual state"""
        # Clear previous selection
        self._clear_selection()
        
        self.selected_unit = unit
        self.selected_tile = tile
        
        # Update tile state
        tile.set_state(TileState.SELECTED)
        
        # Update mode
        self._set_mode(InteractionMode.UNIT_SELECTED)
        
        # Show movement and attack ranges
        self._show_unit_ranges(unit)
        
        # Fire unit selected event
        self._fire_event('unit_selected', unit)
        
        print(f"Unit selected: {unit.id}")
    
    def _clear_selection(self):
        """Clear current selection and reset visual state"""
        if self.selected_tile:
            self.selected_tile.set_state(TileState.NORMAL)
        
        self.selected_unit = None
        self.selected_tile = None
        self.current_path.clear()
        self.path_cursor = None
        
        # Clear all highlights
        self._clear_all_tile_highlights()
        
        # Reset mode
        self._set_mode(InteractionMode.NORMAL)
    
    def _show_unit_ranges(self, unit: GameEntity):
        """Show movement and attack ranges for a unit"""
        unit_pos = self._get_unit_position(unit)
        if not unit_pos:
            return
        
        # Get movement range
        movement_comp = unit.get_component('MovementComponent')
        if movement_comp:
            movement_range = getattr(movement_comp, 'movement_range', 3)
            self._highlight_movement_range(unit_pos, movement_range)
        
        # Get attack range  
        attack_comp = unit.get_component('AttackComponent')
        if attack_comp:
            attack_range = getattr(attack_comp, 'attack_range', 2)
            self._highlight_attack_range(unit_pos, attack_range)
    
    def _highlight_movement_range(self, center: Vector2Int, range_distance: int):
        """Highlight tiles within movement range"""
        for x in range(max(0, center.x - range_distance), 
                      min(self.grid_system.width, center.x + range_distance + 1)):
            for y in range(max(0, center.y - range_distance),
                          min(self.grid_system.height, center.y + range_distance + 1)):
                pos = Vector2Int(x, y)
                distance = abs(pos.x - center.x) + abs(pos.y - center.y)
                
                if distance <= range_distance and distance > 0:
                    tile = self.tiles.get(pos)
                    if tile and self._is_valid_movement_tile(tile):
                        tile.set_state(TileState.MOVEMENT_RANGE)
    
    def _highlight_attack_range(self, center: Vector2Int, range_distance: int):
        """Highlight tiles within attack range"""
        for x in range(max(0, center.x - range_distance),
                      min(self.grid_system.width, center.x + range_distance + 1)):
            for y in range(max(0, center.y - range_distance),
                          min(self.grid_system.height, center.y + range_distance + 1)):
                pos = Vector2Int(x, y)
                distance = abs(pos.x - center.x) + abs(pos.y - center.y)
                
                if distance <= range_distance and distance > 0:
                    tile = self.tiles.get(pos)
                    if tile:
                        # Don't override movement range highlighting
                        if tile.current_state == TileState.NORMAL:
                            tile.set_state(TileState.ATTACK_RANGE)
    
    def _clear_all_tile_highlights(self):
        """Clear highlighting from all tiles"""
        for tile in self.tiles.values():
            if tile.current_state not in [TileState.SELECTED]:
                tile.set_state(TileState.NORMAL)
    
    def _start_movement_planning(self, target_tile: InteractiveTile):
        """Start planning movement to a target tile"""
        if not self.selected_unit:
            return
        
        unit_pos = self._get_unit_position(self.selected_unit)
        if not unit_pos:
            return
        
        # Calculate path
        path_result = self.pathfinder.find_path(unit_pos, target_tile.grid_pos)
        
        if path_result.success and path_result.path:
            self.current_path = path_result.path
            self.path_cursor = target_tile.grid_pos
            self._set_mode(InteractionMode.MOVEMENT_PLANNING)
            
            # Show movement confirmation modal
            self._show_movement_confirmation_modal(path_result.path)
        else:
            print("No valid path found")
    
    def _plan_movement_to_tile(self, target_tile: InteractiveTile):
        """Plan and confirm movement to a specific tile during movement planning mode"""
        if not self.selected_unit:
            return
        
        unit_pos = self._get_unit_position(self.selected_unit)
        if not unit_pos:
            return
        
        # Calculate path to the target tile
        path_result = self.pathfinder.find_path(unit_pos, target_tile.grid_pos)
        
        if path_result.success and path_result.path:
            self.current_path = path_result.path
            self.path_cursor = target_tile.grid_pos
            
            # Show movement confirmation modal
            self._show_movement_confirmation_modal(path_result.path)
        else:
            print("No valid path to selected tile")
            self._cancel_movement_planning()
    
    def _show_unit_action_modal(self, unit: GameEntity):
        """Show action modal for a unit"""
        available_actions = self._get_available_actions(unit)
        action_callbacks = self._create_action_callbacks(unit)
        
        self.modal_manager.show_unit_actions_modal(
            unit=unit,
            available_actions=available_actions,
            action_callbacks=action_callbacks
        )
    
    def _show_movement_confirmation_modal(self, path: List[Vector2Int]):
        """Show movement confirmation modal"""
        def confirm_movement():
            self._execute_movement(path)
        
        self.modal_manager.show_movement_confirmation_modal(
            path=path,
            confirm_callback=confirm_movement
        )
    
    def _get_available_actions(self, unit: GameEntity) -> List[str]:
        """Get list of available actions for a unit"""
        actions = ['move', 'attack']
        
        # Add conditional actions based on unit state
        if hasattr(unit, 'can_use_abilities') and unit.can_use_abilities():
            actions.append('ability')
        
        if hasattr(unit, 'has_items') and unit.has_items():
            actions.append('item')
        
        actions.extend(['defend', 'wait'])
        
        return actions
    
    def _create_action_callbacks(self, unit: GameEntity) -> Dict[str, Callable]:
        """Create callback functions for unit actions"""
        return {
            'move': lambda: self._start_movement_mode(),
            'attack': lambda: self._start_attack_mode(),
            'ability': lambda: self._start_ability_mode(),
            'item': lambda: self._start_item_mode(),
            'defend': lambda: self._execute_defend(unit),
            'wait': lambda: self._execute_wait(unit)
        }
    
    def _start_movement_mode(self):
        """Start movement targeting mode"""
        self._set_mode(InteractionMode.MOVEMENT_PLANNING)
        print("Click on a tile to move to")
    
    def _start_attack_mode(self):
        """Start attack targeting mode"""
        self._set_mode(InteractionMode.ATTACK_TARGETING)
        print("Click on a target to attack")
    
    def _start_ability_mode(self):
        """Start ability targeting mode"""
        self._set_mode(InteractionMode.ABILITY_TARGETING)
        print("Click on a target for ability")
    
    def _start_item_mode(self):
        """Start item usage mode"""
        print("Item usage not implemented yet")
    
    def _execute_movement(self, path: List[Vector2Int]):
        """Execute unit movement along path"""
        if not self.selected_unit or not path:
            return
        
        print(f"Executing movement along path: {path}")
        
        # Move unit to destination
        destination = path[-1]
        old_pos = self._get_unit_position(self.selected_unit)
        
        # Update unit position
        self._set_unit_position(self.selected_unit, destination)
        
        # Fire movement event
        self._fire_event('unit_moved', {
            'unit': self.selected_unit,
            'from': old_pos,
            'to': destination,
            'path': path
        })
        
        # Clear movement planning
        self._cancel_movement_planning()
    
    def _execute_defend(self, unit: GameEntity):
        """Execute defend action"""
        print(f"Unit {unit.id} is defending")
        self._fire_event('action_executed', {'action': 'defend', 'unit': unit})
        self._clear_selection()
    
    def _execute_wait(self, unit: GameEntity):
        """Execute wait action"""
        print(f"Unit {unit.id} is waiting")
        self._fire_event('action_executed', {'action': 'wait', 'unit': unit})
        self._clear_selection()
    
    def _cancel_movement_planning(self):
        """Cancel movement planning mode"""
        self.current_path.clear()
        self.path_cursor = None
        self._set_mode(InteractionMode.UNIT_SELECTED)
    
    def _cancel_attack_targeting(self):
        """Cancel attack targeting mode"""
        self._set_mode(InteractionMode.UNIT_SELECTED)
    
    def _cancel_ability_targeting(self):
        """Cancel ability targeting mode"""
        self._set_mode(InteractionMode.UNIT_SELECTED)
    
    def _set_mode(self, new_mode: InteractionMode):
        """Set the current interaction mode"""
        old_mode = self.current_mode
        self.current_mode = new_mode
        
        print(f"Interaction mode changed: {old_mode.value} -> {new_mode.value}")
        self._fire_event('mode_changed', {'old_mode': old_mode, 'new_mode': new_mode})
    
    def _get_unit_at_tile(self, tile: InteractiveTile) -> Optional[GameEntity]:
        """Get the unit at a specific tile"""
        return tile.occupant if tile.is_occupied else None
    
    def _get_unit_position(self, unit: GameEntity) -> Optional[Vector2Int]:
        """Get the grid position of a unit"""
        return self.unit_positions.get(unit)
    
    def _set_unit_position(self, unit: GameEntity, position: Vector2Int):
        """Set the grid position of a unit"""
        # Clear old position
        old_pos = self.unit_positions.get(unit)
        if old_pos and old_pos in self.tiles:
            self.tiles[old_pos].clear_occupant()
        
        # Set new position
        self.unit_positions[unit] = position
        if position in self.tiles:
            self.tiles[position].set_occupant(unit)
    
    def _is_valid_movement_tile(self, tile: InteractiveTile) -> bool:
        """Check if a tile is valid for movement"""
        return tile.is_valid_for_movement()
    
    def _is_valid_attack_target(self, tile: InteractiveTile) -> bool:
        """Check if a tile is a valid attack target"""
        return tile.is_valid_for_attack() and tile.is_occupied
    
    def _is_valid_ability_target(self, tile: InteractiveTile) -> bool:
        """Check if a tile is a valid ability target"""
        return tile.is_valid_for_attack()
    
    def _show_attack_confirmation(self, tile: InteractiveTile):
        """Show attack confirmation modal"""
        target = self._get_unit_at_tile(tile)
        if target:
            def confirm_attack():
                self._execute_attack(target)
            
            self.modal_manager.show_confirmation_modal(
                title="Confirm Attack",
                message=f"Attack {target.id}?",
                confirm_callback=confirm_attack
            )
    
    def _show_ability_confirmation(self, tile: InteractiveTile):
        """Show ability confirmation modal"""
        def confirm_ability():
            self._execute_ability(tile)
        
        self.modal_manager.show_confirmation_modal(
            title="Confirm Ability",
            message="Use ability on this target?",
            confirm_callback=confirm_ability
        )
    
    def _execute_attack(self, target: GameEntity):
        """Execute attack on target"""
        print(f"Attacking {target.id}")
        self._fire_event('action_executed', {
            'action': 'attack',
            'unit': self.selected_unit,
            'target': target
        })
        self._clear_selection()
    
    def _execute_ability(self, tile: InteractiveTile):
        """Execute ability on tile"""
        print(f"Using ability on {tile.grid_pos}")
        self._fire_event('action_executed', {
            'action': 'ability',
            'unit': self.selected_unit,
            'target_tile': tile
        })
        self._clear_selection()
    
    def _fire_event(self, event_name: str, data: Any):
        """Fire an event to registered callbacks"""
        for callback in self.event_callbacks.get(event_name, []):
            try:
                callback(data)
            except Exception as e:
                print(f"Error in event callback for {event_name}: {e}")
    
    # Public API methods
    
    def register_event_callback(self, event_name: str, callback: Callable):
        """Register a callback for an event"""
        if event_name not in self.event_callbacks:
            self.event_callbacks[event_name] = []
        self.event_callbacks[event_name].append(callback)
    
    def add_unit(self, unit: GameEntity, position: Vector2Int):
        """Add a unit to the interaction system"""
        self._set_unit_position(unit, position)
    
    def remove_unit(self, unit: GameEntity):
        """Remove a unit from the interaction system"""
        old_pos = self.unit_positions.get(unit)
        if old_pos and old_pos in self.tiles:
            self.tiles[old_pos].clear_occupant()
        
        if unit in self.unit_positions:
            del self.unit_positions[unit]
        
        if self.selected_unit == unit:
            self._clear_selection()
    
    def update(self, delta_time: float):
        """Update the interaction manager"""
        # Update modal manager
        self.modal_manager.update()
        
        # Handle ESC key to cancel current mode
        if held_keys.get('escape'):
            if self.current_mode != InteractionMode.NORMAL:
                self._clear_selection()
            else:
                self.modal_manager.close_all_modals()
    
    def set_input_enabled(self, enabled: bool):
        """Enable or disable input processing"""
        self.input_enabled = enabled
    
    def cleanup(self):
        """Clean up resources"""
        for tile in self.tiles.values():
            tile.destroy()
        
        self.tiles.clear()
        self.modal_manager.close_all_modals()
        self.unit_positions.clear()