"""
Movement
movement_handle_mouse_movement
"""

from core.math.vector import Vector2Int, Vector3
from typing import Dict, Any, List, Optional, Tuple

def show_movement_confirmation(self):
    """Show modal to confirm unit movement."""
    if not self.path_cursor or not self.active_unit:
        return

    # Create confirmation buttons
    confirm_btn = Button(
        text=self._get_button_config('movement_confirmation', 'confirm').get('text', 'Confirm Move'),
        color=self._get_button_color('movement_confirmation', 'confirm', color.green)
    )
    cancel_btn = Button(
        text=self._get_button_config('movement_confirmation', 'cancel').get('text', 'Cancel'),
        color=self._get_button_color('movement_confirmation', 'cancel', color.red)
    )

    # Set up button callbacks
    def confirm_move():
        self.execute_movement()
        if self.movement_modal:
            self.movement_modal.enabled = False
            destroy(self.movement_modal)
            self.movement_modal = None

    def cancel_move():
        if self.movement_modal:
            self.movement_modal.enabled = False
            destroy(self.movement_modal)
            self.movement_modal = None

    confirm_btn.on_click = confirm_move
    cancel_btn.on_click = cancel_move

    # Create modal window
    self.movement_modal = WindowPanel(
        title='Confirm Movement',
        content=(
            Text(f'Move {self.active_unit.name} to position ({self.path_cursor[0]}, {self.path_cursor[1]})?'),
            Text(f'This will use {self.calculate_path_cost()} movement points.'),
            confirm_btn,
            cancel_btn
        ),
        popup=True
    )

    # Center the window panel
    self.movement_modal.y = self.movement_modal.panel.scale_y / 2 * self.movement_modal.scale_y
    self.movement_modal.layout()

def calculate_path_cost(self) -> int:
    """Calculate the movement cost of the current path."""
    if not self.path_cursor or not self.active_unit:
        return 0

    # For mouse-generated paths, calculate actual path cost
    if self.current_path and self.pathfinder:
        try:
            # Convert current path to Vector2Int format
            start_pos = Vector2Int(self.active_unit.x, self.active_unit.y)
            path_positions = [start_pos] + [Vector2Int(pos[0], pos[1]) for pos in self.current_path]

            # Calculate actual path cost using grid movement costs
            total_cost = 0.0
            for i in range(len(path_positions) - 1):
                cost = self.pathfinder.grid.get_movement_cost(path_positions[i], path_positions[i + 1])
                if cost == float('inf'):
                    return 999  # Invalid path
                total_cost += cost

            return int(total_cost)
        except Exception as e:
            print(f"⚠ Error calculating path cost: {e}")
            # Fallback to Manhattan distance
            pass

    # Fallback: Manhattan distance for WASD paths or when pathfinder unavailable
    return abs(self.path_cursor[0] - self.active_unit.x) + abs(self.path_cursor[1] - self.active_unit.y)

