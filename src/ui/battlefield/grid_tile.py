from ursina import *
import time

class GridTile(Entity):
    def __init__(self, x, y, game_controller=None):
        # Use master UI configuration
        from src.core.ui.ui_config_manager import get_ui_config_manager
        ui_config = get_ui_config_manager()
        
        # Get tile configuration from master config
        tile_config = ui_config.get('battlefield.grid_tiles', {})
        tile_model = tile_config.get('model', 'cube')
        tile_color = ui_config.get_color('battlefield.grid_tiles.color', '#D3D3D3')
        tile_scale = ui_config.get_scale('battlefield.grid_tiles.scale')
        position_offset = ui_config.get_position('battlefield.grid_tiles.position_offset')
        collider_type = tile_config.get('collider', 'box')
        
        # Convert scale dict to tuple if needed
        if isinstance(tile_scale, dict):
            scale_tuple = (tile_scale['x'], tile_scale['y'], tile_scale['z'])
        else:
            scale_tuple = (0.9, 0.1, 0.9)  # fallback
        
        super().__init__(
            parent=scene,
            model=tile_model,
            color=tile_color,
            scale=scale_tuple,
            position=(x + position_offset['x'], position_offset['y'], y + position_offset['z']),
            collider=collider_type
        )
        self.grid_x, self.grid_y = x, y
        self.original_color = tile_color
        self.game_controller = game_controller
        
        # Double-click detection using master config
        self.last_click_time = 0
        self.double_click_threshold = ui_config.get('battlefield.grid_tiles.double_click_threshold', 0.3)
        self.click_count = 0
        
    def on_click(self):
        current_time = time.time()
        
        # Improved double-click detection
        if (current_time - self.last_click_time) < self.double_click_threshold:
            self.click_count += 1
        else:
            self.click_count = 1
        
        is_double_click = (self.click_count >= 2)
        self.last_click_time = current_time
        
        # Reset click count after processing double-click
        if is_double_click:
            self.click_count = 0
        
        if is_double_click:
            print(f"🖱️  Double-click detected at: ({self.grid_x}, {self.grid_y})")
        else:
            print(f"Tile clicked at: ({self.grid_x}, {self.grid_y})")
            # Debug coordinate mapping
            if self.game_controller and hasattr(self.game_controller, 'units'):
                for unit in self.game_controller.units:
                    if unit.x == self.grid_x and unit.y == self.grid_y:
                        print(f"  → Unit found at this position: {unit.name}")
                        break
        
        if self.game_controller:
            # Don't handle tile clicks if there's an active modal dialog
            if (hasattr(self.game_controller, 'action_modal') and 
                self.game_controller.action_modal and 
                hasattr(self.game_controller.action_modal, 'enabled') and
                self.game_controller.action_modal.enabled):
                print("🚫 Ignoring tile click - action modal is open")
                return
                
            # Handle double-click in movement mode
            if (is_double_click and 
                hasattr(self.game_controller, 'current_mode') and 
                self.game_controller.current_mode == "move" and
                hasattr(self.game_controller, 'active_unit') and 
                self.game_controller.active_unit):
                
                print(f"🖱️  Double-click movement: Confirming movement to ({self.grid_x}, {self.grid_y})")
                # First set the path, then show confirmation
                if self.game_controller.handle_mouse_movement((self.grid_x, self.grid_y)):
                    # If path was set successfully, show movement confirmation
                    if hasattr(self.game_controller, 'show_movement_confirmation'):
                        self.game_controller.show_movement_confirmation()
                return
            
            # Handle double-click in attack mode
            if (is_double_click and 
                hasattr(self.game_controller, 'current_mode') and 
                self.game_controller.current_mode == "attack" and
                hasattr(self.game_controller, 'active_unit') and 
                self.game_controller.active_unit):
                
                print(f"🖱️  Double-click attack: Confirming attack on ({self.grid_x}, {self.grid_y})")
                # Handle attack target selection and show confirmation
                if hasattr(self.game_controller, 'handle_attack_target_selection'):
                    self.game_controller.handle_attack_target_selection(self.grid_x, self.grid_y, from_double_click=True)
                return
                
            # Handle double-click in magic mode
            if (is_double_click and 
                hasattr(self.game_controller, 'current_mode') and 
                self.game_controller.current_mode == "magic" and
                hasattr(self.game_controller, 'active_unit') and 
                self.game_controller.active_unit):
                
                print(f"🖱️  Double-click magic: Confirming magic on ({self.grid_x}, {self.grid_y})")
                # Handle magic target selection and show confirmation
                if hasattr(self.game_controller, 'handle_magic_target_selection'):
                    self.game_controller.handle_magic_target_selection(self.grid_x, self.grid_y, from_double_click=True)
                return
                
            # Check if we're in movement mode and should handle single-click mouse movement
            if (not is_double_click and
                hasattr(self.game_controller, 'current_mode') and 
                self.game_controller.current_mode == "move" and
                hasattr(self.game_controller, 'active_unit') and 
                self.game_controller.active_unit and
                hasattr(self.game_controller, 'handle_mouse_movement')):
                
                # Handle mouse movement for path creation
                print(f"🖱️  Mouse movement: Creating path to ({self.grid_x}, {self.grid_y})")
                if self.game_controller.handle_mouse_movement((self.grid_x, self.grid_y)):
                    return  # Mouse movement handled
            
            # Default tile click handling (unit selection, etc.) - only for single clicks
            if not is_double_click:
                self.game_controller.handle_tile_click(self.grid_x, self.grid_y)
            
    def highlight(self, highlight_color=color.yellow):
        self.color = highlight_color
        
    def unhighlight(self):
        self.color = self.original_color