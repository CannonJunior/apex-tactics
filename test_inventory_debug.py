#!/usr/bin/env python3
"""
Simple test to verify inventory positioning logic
"""

# Mock the necessary parts
class MockInventoryItem:
    def __init__(self, name, x, y):
        self.item_data = {'name': name}
        self.x = x
        self.y = y

class MockInventory:
    def __init__(self, width=6, height=8):
        self.width = width
        self.height = height
        self.children = []
    
    def find_free_spot(self):
        """Find the first available spot in the inventory grid."""
        # Get all occupied grid positions by checking existing InventoryItem positions
        occupied_positions = set()
        
        print(f"🔍 FIND_FREE_SPOT: Checking {len(self.children)} children")
        for child in self.children:
            if isinstance(child, MockInventoryItem):
                # Convert normalized position back to grid coordinates  
                grid_x = round(child.x * self.width)
                grid_y = round(-child.y * self.height)
                occupied_positions.add((grid_x, grid_y))
                print(f"🔍 Found occupied position: ({grid_x}, {grid_y}) from item '{child.item_data['name']}'")
        
        print(f"🔍 Total occupied positions: {occupied_positions}")
        
        # Find first free spot (row by row)
        for y in range(self.height):
            for x in range(self.width):
                if (x, y) not in occupied_positions:
                    print(f"🔍 Found free spot at: ({x}, {y})")
                    return x, y
        
        print("🔍 No free spots available!")
        return None

def test_inventory_positioning():
    print("Testing inventory positioning logic...")
    
    inventory = MockInventory()
    
    # Simulate adding items at positions (0,0) through (5,0)
    for i in range(6):
        normalized_x = i / inventory.width
        normalized_y = 0  # First row
        item = MockInventoryItem(f"Item{i}", normalized_x, normalized_y)
        inventory.children.append(item)
        print(f"Added Item{i} at normalized ({normalized_x:.3f}, {normalized_y:.3f}) -> grid ({i}, 0)")
    
    # Now try to find the next free spot
    print("\nLooking for next free spot...")
    free_spot = inventory.find_free_spot()
    
    if free_spot:
        print(f"Next free spot should be: {free_spot} (expecting (0, 1))")
    else:
        print("ERROR: No free spot found!")

if __name__ == "__main__":
    test_inventory_positioning()