def execute_movement(self):
    """Execute the planned movement."""
    if not self.path_cursor or not self.active_unit:
        return

    # Store old position for TacticalGrid update
    old_pos = Vector2Int(self.active_unit.x, self.active_unit.y)
    new_pos = Vector2Int(self.path_cursor[0], self.path_cursor[1])

    # Calculate movement distance and AP cost
    distance = abs(new_pos.x - old_pos.x) + abs(new_pos.y - old_pos.y)
    
    # Import action costs and calculate AP required
    from ..config.action_costs import ACTION_COSTS
    ap_cost = ACTION_COSTS.get_movement_cost(distance)
    
    # Check if unit has enough AP for movement
    if hasattr(self.active_unit, 'ap') and ap_cost > 0:
        if self.active_unit.ap < ap_cost:
            print(f"❌ Not enough AP for movement! Need {ap_cost}, have {self.active_unit.ap}")
            return
    
    # Move unit to cursor position
    if self.grid.move_unit(self.active_unit, self.path_cursor[0], self.path_cursor[1]):
        # Consume AP for successful movement
        if hasattr(self.active_unit, 'ap') and ap_cost > 0:
            self.active_unit.ap -= ap_cost
            print(f"   🏃 Movement consumed {ap_cost} AP (remaining: {self.active_unit.ap})")
            # Update AP bar immediately
            if hasattr(self, 'refresh_action_points_bar'):
                self.refresh_action_points_bar()
        
        # Update TacticalGrid positions
        if self.tactical_grid:
            self.tactical_grid.free_cell(old_pos)
            # Use unit name and new position as unique identifier
            unit_id = f"{self.active_unit.name}_{new_pos.x}_{new_pos.y}"
            self.tactical_grid.occupy_cell(new_pos, unit_id)

        self.update_unit_positions()
        # Keep unit selected after movement but clear path and mode
        moved_unit = self.active_unit  # Store reference before clearing path
        self.current_path = []
        self.path_cursor = None
        self.current_mode = None  # Exit movement mode
        self.clear_highlights()

        # Keep the unit selected and update its highlights
        if moved_unit:
            self.highlight_active_unit()
            # Don't show movement range - user needs to click Move again for that

            # Update control panel with moved unit info (keep it selected)
            if self.control_panel_callback:
                try:
                    control_panel = self.control_panel_callback()
                    if control_panel:
                        control_panel.update_unit_info(moved_unit)
                except Exception as e:
                    print(f"⚠ Error updating control panel: {e}")

        print(f"Unit moved successfully. Press END TURN when ready.")

def is_valid_move_destination(self, x: int, y: int) -> bool:
    """Check if a position is within the unit's movement range."""
    if not self.active_unit:
        return False

    # Calculate total distance from unit's starting position
    total_distance = abs(x - self.active_unit.x) + abs(y - self.active_unit.y)

    # Check if within movement points and valid grid position
    if total_distance > self.active_unit.current_move_points:
        return False

    if not (0 <= x < self.grid.width and 0 <= y < self.grid.height):
        return False

    # Check if position is occupied using TacticalGrid if available
    if self.tactical_grid:
        cell = self.tactical_grid.get_cell(Vector2Int(x, y))
        if cell and cell.occupied:
            return False
    else:
        # Fallback to legacy BattleGrid
        if (x, y) in self.grid.units:
            return False

    return True

def movement_handle_path_movement(self, direction: str):
    """Handle path movement and confirmation."""
    if not self.active_unit or not self.path_cursor:
        return
            
    if direction == 'enter':
        # Show confirmation modal for movement
        self.show_movement_confirmation()
        return
            
    # Calculate new cursor position based on direction
    x, y = self.path_cursor
    if direction == 'w':  # Forward/Up
        new_pos = (x, y - 1)
    elif direction == 's':  # Backward/Down
        new_pos = (x, y + 1)
    elif direction == 'a':  # Right (swapped)
        new_pos = (x + 1, y)
    elif direction == 'd':  # Left (swapped)
        new_pos = (x - 1, y)
    else:
        return
            
    # Check if new position is valid (within movement range)
    if self.is_valid_move_destination(new_pos[0], new_pos[1]):
        # Calculate the distance from unit's starting position to the new position
        total_distance = abs(new_pos[0] - self.active_unit.x) + abs(new_pos[1] - self.active_unit.y)
            
        # Don't allow path to exceed movement points
        if total_distance > self.active_unit.current_move_points:
            return
            
        # Update path cursor
        self.path_cursor = new_pos
            
        # Calculate complete path from unit position to cursor using pathfinder (like mouse movement)
        if self.pathfinder:
            try:
                start_pos = Vector2Int(self.active_unit.x, self.active_unit.y)
                end_pos = Vector2Int(new_pos[0], new_pos[1])
                    
                calculated_path = self.pathfinder.calculate_movement_path(
                    start_pos, 
                    end_pos, 
                    float(self.active_unit.current_move_points)
                )
                    
                if calculated_path and len(calculated_path) > 1:
                    # Convert Vector2Int path back to tuple format (excluding start position)
                    self.current_path = [(pos.x, pos.y) for pos in calculated_path[1:]]
                else:
                    # Fallback: direct path if pathfinder fails
                    self.current_path = [new_pos]
                        
            except Exception as e:
                print(f"⚠ Pathfinding failed for keyboard movement: {e}")
                # Fallback: simple direct path
                self.current_path = [new_pos]
        else:
            # Fallback: simple direct path if no pathfinder
            self.current_path = [new_pos]
            
        # Update highlights
        self.update_path_highlights()
    
