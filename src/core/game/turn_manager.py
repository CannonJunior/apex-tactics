class TurnManager:
    def __init__(self, units):
        self.units = sorted(units, key=lambda u: u.speed, reverse=True)
        self.current_turn = 0
        self.phase = "move"  # move, action, end
        
    def next_turn(self):
        self.current_turn = (self.current_turn + 1) % len(self.units)
        if self.current_turn == 0:
            for unit in self.units:
                unit.ap = unit.max_ap
                unit.current_move_points = unit.move_points  # Reset movement points
                
    def current_unit(self):
        return self.units[self.current_turn] if self.units else None