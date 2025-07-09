from ursina import *
import time

class GridTile(Entity):
    def __init__(self, x, y, game_controller=None):
        super().__init__(
            parent=scene,
            model='cube',
            color=color.light_gray,
            scale=(0.9, 0.1, 0.9),
            position=(x + 0.5, 0, y + 0.5),  # Center tiles to match unit positioning
            collider='box'  # Add collider for click detection
        )
        self.grid_x, self.grid_y = x, y
        self.original_color = color.light_gray
        self.game_controller = game_controller
        
        # Double-click detection
        self.last_click_time = 0
        self.double_click_threshold = 0.3  # 300ms for double-click
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