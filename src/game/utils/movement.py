"""
Movement
movement_handle_mouse_movement
"""

from core.math.vector import Vector2Int, Vector3
from typing import Dict, Any, List, Optional, Tuple

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