def movement_handle_mouse_movement(self, clicked_tile: Tuple[int, int]) -> bool:
    """
    Handle mouse click for movement path creation.
        
    Args:
        clicked_tile: (x, y) coordinates of clicked tile
            
    Returns:
        True if click was handled, False otherwise
    """
    if not self.active_unit or self.current_mode != "move":
        return False
        
    if not self.pathfinder:
        print("⚠ Pathfinder not available - falling back to manual path building")
        return False
        
    # Convert coordinates to Vector2Int for pathfinder
    start_pos = Vector2Int(self.active_unit.x, self.active_unit.y)
    end_pos = Vector2Int(clicked_tile[0], clicked_tile[1])
        
    # Check if clicking on same tile as unit (no movement needed)
    if start_pos.x == end_pos.x and start_pos.y == end_pos.y:
        return True
        
    # Validate that clicked tile is within unit's movement range
    distance = abs(end_pos.x - start_pos.x) + abs(end_pos.y - start_pos.y)
    if distance > self.active_unit.current_move_points:
        print(f"Target tile ({end_pos.x}, {end_pos.y}) is too far. Distance: {distance}, Movement points: {self.active_unit.current_move_points}")
        return True  # Handle the click but don't move
        
    # Check if target tile is occupied (blocked by another unit)
    if self.tactical_grid:
        target_cell = self.tactical_grid.get_cell(end_pos)
        if target_cell and target_cell.occupied:
            print(f"Target tile ({end_pos.x}, {end_pos.y}) is occupied by another unit")
            return True  # Handle the click but don't move
        
    # Calculate path using pathfinder
    try:
        calculated_path = self.pathfinder.calculate_movement_path(
            start_pos, 
            end_pos, 
            float(self.active_unit.current_move_points)
        )
            
        if calculated_path and len(calculated_path) > 1:
            # Convert Vector2Int path back to tuple format (excluding start position)
            self.current_path = [(pos.x, pos.y) for pos in calculated_path[1:]]
            self.path_cursor = (end_pos.x, end_pos.y)
                
            # Update visual highlights
            self.update_path_highlights()
                
            print(f"Path calculated: {len(self.current_path)} steps to ({end_pos.x}, {end_pos.y})")
            return True
        else:
            # No valid path found - try to get as close as possible
            reachable_positions = self.pathfinder.find_reachable_positions(
                start_pos, 
                float(self.active_unit.current_move_points)
            )
                
            if reachable_positions:
                # Find closest reachable position to clicked tile
                closest_pos = min(reachable_positions, 
                                key=lambda pos: abs(pos.x - end_pos.x) + abs(pos.y - end_pos.y))
                    
                # Calculate path to closest position
                closest_path = self.pathfinder.calculate_movement_path(
                    start_pos,
                    closest_pos,
                    float(self.active_unit.current_move_points)
                )
                    
                if closest_path and len(closest_path) > 1:
                    self.current_path = [(pos.x, pos.y) for pos in closest_path[1:]]
                    self.path_cursor = (closest_pos.x, closest_pos.y)
                    self.update_path_highlights()
                        
                    print(f"Target unreachable. Path to closest position: ({closest_pos.x}, {closest_pos.y})")
                    return True
                
            print(f"No valid path to ({end_pos.x}, {end_pos.y}) within movement range")
            return True
                
    except Exception as e:
        print(f"⚠ Error calculating path: {e}")
        return False
