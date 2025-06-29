from ursina import *

class GridTile(Entity):
    def __init__(self, x, y, game_controller=None):
        super().__init__(
            parent=scene,
            model='cube',
            color=color.light_gray,
            scale=(0.9, 0.1, 0.9),
            position=(x, 0, y),
            collider='box'  # Add collider for click detection
        )
        self.grid_x, self.grid_y = x, y
        self.original_color = color.light_gray
        self.game_controller = game_controller
        
    def on_click(self):
        print(f"Tile clicked at: ({self.grid_x}, {self.grid_y})")
        if self.game_controller:
            self.game_controller.handle_tile_click(self.grid_x, self.grid_y)
            
    def highlight(self, highlight_color=color.yellow):
        self.color = highlight_color
        
    def unhighlight(self):
        self.color = self.original_color