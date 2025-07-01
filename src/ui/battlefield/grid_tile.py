from ursina import *

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
        
    def on_click(self):
        print(f"Tile clicked at: ({self.grid_x}, {self.grid_y})")
        if self.game_controller:
            # Check if we're in movement mode and should handle mouse movement
            if (hasattr(self.game_controller, 'current_mode') and 
                self.game_controller.current_mode == "move" and
                hasattr(self.game_controller, 'selected_unit') and 
                self.game_controller.selected_unit and
                hasattr(self.game_controller, 'handle_mouse_movement')):
                
                # Handle mouse movement for path creation
                print(f"🖱️  Mouse movement: Creating path to ({self.grid_x}, {self.grid_y})")
                if self.game_controller.handle_mouse_movement((self.grid_x, self.grid_y)):
                    return  # Mouse movement handled
            
            # Default tile click handling (unit selection, etc.)
            self.game_controller.handle_tile_click(self.grid_x, self.grid_y)
            
    def highlight(self, highlight_color=color.yellow):
        self.color = highlight_color
        
    def unhighlight(self):
        self.color = self.original_color