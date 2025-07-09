class BattleGrid:
    def __init__(self, width=8, height=8):
        self.width, self.height = width, height
        self.tiles = {}
        self.units = {}
        self.active_unit = None
        
    def is_valid(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height and (x, y) not in self.units
        
    def add_unit(self, unit):
        self.units[(unit.x, unit.y)] = unit
        
    def move_unit(self, unit, x, y):
        if unit.can_move_to(x, y, self):
            distance = abs(x - unit.x) + abs(y - unit.y)
            del self.units[(unit.x, unit.y)]
            unit.x, unit.y = x, y
            unit.current_move_points -= distance
            self.units[(x, y)] = unit
            return True
        return False
    
    def get_unit_at(self, x, y):
        """Get the unit at the specified position."""
        return self.units.get((x, y))
    
    def remove_unit(self, unit):
        """Remove a unit from the grid."""
        if (unit.x, unit.y) in self.units:
            del self.units[(unit.x, unit.y)]